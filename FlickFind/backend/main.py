import os
from dotenv import load_dotenv

# 🔋 This scans your directory, finds your .env file, and securely loads the GEMINI_API_KEY
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text


from schemas import MoodRequest
from ai_service import ai_engine
import database
import models

from google import genai
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

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
    
    # 1. Convert incoming emotional text into a vector coordinate
    vector_signature = ai_engine.generate_vector(user_prompt)
    
    try:
        # 2. Query our PostgreSQL database container via native Cosine Distance
        recommendations = (
            db.query(models.Movie)
            .order_by(models.Movie.mood_vector_data.cosine_distance(vector_signature))
            .limit(2)
            .all()
        )
        
        # Structure database rows into a clean JSON array list
        results = []
        movie_context_strings = []
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
            # Combine individual titles and summaries into text blocks for Gemini
            movie_context_strings.append(f"Title: {movie.title} | Synopsis: {movie.synopsis}")
            
        # 🧠 3. Generative AI Reasoning Pipeline Stage
        formatted_movie_context = "\n\n".join(movie_context_strings)
        
        reasoning_prompt = f"""
        You are an elite cinematic analyst for 'FlickFind.ai'.
        The user wants a movie that matches this mood: "{user_prompt}"
        
        We found these matching films in our database:
        {formatted_movie_context}
        
        Write a concise summary breakdown (max 3 sentences total). 
        Acknowledge their mood and explain creatively why these movies match what they want.
        Do not reveal major plot spoilers.
        """
        
        # Call the reasoning model via our global genai_client instance
        reasoning_response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=reasoning_prompt
        )
        
        ai_reasoning_text = reasoning_response.text

        # 🚀 Now we include the 'ai_reasoning' field in our return package!
        return {
            "search_query": user_prompt,
            "status": "Success",
            "results_count": len(results),
            "ai_reasoning": ai_reasoning_text, 
            "recommendations": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Hybrid pipeline layer failure: {str(e)}"
        }