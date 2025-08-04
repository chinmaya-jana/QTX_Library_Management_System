# This File contains Pydantic data Validation

"""
from enum import Enum

from mypy.fixup import missing_info
from pydantic import field_validator, BaseModel, EmailStr
from typing import Optional

class Validators(BaseModel):
    #ISBN Validation: - Validate ISBN-10 and ISBN-13 formats - Remove hyphens and spaces - Verify check digits
    @field_validator("isbn", check_fields=False)
    def validate_isbn(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = v.strip().replace("-", "").replace(" ", "")
        if not cleaned.isdigit() or len(cleaned) not in (10, 13):
            raise ValueError("ISBN must be 10 or 13 digits")
        if not (cleaned.startswith("978") or cleaned.startswith("979")):
            raise ValueError("ISBN must start with 978 or 979")
        return v


    #Email Validation: - Use Pydantic's EmailStr type - Handle malformed email addresses gracefully
    @field_validator("email", "contact_email", check_fields=False)
    def email_validate(cls, v: EmailStr) -> EmailStr:
        if not v.strip():
            raise missing_info('Email must be non empty')
        if not EmailStr._validate(v):
            raise ValueError('Email format is invalid, read carefully email format')
        return v

    #Name Normalization: - Standardize name capitalization (Title Case) -
    # Handle multiple name variations for the same person - Trim whitespace
    @field_validator('first_name', 'last_name', check_fields=False)
    def human_name_validation(cls, v: str) -> str:
        if not v:
            raise ValueError('Name must be non empty')
        if not v.strip().replace(' ', '').isalpha():
            raise ValueError('Name must be alphabet')
        return v[0].upper() + v[1:].lower()

    # here handle 'Category': 'name', 'Library': 'name' and 'Book': 'title' name
    @field_validator('name', 'title', check_fields=False)
    def name_validation(cls, v: str) -> str:
        name = v.split()
        if not name:
            raise ValueError('Name/title must not be empty')
        if not v.strip().replace(' ', '').isalpha():
            raise ValueError('Name/title only contains alphabet')

        for index, word in enumerate(name):
            name[index] = word[0].upper() + word[1:].lower()
        result = ' '.join(name)
        return result

    #Phone Number Normalization: - Extract digits only - Format to standard pattern
    #(e.g., +1-XXX-XXX-XXXX) - Handle international formats
    @field_validator('phone', 'phone_number', check_fields=False)
    def phone_number_validate(cls, v: Optional[str])-> Optional[str]:
        if not v:
            return None

        cleaned = v.strip().replace('-','')
        if not cleaned.startswith('+1'):
            raise ValueError("International Number always starts with '+1'")
        if not cleaned[2:].isdigit():
            raise ValueError("Phone number must be digit")
        if not len(cleaned[2:]) == 10:
            raise ValueError("Phone number must be 10 digit")
        return cleaned[2:]

    @field_validator("title", check_fields=False)
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must be non-empty")
        return v

    @field_validator("total_copies", check_fields=False)
    def validate_total_copies(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Total copies must be positive")
        return v

    @field_validator("available_copies", check_fields=False)
    def validate_available_copies(cls, v: int, info) -> int:
        total = info.data.get("total_copies")
        if v < 0:
            raise ValueError("Available copies cannot be negative")
        if total is not None and v > total:
            raise ValueError("Available copies cannot exceed total copies")
        return v

class MemberType(str, Enum):
    STUDENT = "Student"
    FACULTY = "Faculty"
"""

from pydantic import BaseModel, EmailStr, ValidationError, field_validator, model_validator
from datetime import date
from typing import Optional, ClassVar, Dict, Tuple, Any
from models import *
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
        return v.strip().title()

    @field_validator('phone_number')
    def phone_validator(cls, v):
        if not v:
            return None
        cleaned = v.strip().replace('-', '')
        if not cleaned.startswith('+1'):
            raise ValueError("International Number always starts with '+1'")
        if not cleaned[2:].isdigit():
            raise ValueError("Phone number must be digit")
        if not len(cleaned[2:]) == 10:
            raise ValueError("Phone number must be 10 digit")
        return cleaned


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
        if not v.strip().replace(" ", "").isalpha():
            raise ValueError("must contain only letters")
        return v.strip().title()


class CategorySchema(BaseValidator):
    primary_key: ClassVar[str] = "category_id"

    category_id: Optional[int]
    name: str
    description: Optional[str]

    @field_validator("name")
    def name_must_alphabetic(cls, v):
        if not v.strip().replace(" ", "").isalpha():
            raise ValueError("must contain only letters")
        return v.strip().title()


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
        if not v.strip().replace(" ", "").isalpha():
            raise ValueError("must contain only letters")
        return v.strip().title()

    @field_validator("phone")
    def phone_format(cls, v):
        if v is None:
            return v
        clean = v.strip().replace("-", "").replace(" ", "")
        if not clean.startswith("+1"):
            raise ValueError("phone must start with +1")
        if not clean[2:].isdigit() or len(clean[2:]) != 10:
            raise ValueError("phone must have 10 digits after country code")
        return clean


class BorrowingSchema(BaseValidator):
    primary_key: ClassVar[str] = "borrowing_id"
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

class ReviewSchema(BaseValidator):
    primary_key: ClassVar[str] = "review_id"
    foreign_keys: ClassVar[Dict[str, Tuple[Any, str]]] = {
        "member_id": (Member, "member_id"),
        "book_id": (Book, "book_id"),
    }

    review_id: Optional[int]
    member_id: int
    book_id: int
    rating: float
    comment: Optional[str]
    review_date: Optional[date]

    @field_validator("rating")
    def rating_range(cls, v):
        if not (1 <= v <= 5):
            raise ValueError("rating must be between 1 and 5")
        return v

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

        pk_field = getattr(schema_class, "primary_key", "unknown_id")
        pk_value = row.get(pk_field, "N/A")

        for error in e.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get('msg', 'Validation error')
            logger.warning(f"{pk_field} ({pk_value}) - {field}: {message}")

        return None