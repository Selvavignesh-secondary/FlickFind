from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text

from schemas import MoodRequest
from ai_service import ai_engine
import database
import models # Import our new structural tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🧠 Initialize the local AI engine on boot
    ai_engine.load_model()
    
    yield  # This acts as the structural pause button while the server runs
    
    # 🔌 This runs when you turn the server off
    print("🔌 [FlickFind API] Shutting down application engine...")


app = FastAPI(title="FlickFind API", version="1.0.0", lifespan=lifespan)

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
async def analyze_mood(request: MoodRequest):
    user_prompt = request.mood_text
    vector_signature = ai_engine.generate_vector(user_prompt)
    
    return {
        "received": True,
        "processed_text": user_prompt,
        "vector_dimensions": len(vector_signature),
        "sample_vector_values": vector_signature[:5],
        "status": "Vector generated successfully. Ready for PostgreSQL similarity matching."
    }