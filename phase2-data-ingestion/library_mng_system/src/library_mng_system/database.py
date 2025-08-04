#DATABASE_URL = "mysql+pymysql://root:Chintu%4024@localhost:3306/library_db" #lib_mng_system

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def get_engine_and_session(database_url: str):
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal
