import argparse
import json
from sqlalchemy.exc import IntegrityError
from api_client import OpenLibraryAPIClient
from schemas import BookSchema, AuthorSchema, ValidationTracker, validate_and_log
from models import Book, Author
from database import get_engine_and_session, Base
from logs import logger

def get_author_key(api_client: OpenLibraryAPIClient, author_name: str) -> str:
    result = api_client.search_author(author_name)
    docs = result.get("docs", [])
    if not docs:
        logger.warning(f"No author found for: {author_name}")
        return None
    return docs[0]["key"]  # e.g., "/authors/OL24636A"

def map_work_to_book_schema(work: dict, author_id: int) -> dict:
    return {
        "title": work.get("title", "Unknown Title"),
        "isbn": extract_isbn(work),
        "publication_date": extract_publication_date(work),
        "pages": extract_page_count(work),
        "author_id": author_id
    }

def extract_isbn(work: dict) -> str:
    # Work may not include ISBN, need to extract from editions in a real-world case
    identifiers = work.get("identifiers", {})
    isbn_list = identifiers.get("isbn_13") or identifiers.get("isbn_10")
    if isbn_list and isinstance(isbn_list, list):
        return isbn_list[0]
    return None


def extract_publication_date(work: dict) -> str:
    return work.get("created", {}).get("value", "1900")  # fallback

def extract_page_count(work: dict) -> int:
    return work.get("number_of_pages", 100)  # fallback if pages not available


def insert_author(session, author_data: dict, tracker: ValidationTracker):
    validated = validate_and_log(AuthorSchema, author_data, tracker)
    if validated:
        author = Author(**validated.model_dump())
        session.add(author)
        session.commit()
        return author
    return None


def insert_books(session, books_data: list, tracker: ValidationTracker):
    for book_data in books_data:
        validated = validate_and_log(BookSchema, book_data, tracker)
        if validated:
            existing = session.query(Book).filter_by(
                title=validated.title,
                author_id=validated.author_id
            ).first()
            if existing:
                logger.info(f"Skipping duplicate book: {validated.title}")
                continue

            book = Book(**validated.model_dump())
            session.add(book)
            try:
                session.commit()
                logger.info(f"Inserted book: {book.title}")
            except IntegrityError:
                session.rollback()
                logger.warning(f"Failed to insert book due to DB constraint: {book.title}")


def main():
    parser = argparse.ArgumentParser(description="Fetch books from Open Library and insert into DB")
    parser.add_argument("--author", required=True, help="Author name to search for")
    parser.add_argument("--limit", type=int, default=20, help="Max number of books to fetch")
    parser.add_argument("--db", "--database-url", dest="database_url", required=True, help="Database connection URL")
    parser.add_argument("--output", help="Optional output JSON file for raw responses")

    args = parser.parse_args()

    # Setup DB
    engine, SessionLocal = get_engine_and_session(args.database_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)  # Auto create tables
    session = SessionLocal()

    api_client = OpenLibraryAPIClient()

    # Track validation stats
    author_tracker = ValidationTracker()
    book_tracker = ValidationTracker()

    # Fetch author key
    author_key = get_author_key(api_client, args.author)
    if not author_key:
        logger.warning("Could not find author, exiting.")
        return

    # Fetch author works
    works_data = api_client.get_author_works(author_key, args.limit)
    works = works_data.get("entries", [])

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(works, f, indent=2)

    # Insert author into DB
    author_schema_data = {
        "name": args.author,
        "birth_date": None,
        "nationality": "Unknown",  # As Open Library may not return this
        "biography": None
    }

    db_author = insert_author(session, author_schema_data, author_tracker)
    if not db_author:
        logger.warning("Author data invalid. Exiting.")
        return

    books_to_insert = []

    for work in works:
        work_key = work.get("key")
        if not work_key:
            continue

        work_detail = api_client.get_work_details(work_key)
        if not work_detail:
            continue

        mapped = map_work_to_book_schema(work_detail, db_author.author_id)
        books_to_insert.append(mapped)

    # Insert validated books into DB
    insert_books(session, books_to_insert, book_tracker)

    # Final report
    author_tracker.report("Author")
    book_tracker.report("Book")


if __name__ == "__main__":
    main()
