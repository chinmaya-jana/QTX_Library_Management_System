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

import os
import csv
import logging
import argparse
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import *
from schemas import *
from schemas import validate_and_log, ValidationTracker
from sqlalchemy.orm import declarative_base

# We don't import database.py because DB URL is dynamic from CLI
Base = declarative_base()

# Mapping CSV file names to (Schema, Model) tuples
FILE_SCHEMA_MODEL_MAPPING = {
    "library.csv": (LibrarySchema, Library),
    "author.csv": (AuthorSchema, Author),
    "category.csv": (CategorySchema, Category),
    "book.csv": (BookSchema, Book),
    "member.csv": (MemberSchema, Member),
    "review.csv": (ReviewSchema, Review),
    "borrowing.csv": (BorrowingSchema, Borrowing),
}

def get_args():
    parser = argparse.ArgumentParser(
        description="Load CSV data into MySQL DB with validation"
    )
    parser.add_argument(
        "-d", "--directory",
        required=True,
        help="Path to directory containing CSV files"
    )
    parser.add_argument(
        "--database-url", "--db",
        required=True,
        help="Database connection URL, e.g. mysql+pymysql://user:pass@host/dbname"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    return parser.parse_args()

def setup_logging(log_level):
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s"
    )
    return logging.getLogger(__name__)

def load_and_insert_data(file_path, schema_class, model_class, session, logger):
    if not os.path.exists(file_path):
        logger.warning(f"❌ File not found: {file_path}")
        return

    tracker = ValidationTracker()
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize empty strings and parse dates
            for key, value in row.items():
                if value == "":
                    row[key] = None
                elif "date" in key.lower() and value:
                    try:
                        row[key] = datetime.strptime(value.strip(), "%Y-%m-%d").date()
                    except Exception:
                        # Let schema validation handle date format errors
                        pass

            obj = validate_and_log(schema_class, row, tracker)
            if obj:
                try:
                    db_obj = model_class(**obj.model_dump())
                    session.add(db_obj)
                except Exception as e:
                    logger.error(f"❌ DB insertion error for row: {e}")

    session.commit()
    tracker.report(os.path.basename(file_path))


def main():
    args = get_args()
    logger = setup_logging(args.log_level)

    logger.info(f"Connecting to DB: {args.database_url}")
    engine = create_engine(args.database_url, echo=False)

    # Create all tables from models automatically
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        for file_name, (schema_class, model_class) in FILE_SCHEMA_MODEL_MAPPING.items():
            full_path = os.path.join(args.directory, file_name)
            logger.info(f"📥 Processing file: {file_name}")
            load_and_insert_data(full_path, schema_class, model_class, session, logger)
    finally:
        session.close()
        logger.info("Processing completed, session closed.")

if __name__ == "__main__":
    main()
