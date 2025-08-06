# This File contains Pydantic data Validation
import re
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, EmailStr, ValidationError, field_validator, model_validator, confloat
from datetime import date
from typing import Optional, ClassVar
from models import Member, Book, Author, Library, MemberType
from logs import logger

class BaseValidator(BaseModel):
    model_config = {
        "from_attributes": True
    }

# ========== SCHEMAS ==========
class LibrarySchema(BaseValidator):
    primary_key: ClassVar[str] = "library_id"

    library_id: Optional[int]
    name: str
    campus_location: str
    contact_email: EmailStr
    phone_number: Optional[str]

    @field_validator("name", "campus_location")
    def non_empty_checker(cls, v):
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("phone_number")
    def validate_phone(cls, v):
        return validate_phone_global(v)


class AuthorSchema(BaseValidator):
    primary_key: ClassVar[str] = "author_id"

    author_id: Optional[int]
    first_name: str
    last_name: str
    birth_date: Optional[date]
    nationality: Optional[str]
    biography: Optional[str]

    @field_validator("first_name", "last_name")
    def name_must_alphabetic(cls, v):
        return name_validator(v)

class BookSchema(BaseValidator):
    primary_key: ClassVar[str] = "book_id"

    book_id: Optional[int]
    title: str
    isbn: Optional[str]
    publication_date: date
    total_copies: int
    available_copies: int
    library_id: int

    @field_validator("title")
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("isbn")
    def isbn_check(cls, v):
        if v is None:
            return v
        clean = v.replace("-", "").replace(" ", "")
        if not clean.isdigit() or len(clean) not in (10, 13):
            raise ValueError("ISBN must be 10 or 13 digits")
        if not (clean.startswith("978") or clean.startswith("979")):
            raise ValueError("ISBN must start with 978 or 979")
        return clean

    @field_validator("total_copies")
    def total_copies_always_positive(cls, v):
        if v <= 0:
            raise ValueError("total_copies must be positive")
        return v

    @model_validator(mode="after")
    def validate_copies_consistency(self) -> "BookSchema":
        if self.available_copies < 0:
            raise ValueError("available_copies cannot be negative")
        if self.available_copies > self.total_copies:
            raise ValueError("available_copies cannot exceed total_copies")
        return self


class MemberSchema(BaseValidator):
    primary_key: ClassVar[str] = "member_id"

    member_id: Optional[int]
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    member_type: MemberType
    registration_date: date

    @field_validator("first_name", "last_name")
    def clean_name(cls, v):
        return name_validator(v)

    @field_validator("phone")
    def validate_phone(cls, v):
        return validate_phone_global(v)

# Some common validation across models
def validate_phone_global(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    try:
        # Try parsing with no region to force international format (+)
        number = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(number):
            raise ValueError("Invalid phone number")
        # Return number in E.164 format: +12345678900
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)

    except NumberParseException as e:
        raise ValueError(f"Invalid phone number format: {e}")

def name_validator(name: Optional[str]) -> Optional[str]:
    if not re.fullmatch(r"[A-Za-z\s\-']+", name.strip()):
        raise ValueError("must contain only letters, spaces, hyphens or apostrophes")
    return name.strip()

# ========== VALIDATION TRACKING ==========
class ValidationTracker:
    def __init__(self):
        self.total = 0
        self.valid = 0
        self.invalid = 0

    def log_valid(self):
        self.valid += 1
        self.total += 1

    def log_invalid(self):
        self.invalid += 1
        self.total += 1

    def reset(self):
        self.total = self.valid = self.invalid = 0

    def report(self, schema_name):
        success_rate = (self.valid / self.total * 100) if self.total else 0
        logger.info(f"\n[Validation Summary: {schema_name}]")
        logger.info(f"====>Valid rows:   {self.valid}")
        logger.info(f"====>Invalid rows: {self.invalid}")
        logger.info(f"====>Total rows:   {self.total}\n")
        logger.info(f"====> Success rate: {success_rate:.1f}%\n")

def validate_and_log(schema_class, row: dict, tracker: ValidationTracker) -> Optional[BaseValidator]:
    try:
        obj = schema_class(**row)
        tracker.log_valid()
        return obj
    except ValidationError as e:
        tracker.log_invalid()

        # UPDATED to handle tuple or str primary_key (composite keys support)
        pk_fields = getattr(schema_class, "primary_key", ("unknown_id",))
        if not isinstance(pk_fields, (list, tuple)):
            pk_fields = (pk_fields,)

        pk_value = ", ".join(str(row.get(pk, "N/A")) for pk in pk_fields)

        for error in e.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get('msg', 'Validation error')
            logger.warning(f"{pk_fields} ({pk_value}) - {field}: {message}")

        return None
