from pydantic import BaseModel, field_validator, ValidationError
from typing import Optional
from datetime import date
import re

class Book(BaseModel):
    book_id: int
    title: str
    publication_date: date
    total_copies: int
    available_copies: int
    library_id: int
    isbn: Optional[str] = None  # Some books might not have ISBN

    # Book_id must be positive

    # title is not null
    @field_validator('title')
    def title_must_not_empty(cls, v: str) -> str:
        if not v.strip() or not v:
            raise ValueError('title must be non empty')
        return v

    # total_copies > 0
    @field_validator('total_copies')
    def total_copies_always_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Total copies always positive if record is available')
        return v

    # available_copies must be less than or equal to total_copies
    @field_validator('available_copies')
    def available_copies_check(cls, v: int, info) -> int:
        total_copies = info.data.get('total_copies')
        if total_copies is not None and v > total_copies:
            raise ValueError('Available copies can not be geather than total copies')
        if v < 0:
            raise ValueError("Available copies cannot be negative")
        return v

    # ISBN validation
    @field_validator('isbn')
    def isbn_validation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # remove '-' and space
        cleaned_isbn = v.replace('-','').replace(' ', '')
        if not re.fullmatch(r'\d{13}', cleaned_isbn):
            raise ValueError('ISBN must be 13 digit')

        # ISBN startswith '978' and '979'
        if not cleaned_isbn.startswith('978') or cleaned_isbn.startswith('979'):
            raise ValueError('ISBN starts with either 978 or 979')

        return v