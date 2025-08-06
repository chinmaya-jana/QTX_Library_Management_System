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
