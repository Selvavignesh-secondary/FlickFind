import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flickadmin:flicksecretpassword@127.0.0.1:5433/flickfind_db"
)

# pool_pre_ping=True verifies connectivity before running queries, auto-recovering dropped connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that yields a database session and closes it cleanly when finished."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()