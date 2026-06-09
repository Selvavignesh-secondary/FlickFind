from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Hardcoded explicit IPv4 connection mapping
DATABASE_URL = "postgresql://flickadmin:flicksecretpassword@127.0.0.1:5433/flickfind_db"

# We add pool_pre_ping=True to force the engine to test the live connection 
# before executing a query, automatically recovering if the socket is briefly stale.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()