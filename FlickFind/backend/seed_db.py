import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Movie
from ai_service import ai_engine
from sqlalchemy import text

# A targeted seed catalog matching your high-rating thriller preference parameters
MOCK_MOVIES = [
    {
        "id": 27205, # Real TMDB identifier baseline
        "title": "Inception",
        "release_year": 2010,
        "imdb_rating": 8.8,
        "imdb_votes": 2500000,
        "popularity": 120.5,
        "director": "Christopher Nolan",
        "runtime": 148,
        "genres": "Action, Sci-Fi, Adventure",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."
    },
    {
        "id": 11324,
        "title": "Shutter Island",
        "release_year": 2010,
        "imdb_rating": 8.2,
        "imdb_votes": 1400000,
        "popularity": 95.4,
        "director": "Martin Scorsese",
        "runtime": 138,
        "genres": "Drama, Thriller, Mystery",
        "overview": "A U.S. Marshal uncovers a chilling and reality-shattering conspiracy while investigating the sudden disappearance of a murderer from a remote asylum."
    },
    {
        "id": 157336,
        "title": "Interstellar",
        "release_year": 2014,
        "imdb_rating": 8.7,
        "imdb_votes": 2000000,
        "popularity": 150.2,
        "director": "Christopher Nolan",
        "runtime": 169,
        "genres": "Adventure, Drama, Sci-Fi",
        "overview": "A team of explorers travel through a wormhole in space in an epic, emotional attempt to ensure humanity's survival on a dying Earth."
    },
    {
        "id": 210577,
        "title": "Gone Girl",
        "release_year": 2014,
        "imdb_rating": 8.1,
        "imdb_votes": 1000000,
        "popularity": 80.1,
        "director": "David Fincher",
        "runtime": 149,
        "genres": "Drama, Mystery, Thriller",
        "overview": "With his wife's sudden disappearance having become the focus of an intense media circus, a man sees the spotlight turned on him as suspicions grow."
    }
]

def seed_database():
    db: Session = SessionLocal()
    
    print("🔋 [Seeder] Registering pgvector C-extensions inside the PostgreSQL container...")
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    db.commit()
    
    print("🗄️  [Seeder] Synchronizing vector schemas with data tables...")
    Base.metadata.create_all(bind=engine)
    
    # Simple count check to prevent data row clutter if re-run
    existing_count = db.query(Movie).count()
    if existing_count > 0:
        print(f"⚠️  [Seeder] Database already contains {existing_count} records. Clearing to apply fresh parameters...")
        db.execute(text("TRUNCATE TABLE movies RESTART IDENTITY CASCADE;"))
        db.commit()

    # Load our transformer model into local RAM execution contexts
    ai_engine.load_model()
    
    print("\n🚀 [Seeder] Beginning cinematic vectorization pipeline loop...")
    for item in MOCK_MOVIES:
        print(f"🎬 Processing synopsis metadata for: '{item['title']}'...")
        
        # Consolidate text block into a rich semantic context for our 768-dim embedder
        context_string = f"{item['title']} directed by {item['director']}. Genres: {item['genres']}. Overview: {item['overview']}"
        
        computed_vector = ai_engine.generate_vector(context_string)
        
        db_movie = Movie(
            id=item["id"],
            title=item["title"],
            release_year=item["release_year"],
            imdb_rating=item["imdb_rating"],
            imdb_votes=item["imdb_votes"],
            popularity=item["popularity"],
            director=item["director"],
            runtime=item["runtime"],
            genres=item["genres"],
            overview=item["overview"],
            mood_vector_data=computed_vector
        )
        db.add(db_movie)
    
    db.commit()
    db.close()
    print("\n✨ [Seeder] Data warehouse successfully populated with vector-mapped film structures!")

if __name__ == "__main__":
    seed_database()