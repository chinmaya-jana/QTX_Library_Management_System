import argparse
from datetime import date
from sqlalchemy.exc import IntegrityError
from api_client import OpenLibraryClient
from database import get_engine_and_session, Base
from models import Author, Book
from schemas import AuthorSchema, BookSchema, validate_and_log, ValidationTracker
from logs import logger

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and store books from Open Library API")
    parser.add_argument("--author", required=True, help="Author name to search for")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of books to fetch")
    parser.add_argument("--db", required=True, help="Database connection URL")
    parser.add_argument("--output", help="Optional output file to store fetched book data as JSON")
    return parser.parse_args()

def main():
    args = parse_args()
    db_url = args.db
    author_name = args.author
    limit = args.limit

    try:
        engine, SessionLocal = get_engine_and_session(db_url)
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
    except Exception as e:
        logger.error(f"Failed to connect to DB: {e}")
        return

    client = OpenLibraryClient()
    author_search = client.search_author(author_name)
    if not author_search:
        logger.error(f"No author found with name: {author_name}")
        return

    author_key = author_search.get("key")
    author_details = client.get_author_details(author_key)

    author_data = {
        "name": author_search.get("name"),
        "birth_date": author_details.get("birth_date"),
        "nationality": None,  # Not provided by Open Library
        "biography": None     # Not provided by Open Library
    }

    author_tracker = ValidationTracker()
    author_schema = validate_and_log(AuthorSchema, author_data, author_tracker)
    author_tracker.report("Author")

    if not author_schema:
        logger.error("Author validation failed. Aborting.")
        return

    # author exists or not in DB
    db_author = session.query(Author).filter_by(name=author_schema.name).first()
    if not db_author:
        db_author = Author(**author_schema.model_dump())
        session.add(db_author)
        session.commit()

    works = client.get_author_works(author_key, limit)

    book_tracker = ValidationTracker()
    for work in works:
        work_key = work.get("key")
        if not work_key:
            continue
        work_key_clean = work_key.split("/")[-1]
        work_details = client.get_work_details(work_key_clean)
        if not work_details:
            logger.warning(f"Could not fetch details for work: {work_key}")
            continue

        # extract publication date
        pub_date = work_details.get("created", {}).get("value")
        pages = 0
        editions = client.get_editions_for_work(work_key_clean)
        for edition in editions.get("entries", []):
            num_pages = edition.get("number_of_pages")
            if isinstance(num_pages, int) and num_pages > 0:
                pages = num_pages
                break
        #isbn extraction
        isbn = None
        if 'isbn' in work:
            isbn_list = work['isbn']
            if isinstance(isbn_list, list) and isbn_list:
                isbn = isbn_list[0]

        book_data = {
            "title": work_details.get("title"),
            "isbn": isbn,
            "publication_date": pub_date,
            "pages": pages,
            "author_id": db_author.author_id
        }
        book_schema = validate_and_log(BookSchema, book_data, book_tracker)
        if not book_schema:
            continue
        # Check for duplicate
        existing = session.query(Book).filter_by(
            title=book_schema.title,
            author_id=db_author.author_id
        ).first()
        if existing:
            logger.warning("Data is already present in db")
            continue
        book_model = Book(**book_schema.model_dump())
        session.add(book_model)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Database commit failed: {e}")
    book_tracker.report("Books")
    session.close()

if __name__ == "__main__":
    main()
