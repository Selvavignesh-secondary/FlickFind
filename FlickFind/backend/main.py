from fastapi import FastAPI
# Import our new secure validation schema
from schemas import MoodRequest

app = FastAPI(title="FlickFind API", version="1.0.0")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to the FlickFind Backend Engine!"
    }

# Define a secure POST endpoint for analyzing incoming moods
@app.post("/api/v1/recommend/mood")
async def analyze_mood(request: MoodRequest):
    # At this point, Pydantic has ALREADY validated that request.mood_text exists and is safe!
    user_prompt = request.mood_text
    
    # For now, we simulate a response placeholder until our AI model is wired up
    return {
        "received": True,
        "processed_text": user_prompt,
        "mode_detected": "PENDING_AI_INTEGRATION",
        "message": "Successfully intercepted secure data payload!"
    }