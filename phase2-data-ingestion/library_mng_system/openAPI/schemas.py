# This File contains Pydantic data Validation
import re
from pydantic import BaseModel, ValidationError, field_validator
from datetime import date, datetime
from typing import Optional, ClassVar, Union
from models import Book, Author
from logs import logger

class BaseValidator(BaseModel):
    model_config = {
        "from_attributes": True
    }

# ========== SCHEMAS ==========
class AuthorSchema(BaseValidator):
    name: str
    birth_date: Union[date, str, None]
    nationality: Optional[str] = None
    biography: Optional[str] = None

    @field_validator("name")
    def name_must_alphabetic(cls, v):
        return name_validator(v)

    @field_validator("birth_date", mode="before")
    def birth_date_validator(cls, v):
        return date_validation(v)

class BookSchema(BaseValidator):
    title: str
    isbn: Optional[str]
    publication_date: Union[date, str]
    pages: int
    author_id: int

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
        if not clean.isdigit():
            raise ValueError("ISBN must contain only digits (with optional hyphens/spaces)")
        if len(clean) == 10:
            if not validate_isbn10(clean):
                raise ValueError("Invalid ISBN-10 format")
        elif len(clean) == 13:
            if not validate_isbn13(clean):
                raise ValueError("Invalid ISBN-13 format")
        else:
            raise ValueError("ISBN must be either 10 or 13 digits long")
        return clean

    @field_validator("pages")
    def pages_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("pages must be a positive number")
        return v

    @field_validator("publication_date", mode="before")
    def parse_publication_date(cls, v):
        return date_validation(v)

# ========= Common Validation Functions ==========
def validate_isbn10(isbn: str) -> bool:
    if len(isbn) != 10:
        return False
    total = 0
    for i, char in enumerate(isbn):
        if char == 'X' and i == 9:
            total += 10
        elif char.isdigit():
            total += int(char) * (10 - i)
        else:
            return False
    return total % 11 == 0

def validate_isbn13(isbn: str) -> bool:
    if len(isbn) != 13:
        return False
    total = 0
    for i, char in enumerate(isbn):
        if not char.isdigit():
            return False
        digit = int(char)
        if i % 2 == 0:
            total += digit
        else:
            total += 3 * digit
    return total % 10 == 0

def name_validator(name: Optional[str]) -> Optional[str]:
    if not re.fullmatch(r"[A-Za-z\s\-']+", name.strip()):
        raise ValueError("must contain only letters, spaces, hyphens or apostrophes")
    return name.strip()

def try_parse_date(v: str, fmt: str) -> Optional[date]:
    try:
        return datetime.strptime(v, fmt).date()
    except ValueError:
        return None

def date_validation(v: Optional[Union[str, date]]) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        v = v.strip()
        # Handle full ISO format with time
        try:
            return datetime.fromisoformat(v).date()
        except ValueError:
            pass
        # Try common formats
        common_formats = [
            "%Y-%m-%d",
            "%d %B %Y",     #ex: 7 February 1812
            "%B %d, %Y",     #ex: February 7, 1812
            "%Y/%m/%d",
            "%Y"            #ex: year only
        ]
        for fmt in common_formats:
            parsed = try_parse_date(v, fmt)
            if parsed:
                return parsed
    raise ValueError(f"Unrecognized date format: {v}")

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

        pk_fields = getattr(schema_class, "primary_key", ("unknown_id",))
        if not isinstance(pk_fields, (list, tuple)):
            pk_fields = (pk_fields,)

        pk_value = ", ".join(str(row.get(pk, "N/A")) for pk in pk_fields)

        for error in e.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get('msg', 'Validation error')
            logger.warning(f"{pk_fields} ({pk_value}) - {field}: {message}")

        return None
