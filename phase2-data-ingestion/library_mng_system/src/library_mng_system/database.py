#DATABASE_URL = "mysql+pymysql://root:Chintu%4024@localhost:3306/library_db" #lib_mng_system
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def get_engine_and_session(database_url: str):
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# You can override this via environment variable for flexibility
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Chintu%4024@localhost:3306/library_db")

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables. Call this explicitly on startup or migration."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Return a new SQLAlchemy session. Caller must close() it."""
    return SessionLocal()
