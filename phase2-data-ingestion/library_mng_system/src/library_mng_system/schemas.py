# This File contains Pydantic data Validation

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