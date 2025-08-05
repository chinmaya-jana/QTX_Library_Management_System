# This File contains Pydantic data Validation
import re
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, EmailStr, ValidationError, field_validator, model_validator, confloat
from datetime import date
from typing import Optional, ClassVar, Dict, Tuple, Any, Union
from models import Member, Book, Author, Category, Library, Borrowing, Review, MemberType, BookAuthor, BookCategory
from logs import logger

class BaseValidator(BaseModel):
    model_config = {
        "from_attributes": True
    }

# ========== SCHEMAS ==========
class LibrarySchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "library_id"

    library_id: Optional[int]
    name: str
    campus_location: str
    contact_email: EmailStr
    phone_number: Optional[str]

    @field_validator("name", "campus_location")
    def non_empty_checker(cls, v):
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip().title()

    @field_validator("phone_number")
    def validate_phone(cls, v):
        return validate_phone_global(v)


class AuthorSchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "author_id"

    author_id: Optional[int]
    first_name: str
    last_name: str
    birth_date: Optional[date]
    nationality: Optional[str]
    biography: Optional[str]

    @field_validator("first_name", "last_name")
    def name_must_alphabetic(cls, v):
        return name_validator(v)


class CategorySchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "category_id"

    category_id: Optional[int]
    name: str
    description: Optional[str]

    @field_validator("name")
    def name_must_alphabetic(cls, v):
        return name_validator(v)

class BookSchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "book_id"

    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "library_id": (Library, "library_id"),
    }

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
        return v.strip().title()

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
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "member_id"

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


class BorrowingSchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "borrowing_id"

    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "member_id": (Member, "member_id"),
        "book_id": (Book, "book_id"),
    }

    borrowing_id: Optional[int]
    member_id: int
    book_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date]
    late_fee: Optional[float]

    @field_validator("due_date")
    def due_after_borrow(cls, v, info):
        borrow_date = info.data.get("borrow_date")
        if borrow_date and v < borrow_date:
            raise ValueError("due_date must be after borrow_date")
        return v

    @field_validator("return_date")
    def return_after_borrow(cls, v, info):
        borrow_date = info.data.get("borrow_date")
        if v and borrow_date and v < borrow_date:
            raise ValueError("return_date cannot be before borrow_date")
        return v

    @field_validator("late_fee")
    def fee_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("late_fee cannot be negative")
        return v

    @field_validator("borrow_date")
    def borrow_date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Borrow date must be in past")
        return v

class ReviewSchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = "review_id"

    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "member_id": (Member, "member_id"),
        "book_id": (Book, "book_id"),
    }

    review_id: Optional[int]
    member_id: int
    book_id: int
    rating: confloat(ge=1, le=5)   #float
    comment: Optional[str]
    review_date: Optional[date]

class BookAuthorSchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = ("book_id", "author_id")

    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "book_id": (Book, "book_id"),
        "author_id": (Author, "author_id"),
    }

    book_id: int
    author_id: int

class BookCategorySchema(BaseValidator):
    primary_key: ClassVar[Union[str, Tuple[str, ...]]] = ("book_id", "category_id")

    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "book_id": (Book, "book_id"),
        "category_id": (Category, "category_id"),
    }

    book_id: int
    category_id: int

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
    return name.strip().title()

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


def check_foreign_keys(schema_obj) -> bool:
    """
    Check all foreign keys defined on schema_obj exist in DB.
    Logs warning if any foreign key is missing or not found.
    Returns True if all foreign keys exist, else False.
    """
    fk_map = getattr(schema_obj.__class__, "foreign_keys", {})
    for fk_field, (model_cls, model_pk) in fk_map.items():
        fk_value = getattr(schema_obj, fk_field, None)
        # FK field missing in the schema object (e.g., None or absent)
        if fk_value is None:
            logger.warning(
                f"{schema_obj.__class__.__name__} ({getattr(schema_obj, schema_obj.primary_key if isinstance(schema_obj.primary_key, str) else schema_obj.primary_key[0], 'N/A')})"
                f": Missing foreign key field '{fk_field}'"
            )
            return False
        # FK value present but not found in DB via model_cls.get_by_pk()
        if not model_cls.get_by_pk(fk_value):
            logger.warning(
                f"{schema_obj.__class__.__name__} ({getattr(schema_obj, schema_obj.primary_key if isinstance(schema_obj.primary_key, str) else schema_obj.primary_key[0], 'N/A')})"
                f": Foreign key '{fk_field}' value '{fk_value}' not found in {model_cls.__name__}"
            )
            return False
    return True

def process_row(schema_class, row: dict, tracker: ValidationTracker, session=None):
    """
    Validates data using Pydantic schema, checks FK constraints, then
    creates and inserts the corresponding SQLAlchemy model instance using the session.
    """
    if session is None:
        raise ValueError("SQLAlchemy session is required")

    # Step 1: Validate with Pydantic
    schema_obj = validate_and_log(schema_class, row, tracker)
    if schema_obj is None:
        return None  # Validation failed

    # Step 2: Check foreign key existence (optional)
    if hasattr(schema_class, "foreign_keys") and schema_class.foreign_keys:
        if not check_foreign_keys(schema_obj):
            tracker.log_invalid()
            return None

    # Step 3: Convert to ORM model (use matching model class from schema)
    try:
        # Infer model class from schema name
        model_class = {
            "LibrarySchema": Library,
            "AuthorSchema": Author,
            "CategorySchema": Category,
            "BookSchema": Book,
            "MemberSchema": Member,
            "BorrowingSchema": Borrowing,
            "ReviewSchema": Review,
            "BookAuthorSchema": BookAuthor,
            "BookCategorySchema": BookCategory,
        }.get(schema_class.__name__)

        if not model_class:
            raise ValueError(f"No ORM model found for {schema_class.__name__}")

        orm_obj = model_class(**schema_obj.model_dump(exclude_none=True))
        session.add(orm_obj)
        tracker.log_valid()
        return orm_obj

    except Exception as e:
        tracker.log_invalid()
        pk = schema_obj.primary_key if isinstance(schema_obj.primary_key, str) else schema_obj.primary_key[0]
        logger.warning(f"{schema_class.__name__} ({getattr(schema_obj, pk, 'N/A')}): DB insert error: {e}")
        return None

