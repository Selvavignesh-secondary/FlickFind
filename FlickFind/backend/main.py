from fastapi import FastAPI
from contextlib import asynccontextmanager
from schemas import MoodRequest
from ai_service import ai_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    ai_engine.load_model()
    yield
    print("🔌 [FlickFind API] Shutting down application engine...")

app = FastAPI(title="FlickFind API", version="1.0.0", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to the FlickFind Backend Engine!"
    }

@app.post("/api/v1/recommend/mood")
async def analyze_mood(request: MoodRequest):
    user_prompt = request.mood_text
    
    # Generate the single, context-rich vector signature reflecting their exact mental state
    vector_signature = ai_engine.generate_vector(user_prompt)
    
    return {
        "received": True,
        "processed_text": user_prompt,
        "vector_dimensions": len(vector_signature),
        "sample_vector_values": vector_signature[:5],
        "status": "Vector generated successfully. Ready for PostgreSQL similarity matching."
    }