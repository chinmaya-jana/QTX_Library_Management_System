
CLI for run the program:
python src/library_mng_system/data_processor.py --directory ./csv_data --db mysql+pymysql://root:Chintu%4024@localhost:3306/library_db --log-level INFO



CLI for openAPI:
python openAPI/api_fetcher.py --author "Charles Dickens" --limit 20 --db "mysql+pymysql://root:Chintu%4024@localhost:3306/library_db"
