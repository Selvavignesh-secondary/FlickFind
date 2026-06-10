from sqlalchemy import Column, Integer, String, Float
from pgvector.sqlalchemy import Vector
from database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True) # Will hold the TMDB global ID
    title = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)
    imdb_rating = Column(Float, nullable=False)
    
    # 📊 LFU Cache Tracking: Starts at 0, increments when matched
    hit_count = Column(Integer, default=0, nullable=False)
    
    # 🧬 384-Dimensional High-Density Vector Coordinates
    mood_vector_data = Column(Vector(768), nullable=True)