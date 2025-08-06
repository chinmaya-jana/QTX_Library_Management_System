from sqlalchemy import (Column, Integer, String, Date, ForeignKey, Enum)
from sqlalchemy.orm import relationship
from database import Base
import enum

class MemberType(enum.Enum):
    STUDENT = 'Student'
    FACULTY = 'Faculty'

#Models
class Library(Base):
    __tablename__ = 'libraries'

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

class Book(Base):
    __tablename__= 'book'

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

class Author(Base):
    __tablename__ = 'author'

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(50), nullable=False)
    biography = Column(String(1000), nullable=True)

class Member(Base):
    __tablename__ = "member"

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    member_type = Column(Enum(MemberType), nullable=False)
    registration_date = Column(Date, nullable=False)
