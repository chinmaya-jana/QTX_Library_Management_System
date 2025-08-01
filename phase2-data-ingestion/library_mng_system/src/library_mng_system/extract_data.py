
#NOTE: whenever you run this program change the database name as "lib_mng_system"

from database import SessionLocal
from models import Book

def get_all_books():
    session = SessionLocal()
    try:
        books = session.query(Book).all()
        for book in books:
            print(f"BookID: {book.book_id}, Title: {book.title}")

    finally:
        session.close()

def get_all_even_books():
    session = SessionLocal()
    try:
        books = session.query(Book).filter(Book.book_id % 2 == 0).all()
        for book in books:
            print(f"BookID: {book.book_id}, Title: {book.title}")
    finally:
        session.close()

if __name__ == "__main__":
    get_all_books()
    print("******************************")
    get_all_even_books()