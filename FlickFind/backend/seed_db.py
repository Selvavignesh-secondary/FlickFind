from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Movie
from ai_service import ai_engine
from sqlalchemy import text

# A targeted seed catalog matching your high-rating thriller preference parameters
MOCK_MOVIES = [
    {
        "title": "Inception",
        "release_year": 2010,
        "imdb_rating": 8.8,
        "director": "Christopher Nolan",
        "runtime": 148,
        "age_rating": "PG-13",
        "synopsis": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "content_warning": "Mild violence and intense action sequences"
    },
    {
        "title": "Shutter Island",
        "release_year": 2010,
        "imdb_rating": 8.2,
        "director": "Martin Scorsese",
        "runtime": 138,
        "age_rating": "R",
        "synopsis": "A U.S. Marshal uncovers a chilling and reality-shattering conspiracy while investigating the sudden disappearance of a murderer from a remote asylum.",
        "content_warning": "Disturbing psychological themes and intense thriller sequences"
    },
    {
        "title": "Interstellar",
        "release_year": 2014,
        "imdb_rating": 8.7,
        "director": "Christopher Nolan",
        "runtime": 169,
        "age_rating": "PG-13",
        "synopsis": "A team of explorers travel through a wormhole in space in an epic, emotional attempt to ensure humanity's survival on a dying Earth.",
        "content_warning": "Intense cosmic peril and emotional distress strings"
    },
    {
        "title": "Gone Girl",
        "release_year": 2014,
        "imdb_rating": 8.1,
        "director": "David Fincher",
        "runtime": 149,
        "age_rating": "R",
        "synopsis": "With his wife's sudden disappearance having become the focus of an intense media circus, a man sees the spotlight turned on him as suspicions grow.",
        "content_warning": "Graphic descriptions of crime, domestic toxicity, and violence"
    }
]

def seed_database():
    db: Session = SessionLocal()
    
    print("🔋 [Seeder] Registering pgvector C-extensions inside the PostgreSQL container...")
    # This enables mathematical vector sorting inside Postgres natively
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    db.commit()
    
    print("🗄️  [Seeder] Synchronizing vector schemas with data tables...")
    Base.metadata.create_all(bind=engine)
    
    # Simple count check to prevent data row clutter if re-run
    existing_count = db.query(Movie).count()
    if existing_count > 0:
        print(f"⚠️  [Seeder] Database already contains {existing_count} records. Aborting pipeline loop.")
        db.close()
        return

    # Load our transformer model into local RAM execution contexts
    ai_engine.load_model()
    
    print("\n🚀 [Seeder] Beginning cinematic vectorization pipeline loop...")
    for item in MOCK_MOVIES:
        print(f"🎬 Processing synopsis metadata for: '{item['title']}'...")
        
        # We consolidate fields into a rich data block for the AI model to analyze
        context_string = f"{item['title']} directed by {item['director']}. Synopsis: {item['synopsis']}"
        
        # Calculate the 384 positional parameters on your processing nodes
        computed_vector = ai_engine.generate_vector(context_string)
        
        db_movie = Movie(
            title=item["title"],
            release_year=item["release_year"],
            imdb_rating=item["imdb_rating"],
            director=item["director"],
            runtime=item["runtime"],
            age_rating=item["age_rating"],
            synopsis=item["synopsis"],
            content_warning=item["content_warning"],
            mood_vector_data=computed_vector # Bind the floating point array directly to the vector column
        )
        db.add(db_movie)
    
    db.commit()
    db.close()
    print("\n✨ [Seeder] Data warehouse successfully populated with vector-mapped film structures!")

if __name__ == "__main__":
    seed_database()