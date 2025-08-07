
from sqlalchemy import (Column, Integer, String, Date, ForeignKey)
from sqlalchemy.orm import relationship
from database import Base

#Models
class Book(Base):
    __tablename__= 'book'

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(20), nullable=True)
    publication_date = Column(Date, nullable=False)
    pages = Column(Integer, nullable=False)
    author_id = Column(Integer, ForeignKey('author.author_id'), nullable=False)

    author = relationship(
        "Author",
        back_populates="books"
    )

class Author(Base):
    __tablename__ = 'author'

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(50), nullable=True)
    biography = Column(String(1000), nullable=True)

    books = relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan"
    )
