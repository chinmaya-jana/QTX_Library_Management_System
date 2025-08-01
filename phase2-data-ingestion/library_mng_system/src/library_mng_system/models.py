"""
# Things that I did first

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
"""

from sqlalchemy import (Column, Integer, String, Date, Float, ForeignKey, Enum, Table,)
from sqlalchemy.orm import relationship
from database import Base
import enum

class MemberType(enum.Enum):
    STUDENT = 'Student'
    FACULTY = 'Faculty'

book_author = Table(
    'book_author',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('book.book_id'), primary_key=True),
    Column('author_id', Integer, ForeignKey('author.author_id'), primary_key=True)
)

book_category = Table(
    'book_category',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('book.book_id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('category.category_id'), primary_key=True)
)

#Models
class Library(Base):
    __tablename__ = 'libraries'
    library_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    campus_location = Column(String(250), nullable=False)
    contact_email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=True)
    books = relationship("Book", back_populates="library")

class Book(Base):
    __tablename__= 'book'
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(13), nullable=True)
    publication_date = Column(Date, nullable=False)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)
    library_id = Column(Integer, ForeignKey('libraries.library_id'), nullable=False)
    library = relationship("Library", back_populates="books")
    author = relationship(
        "Author",
        secondary=book_author,
        back_populates="books"
    )
    category = relationship(
        "Category",
        secondary=book_category,
        back_populates="books"
    )
    review = relationship("Review", back_populates="book")
    borrowing = relationship("Borrowing", back_populates="book")


class Author(Base):
    __tablename__ = 'author'
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(50), nullable=False)
    biography = Column(String(1000), nullable=True)
    books = relationship(
        "Book",
        secondary=book_author,
        back_populates="author"
    )

class Category(Base):
    __tablename__ = "category"
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)
    books = relationship(
        "Book",
        secondary=book_category,
        back_populates="category"
    )

class Member(Base):
    __tablename__ = "member"
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    member_type = Column(Enum(MemberType), nullable=False)
    registration_date = Column(Date, nullable=False)
    borrowing = relationship("Borrowing", back_populates="member")
    review = relationship("Review", back_populates="member")

class Borrowing(Base):
    __tablename__ = "borrowing"
    borrowing_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("member.member_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    late_fee = Column(Float, nullable=True)
    member = relationship("Member", back_populates="borrowing")
    book = relationship("Book", back_populates="borrowing")

class Review(Base):
    __tablename__ = "review"
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("member.member_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(String(1000), nullable=True)
    review_date = Column(Date, nullable=True)
    member = relationship("Member", back_populates="review")
    book = relationship("Book", back_populates="review")
