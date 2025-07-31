from book import Book
import logging
import csv
from datetime import datetime
from pydantic import ValidationError

# Configure logging
logging.basicConfig(
    filename='../invalid_data/invalid_books.log',
    filemode='a',
    level=logging.WARNING,
    format='\n%(asctime)s - BookID %(book_id)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():

    with open('../data/books.csv', newline='', encoding='utf-8') as books:
        reader = csv.DictReader(books)
        for row in reader:
            try:
                #convert and prepare fields
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
                logging.warning(f"Invalid data: {row} | Error: {error}", extra={'book_id': book_id})

            # Unhandled error
            except Exception as e:
                book_id = row.get('book_id', 'Unknown')
                logging.warning(f"Invalid data: {row} | Error: {e}", extra={'book_id': book_id})

if __name__ == "__main__":
    main()
