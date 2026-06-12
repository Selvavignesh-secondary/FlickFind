from sqlalchemy import Column, Integer, String, Float, Text
from pgvector.sqlalchemy import Vector
from database import Base

class Movie(Base):
    __tablename__ = "movies"

    # Core Identifiers
    id = Column(Integer, primary_key=True, index=True) # TMDB global ID
    imdb_id = Column(String, nullable=True)

    # Textual Data
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    tagline = Column(Text, nullable=True)
    overview = Column(Text, nullable=True)
    genres = Column(String, nullable=True)
    
    # Production Metadata
    release_year = Column(Integer, nullable=False)
    release_date = Column(String, nullable=True)
    status = Column(String, nullable=True)
    runtime = Column(Integer, nullable=True, default=0)
    original_language = Column(String, nullable=True)
    
    # Financial Analytics
    budget = Column(Float, nullable=True, default=0.0)
    revenue = Column(Float, nullable=True, default=0.0)
    
    # Quality & Metric Aggregations
    imdb_rating = Column(Float, nullable=False, default=0.0) 
    imdb_votes = Column(Integer, nullable=True, default=0)    
    popularity = Column(Float, nullable=True, default=0.0)
    
    # Crew & Talent (COMPLETE SPECTRUM)
    director = Column(String, nullable=True)
    director_of_photography = Column(String, nullable=True) # 👈 NEW: Visual Mood Identifier
    music_composer = Column(String, nullable=True)          # 👈 NEW: Auditory Mood Identifier
    movie_cast = Column(Text, nullable=True)
    writers = Column(Text, nullable=True)
    producers = Column(Text, nullable=True)
    production_companies = Column(Text, nullable=True)
    production_countries = Column(String, nullable=True)
    
    # Media Assets & Miscellaneous
    poster_path = Column(String, nullable=True)
    title_tagline_overview = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=True)
    
    # Operational Application States
    hit_count = Column(Integer, default=0, nullable=False)
    
    # 🧬 768-Dimensional High-Density Vector Coordinates
    mood_vector_data = Column(Vector(768), nullable=True)