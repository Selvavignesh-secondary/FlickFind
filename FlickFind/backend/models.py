from sqlalchemy import Column, Integer, String, Float
from database import Base
# We import the native vector data type extension from the pgvector package
from pgvector.sqlalchemy import Vector

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    release_year = Column(Integer, nullable=False)
    imdb_rating = Column(Float, nullable=True)
    director = Column(String(255), nullable=True)
    runtime = Column(Integer, nullable=False)
    age_rating = Column(String(50), nullable=True)
    synopsis = Column(String(500), nullable=False)
    content_warning = Column(String(255), nullable=True)
    
    # 🧠 --- True High-Dimensional Vector Column ---
    # We specify 384 dimensions to perfectly map and index the semantic outputs
    # calculated by our local all-MiniLM-L6-v2 transformer model.
    mood_vector_data = Column(Vector(384), nullable=True)