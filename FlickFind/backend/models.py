from sqlalchemy import Column, Integer, String, Float
from database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    release_year = Column(Integer, nullable=False)
    imdb_rating = Column(Float, nullable=True) # E.g., 8.3 [cite: 102]
    director = Column(String(255), nullable=True)
    runtime = Column(Integer, nullable=False) # Total running minutes [cite: 104]
    age_rating = Column(String(50), nullable=True) # E.g., "PG-13", "R" [cite: 80, 105]
    synopsis = Column(String(500), nullable=False) # Scannable one-line summary [cite: 106]
    content_warning = Column(String(255), nullable=True) # Single line warning string [cite: 81, 110]
    
    # --- The Vector Element Column ---
    # We define our dimension length as 384 to perfectly align 
    # with the sentence transformer vector dimensions[cite: 29].
    # For now, we will store it as an array string field placeholder 
    # while we initialize our custom mapping rules.
    mood_vector_data = Column(String, nullable=True)