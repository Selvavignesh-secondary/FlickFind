from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text


from schemas import MoodRequest
from ai_service import ai_engine
import database
import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🧠 Initialize the local AI engine on boot
    ai_engine.load_model()
    
    yield  # This acts as the structural pause button while the server runs
    
    # 🔌 This runs when you turn the server off
    print("🔌 [FlickFind API] Shutting down application engine...")


app = FastAPI(title="FlickFind API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your React dev loop port to connect flawlessly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to the FlickFind Backend Engine!"
    }

@app.get("/api/v1/health/db")
async def check_database_health(db: Session = Depends(database.get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "database_status": "connected",
            "message": "FastAPI successfully verified communication channel with PostgreSQL inside Docker!"
        }
    except Exception as e:
        return {
            "database_status": "disconnected",
            "error_details": str(e)
        }


@app.post("/api/v1/recommend/mood")
async def analyze_mood(request: MoodRequest, db: Session = Depends(database.get_db)):
    user_prompt = request.mood_text
    
    # 1. Convert incoming raw emotional text into a clean 384-dimensional vector coordinate
    vector_signature = ai_engine.generate_vector(user_prompt)
    
    # 2. Query our PostgreSQL database container natively using Cosine Distance metric.
    # We order by the closest mathematical distance to our search coordinate,
    # and restrict our final response matrix to the top 2 closest recommendations.
    try:
        # We use SQLAlchemy's native structure, but bypass the compilation quirk
        # by explicitly calling the Cosine Distance function built into our models.
        recommendations = (
            db.query(models.Movie)
            .order_by(models.Movie.mood_vector_data.cosine_distance(vector_signature))
            .limit(2)
            .all()
        )
        
        # 3. Restructure database model instances into a clean serialized JSON array block
        results = []
        for movie in recommendations:
            results.append({
                "id": movie.id,
                "title": movie.title,
                "release_year": movie.release_year,
                "imdb_rating": movie.imdb_rating,
                "director": movie.director,
                "runtime": movie.runtime,
                "age_rating": movie.age_rating,
                "synopsis": movie.synopsis,
                "content_warning": movie.content_warning
            })
            
        return {
            "search_query": user_prompt,
            "status": "Semantic vector scan matched successfully against PostgreSQL vector catalog",
            "results_count": len(results),
            "recommendations": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Vector similarity execution layer failure: {str(e)}"
        }