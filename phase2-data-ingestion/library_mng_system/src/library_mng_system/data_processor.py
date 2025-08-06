"""
from models import Book
import logging
import csv
from datetime import datetime
from pydantic import ValidationError

# Logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: BookID %(book_id)s - %(message)s'
)
def main():
    with open('../data/books.csv', newline='', encoding='utf-8') as books:
        reader = csv.DictReader(books)
        for row in reader:
            try:
                row['book_id'] = int(row['book_id'].strip())
                row['title'] = str(row['title'])
                row['publication_date'] = datetime.strptime(row['publication_date'].strip(), '%Y-%m-%d').date()
                row['total_copies'] = int(row['total_copies'].strip())
                row['available_copies'] = int(row['available_copies'].strip())
                row['library_id'] = int(row['library_id'].strip())

                isbn_val = row.get('isbn', '').strip()
                row['isbn'] = isbn_val if isbn_val else None

                book = Book(**row)

            except ValidationError as ve:
                book_id = row.get('book_id', 'Unknown')
                error = "; ".join([err['msg'] for err in ve.errors()])
                logging.warning(f"Validation failed: {error}", extra={'book_id': book_id})

            except Exception as e:
                book_id = row.get('book_id', 'Unknown')
                logging.warning(f"Unexpected error: {e}", extra={'book_id': book_id})

if __name__ == "__main__":
    main()
"""

"""
import os
import csv
from datetime import datetime
import argparse

from database import get_engine_and_session, Base
from models import *
from schemas import (
    LibrarySchema, AuthorSchema, CategorySchema, BookSchema,
    MemberSchema, ReviewSchema, BorrowingSchema,
    validate_and_log, ValidationTracker
)
from logs import logger

# === Mapping and Order ===
FILE_SCHEMA_MODEL_MAPPING = {
    "library.csv": (LibrarySchema, Library),
    "author.csv": (AuthorSchema, Author),
    "category.csv": (CategorySchema, Category),
    "book.csv": (BookSchema, Book),
    "member.csv": (MemberSchema, Member),
    "review.csv": (ReviewSchema, Review),
    "borrowing.csv": (BorrowingSchema, Borrowing),
}

PROCESS_ORDER = [
    "library.csv",
    "author.csv",
    "category.csv",
    "book.csv",
    "member.csv",
    "review.csv",
    "borrowing.csv",
]

# === CLI Argument Parser ===
def get_args():
    parser = argparse.ArgumentParser(description="Load CSV data into DB with validation")
    parser.add_argument(
        "-d", "--directory", required=True,
        help="Directory path containing the CSV files"
    )
    parser.add_argument(
        "--database-url", "--db", required=True,
        help="Database URL, e.g. mysql+pymysql://user:pass@host/dbname"
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    return parser.parse_args()


# === Logging Setup ===
def setup_logging(log_level):
    import logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    return logger

# === Data Loader & Validator ===
def load_and_insert_data(file_path, schema_class, model_class, session):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    tracker = ValidationTracker()

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if None in reader.fieldnames:
            logger.error(f"{file_path} has missing column headers. Please fix the CSV file.")
            return

        for line_no, row in enumerate(reader, start=2):  # start=2 to skip header
            try:
                for key, value in row.items():
                    if key is None:
                        continue
                    if value == "":
                        row[key] = None
                    elif "date" in key.lower() and value:
                        try:
                            row[key] = datetime.strptime(value.strip(), "%Y-%m-%d").date()
                        except Exception:
                            pass

                obj = validate_and_log(schema_class, row, tracker)
                if obj:
                    db_obj = model_class(**obj.model_dump())
                    session.add(db_obj)

            except Exception as e:
                pk_field = getattr(schema_class, "primary_key", "unknown_id")
                pk_value = row.get(pk_field, "N/A")
                logger.error(
                    f"Line {line_no} → DB error for {pk_field}={pk_value}: {e}"
                )

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to commit data from {file_path}: {e}")

    tracker.report(os.path.basename(file_path))


# === Main Runner ===
def main():
    args = get_args()
    setup_logging(args.log_level)

    logger.info(f"Connecting to database at {args.database_url}")
    engine, SessionLocal = get_engine_and_session(args.database_url)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        for filename in PROCESS_ORDER:
            schema_class, model_class = FILE_SCHEMA_MODEL_MAPPING[filename]
            filepath = os.path.join(args.directory, filename)
            logger.info(f"Processing file: {filename}")
            load_and_insert_data(filepath, schema_class, model_class, session)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")

    finally:
        session.close()
        logger.info("All processing completed. Session closed.")


if __name__ == "__main__":
    main()
"""
import models
import os
import argparse
import csv
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models import Library, Book, Author, Member
from schemas import (
    LibrarySchema,
    BookSchema,
    AuthorSchema,
    MemberSchema,
    ValidationTracker,
    validate_and_log
)
from logs import logger, set_log_level
from database import get_engine_and_session, Base

# Map CSV file names to models and schemas
FILE_MODEL_SCHEMA_MAP = {
    "libraries.csv": (Library, LibrarySchema),
    "books.csv": (Book, BookSchema),
    "authors.csv": (Author, AuthorSchema),
    "members.csv": (Member, MemberSchema),
}

def parse_args():
    parser = argparse.ArgumentParser(description="Process and insert validated CSV data into the database.")
    parser.add_argument("--directory", required=True, help="Directory containing CSV files.")
    parser.add_argument("--db", required=True, help="SQLAlchemy-compatible database URL.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (e.g., INFO, DEBUG, WARNING).")
    return parser.parse_args()

def load_csv(filepath):
    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield {k.strip(): v.strip() for k, v in row.items()}
"""
def insert_validated_data(session: Session, model, validated_objects):
    for obj in validated_objects:
        db_obj = model(**obj.model_dump())
        session.add(db_obj)
"""


def insert_validated_data(session: Session, model, validated_objects):
    for obj in validated_objects:
        # Check if object with this PK already exists, skip to avoid duplicates
        pk_name = list(model.__table__.primary_key.columns)[0].name
        pk_value = getattr(obj, pk_name, None)

        if pk_value is not None:
            exists = session.query(model).filter(getattr(model, pk_name) == pk_value).first()
            if exists:
                logger.warning(f"Skipping duplicate {model.__tablename__} with {pk_name}={pk_value}")
                continue

        db_obj = model(**obj.model_dump())
        session.add(db_obj)


def process_file(filename, model, schema_class, directory, session):
    logger.info(f"Processing file: {filename}")
    filepath = os.path.join(directory, filename)

    if not os.path.isfile(filepath):
        logger.warning(f"File not found: {filepath}")
        return

    tracker = ValidationTracker()
    validated_objects = []

    for row in load_csv(filepath):
        # Extra foreign key validation for Book
        if schema_class == BookSchema:
            library_id = row.get("library_id")
            if not session.query(Library).filter_by(library_id=library_id).first():
                logger.warning(f"Book skipped - library_id {library_id} does not exist in DB.")
                tracker.log_invalid()
                continue

        validated = validate_and_log(schema_class, row, tracker)
        if validated:
            validated_objects.append(validated)

    insert_validated_data(session, model, validated_objects)
    tracker.report(schema_class.__name__)

def main():
    args = parse_args()
    set_log_level(args.log_level)

    engine, SessionLocal = get_engine_and_session(args.db)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)  # Auto-create tables

    with SessionLocal() as session:
        for filename, (model, schema_class) in FILE_MODEL_SCHEMA_MAP.items():
            try:
                process_file(filename, model, schema_class, args.directory, session)
                session.commit()
            except IntegrityError as e:
                logger.warning(f"Integrity error while processing {filename}: {e}")
                session.rollback()
            except Exception as e:
                logger.warning(f"Unexpected error while processing {filename}: {e}")
                session.rollback()

if __name__ == "__main__":
    main()
