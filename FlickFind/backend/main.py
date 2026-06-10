import os
from dotenv import load_dotenv

# 🔋 Load environment configuration first
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

# 📦 FIXED: Import BOTH required schema validation contracts simultaneously
from schemas import MoodRequest, ChattedRecommendationResponse
from ai_service import ai_engine
import database
import models

# 🚀 Initialize the official Google GenAI SDK client
from google import genai
from google.genai import types

genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# 🧠 Lifespan Event Handler Configuration
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the local embedding model on boot memory
    ai_engine.load_model()
    yield  
    print("🔌 [FlickFind API] Shutting down application engine...")


# 🚀 FIXED: Single, unified application instantiation
app = FastAPI(title="FlickFind API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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


@app.post("/api/v1/recommend/mood", response_model=ChattedRecommendationResponse)
async def analyze_mood_chat(request: MoodRequest, db: Session = Depends(database.get_db)):
    user_message = request.mood_text
    
    # 📡 THE SYSTEM CONTEXT PROMPT
    system_instruction = """
    You are 'FlickFind AI', an elite, highly conversational cinema concierge.
    Your job is to analyze the user's movie request and determine if they have provided enough specific thematic, emotional, or stylistic context for us to perform an accurate vector search.
    
    CRITICAL CRITERIA FOR CONTEXT SUFFICIENCY:
    - Vague requests (e.g., 'show me a thriller', 'i want a comedy', 'good movies') are INSUFFICIENT (is_context_sufficient = false). You must engage in chat and ask sharp, creative follow-up questions to drill down into their specific taste profile.
    - Detailed or specific requests (e.g., 'i need a high octane thriller with great visual effects', 'grounded slow-burn psychological mystery') are SUFFICIENT (is_context_sufficient = true). 
    
    HYBRID SUMMARY DIRECTIONS (Only apply if context is sufficient):
    You will be given the titles of 5 mathematically matched movies. For EACH movie card, write a 'hybrid_summary'. 
    This summary must seamlessly merge a brief plot hook of the film AND a creative explanation of why it perfectly fulfills their stated mood preference. Keep it tightly capped under 4 sentences.
    """
    
    try:
        # 🕵️‍♂️ STAGE 1: FIRST LLM PASS TO CHECK CONTEXT SUFFICIENCY
        routing_prompt = f"Analyze this user chat message for movie recommendation depth: '{user_message}'"
        
        class RouterGate(BaseModel):
            is_context_sufficient: bool
            followup_chat_response: str

        gate_response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=routing_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=RouterGate,
            ),
        )
        
        router_decision = RouterGate.model_validate_json(gate_response.text)
        
        # 🚧 GATE BRANCH A: Context is too vague. Return early as a chatbot!
        if not router_decision.is_context_sufficient:
            return ChattedRecommendationResponse(
                is_context_sufficient=False,
                ai_followup_chat=router_decision.followup_chat_response,
                recommendations=[] 
            )
            
        # 🚀 GATE BRANCH B: Context is golden! Execute vector retrieval and data generation
        # Step 2a: Convert user message to high-dimensional coordinate vector space
        vector_signature = ai_engine.generate_vector(user_message)
        
        # Step 2b: Scan our ultra-lightweight PostgreSQL database layout for 5 matches
        db_matches = (
            db.query(models.Movie)
            .order_by(models.Movie.mood_vector_data.cosine_distance(vector_signature))
            .limit(5)
            .all()
        )
        
        # Increment hit counters on the fly for our LFU eviction cache strategy
        for movie in db_matches:
            movie.hit_count += 1
        db.commit()
        
        # Bundle database identities to hand to the synthesis engine
        local_movie_context = "\n".join([f"ID: {m.id} | Title: {m.title} | Year: {m.release_year}" for m in db_matches])
        
        # 🧠 STAGE 2: SECOND PASS FOR INDIVIDUAL CARD HYDRATION & REASONING
        generation_prompt = f"""
        The user wants: "{user_message}"
        
        Our local vector database has successfully isolated these 5 movie matches:
        {local_movie_context}
        
        Using your deep cinematic knowledge, hydrate the remaining missing card values (director, poster image URL placeholder, and the 4-sentence hybrid_summary).
        """
        
        final_package_response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=generation_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChattedRecommendationResponse,
            ),
        )
        
        final_validated_output = ChattedRecommendationResponse.model_validate_json(final_package_response.text)
        return final_validated_output

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent System Breakdown: {str(e)}")