from datetime import date
from typing import Optional
from pydantic import EmailStr
from schemas import Validators, MemberType


class Book(Validators):
    book_id: int     #Primary Key in db
    title: str
    publication_date: date
    total_copies: int
    available_copies: int
    library_id: int
    isbn: Optional[str] = None

class Library(Validators):
    library_id: int   #Primary Key in db
    name: str
    campus_location: str
    contact_email: EmailStr
    phone_number: Optional[str] = None

class Author(Validators):
    author_id: int     #Primary Key in db
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    biography: Optional[str] = None

class BookAuthor(Validators):
    book_id: int       #Primary Key in db
    author_id: int    #Primary Key in db

class Category(Validators):
    category_id: int   #Primary Key in db
    name: str
    description: Optional[str] = None

class BookCategory(Validators):
    book_id: int       #Primary Key in db
    category_id: int   #Primary Key in db

class Member(Validators):
    member_id: int     #Primary Key in db
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    member_type: Optional[MemberType] #{student/faculty}
    registration_date: date

class Borrowing(Validators):
    borrowing_id: int  #Primary Key in db
    member_id: int
    book_id: int
    borrow_date: date  #Borrow date won't be non-empty if borrowing_id is available
    due_date: date
    return_date: Optional[date] = None #Suppose someone borrowed the book and return not yet
    late_fee: Optional[float] = None

class Review(Validators):
    review_id: int     #Primary Key
    member_id: int
    book_id: int
    rating: float
    comment: Optional[str] = None
    review_date: date
