from sqlalchemy import (Column, Integer, String, Date, Float, ForeignKey, Enum, Table, UniqueConstraint)
from sqlalchemy.orm import relationship, Session
from database import Base, SessionLocal
import enum

class MemberType(enum.Enum):
    STUDENT = 'Student'
    FACULTY = 'Faculty'
"""
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
"""

class CRUDMixin:
    primary_key = []  # list or tuple of column names

    @classmethod
    def get_by_pk(cls, session: Session, *pk_values):
        if not isinstance(cls.primary_key, (list, tuple)):
            raise ValueError("primary_key must be a list or tuple of column names")

        if len(pk_values) != len(cls.primary_key):
            raise ValueError("Number of pk_values must match number of primary_key columns")

        filters = [getattr(cls, key) == value for key, value in zip(cls.primary_key, pk_values)]
        query = session.query(cls)
        for condition in filters:
            query = query.filter(condition)

        return query.first()

    def save(self, session: Session):
        try:
            session.add(self)
            session.flush()  # flush, but don't commit yet
        except Exception as e:
            session.rollback()
            raise e

#
class BookAuthor(CRUDMixin, Base):
    __tablename__ = 'book_author'
    primary_key = ['book_id', 'author_id']

    book_id = Column(Integer, ForeignKey('book.book_id'), primary_key=True, autoincrement=False)
    author_id = Column(Integer, ForeignKey('author.author_id'), primary_key=True, autoincrement=False)
    book = relationship(
        "Book",
        back_populates="book_authors"
    )
    author = relationship(
        "Author",
        back_populates="book_authors"
    )

class BookCategory(CRUDMixin, Base):
    __tablename__ = 'book_category'
    primary_key = ['book_id', 'category_id']

    book_id = Column(Integer, ForeignKey('book.book_id'), primary_key=True, autoincrement=False)
    category_id = Column(Integer, ForeignKey('category.category_id'), primary_key=True, autoincrement=False)
    book = relationship(
        "Book",
        back_populates="book_categories"
    )
    category = relationship(
        "Category",
        back_populates="book_categories"
    )

#Models
class Library(CRUDMixin, Base):
    __tablename__ = 'libraries'
    primary_key = ['library_id']

    library_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    campus_location = Column(String(250), nullable=False)
    contact_email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=True)
    #One to many
    books = relationship(
        "Book",
        back_populates="library"
    )

class Book(CRUDMixin, Base):
    __tablename__= 'book'
    primary_key = ['book_id']

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(13), nullable=True)
    publication_date = Column(Date, nullable=False)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)
    library_id = Column(Integer, ForeignKey('libraries.library_id'), nullable=False)

    library = relationship(
        "Library",
        back_populates="books"
    )
    borrowings = relationship(
        "Borrowing",
        back_populates="book"
    )
    reviews = relationship(
        "Review",
        back_populates="book"
    )
    book_authors = relationship(
        "BookAuthor",
        back_populates="book",
        cascade="all, delete-orphan"
    )
    book_categories = relationship(
        "BookCategory",
        back_populates="book",
        cascade="all, delete-orphan"
    )

class Author(CRUDMixin, Base):
    __tablename__ = 'author'
    primary_key = ['author_id']

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(50), nullable=False)
    biography = Column(String(1000), nullable=True)

    book_authors = relationship(
        "BookAuthor",
        back_populates="author",
        cascade="all, delete-orphan"
    )

class Category(CRUDMixin, Base):
    __tablename__ = "category"
    primary_key = ['category_id']

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)
    book_categories = relationship(
        "BookCategory",
        back_populates="category",
        cascade="all, delete-orphan"
    )

class Member(CRUDMixin, Base):
    __tablename__ = "member"
    primary_key = ['member_id']

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    member_type = Column(Enum(MemberType), nullable=False)
    registration_date = Column(Date, nullable=False)

    borrowings = relationship(
        "Borrowing",
        back_populates="member"
    )
    reviews = relationship(
        "Review",
        back_populates="member"
    )

class Borrowing(CRUDMixin, Base):
    __tablename__ = "borrowing"
    primary_key = ['borrowing_id']

    borrowing_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("member.member_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    late_fee = Column(Float, nullable=True)

    member = relationship(
        "Member",
        back_populates="borrowings"
    )
    book = relationship(
        "Book",
        back_populates="borrowings"
    )

class Review(CRUDMixin, Base):
    __tablename__ = "review"
    primary_key = ['review_id']
    # a member can only review a book once
    __table_args__ = (
        UniqueConstraint('member_id', 'book_id', name='uix_member_book_review'),
    )

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("member.member_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(String(1000), nullable=True)
    review_date = Column(Date, nullable=True)

    member = relationship(
        "Member",
        back_populates="reviews"
    )
    book = relationship(
        "Book",
        back_populates="reviews"
    )