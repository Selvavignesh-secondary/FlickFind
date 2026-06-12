# main.py
import os
import random
from dotenv import load_dotenv

# 🔋 Load environment configuration first
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional, List

from schemas import MoodRequest, ChattedRecommendationResponse, MovieCard
from ai_service import ai_engine
import database
import models

from google import genai
from google.genai import types

genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# =====================================================================
# 🎛️ THE FLICKFIND DISCOVERY CONFIGURATION BOARD
# =====================================================================
ALGORITHM_CONFIG = {
    "MIN_RATING": 6.0,              # 🎯 Hard premium floor: Filters out anything below a solid 7.0
    "MIN_VOTES": 300,               # 🚫 Obscurity guard: Wipes out zero-vote slop and unverified indie media
    "MIN_RUNTIME": 60,              # ⏳ Runtime floor: Captures standard feature lengths and tight pacing
    "CANDIDATE_POOL_LIMIT": 45,      # 📦 Size of candidate warehouse chunk passed into Gemini's single pass
    
    # 🧬 VECTOR VS. MAINSTREAM BALANCE COEFFICIENTS
    # We increase the popularity multiplier so well-known films can easily climb above niche matches.
    "POPULARITY_MULTIPLIER": 0.00035,  # 👈 Elevated to pull your engine firmly into mainstream territory
    "RATING_MULTIPLIER": 0.02
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the local 768-dim embedding model on boot memory
    ai_engine.load_model()
    yield  
    print("🔌 [FlickFind API] Shutting down application engine...")


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
    return {"status": "online", "message": "FlickFind Single-Pass Engine Active"}


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


# main.py - High-Throughput Latency Optimization Phase
@app.post("/api/v1/recommend/mood", response_model=ChattedRecommendationResponse)
async def analyze_mood_chat(request: MoodRequest, db: Session = Depends(database.get_db)):
    user_message = request.mood_text
    
    try:
        # 🏎️ STEP 1: IMMEDIATELY RUN LOCAL VECTOR INFERENCE (Sub-50ms)
        vector_signature = ai_engine.generate_vector(user_message)
        
        # 🧼 STEP 2: BUNDLE ROLLING CHAT CONTEXT WINDOW
        formatted_history = ""
        for msg in request.chat_history:
            formatted_history += f"{msg.role.upper()}: {msg.text}\n"
        formatted_history += f"USER CURRENT COMMAND: {user_message}"

        # 🛡️ STEP 3: PRE-EVALUATE PROFILE OVERRIDE FOR THE SQL LAYER
        lower_message = user_message.lower()
        explicit_override = any(word in lower_message for word in ["override", "ignore my profile", "ignore profile", "something new", "different genre"])

        min_runtime = ALGORITHM_CONFIG["MIN_RUNTIME"]
        min_rating = ALGORITHM_CONFIG["MIN_RATING"]
        min_votes = ALGORITHM_CONFIG["MIN_VOTES"]
        
        pop_w = ALGORITHM_CONFIG["POPULARITY_MULTIPLIER"] if not explicit_override else 0.0
        rat_w = ALGORITHM_CONFIG["RATING_MULTIPLIER"] if not explicit_override else 0.0
        
        # 🎯 STEP 4: EXTRACT CANDIDATE POOL (40 MOVIES)
        raw_candidates = (
            db.query(models.Movie)
            .filter(models.Movie.runtime >= min_runtime)
            .filter(models.Movie.imdb_rating >= min_rating)
            .filter(models.Movie.imdb_votes >= min_votes)
            .order_by(
                models.Movie.mood_vector_data.cosine_distance(vector_signature) - 
                (models.Movie.popularity * pop_w) - 
                (models.Movie.imdb_rating * rat_w)
            )
            .limit(ALGORITHM_CONFIG["CANDIDATE_POOL_LIMIT"])
            .all()
        )
        
        if not raw_candidates:
            return ChattedRecommendationResponse(
                is_context_sufficient=True,
                ai_followup_chat="Our movie data catalog came up empty. Try rephrasing your mood!",
                recommendations=[]
            )

        sampled_candidates = random.sample(raw_candidates, min(len(raw_candidates), 30))

        # 🛡️ STEP 5: BUNDLE PERSISTENT SIDEBAR PROFILE METRICS
        profile_context = "No profile constraints tracking active."
        if request.user_profile:
            p = request.user_profile
            profile_context = f"Favorite Genres: {p.favorite_genres} | Disliked/Exclude Genres: {p.disliked_genres} | Preferred Eras: {p.preferred_eras}"

        local_movie_context = "\n".join([
            f"ID: {m.id} | Title: {m.title} | Year: {m.release_year} | Rating: {m.imdb_rating} | Runtime: {m.runtime}m | Genres: {m.genres or 'N/A'} | Director: {m.director or 'Unknown'} | Cinematographer: {m.director_of_photography or 'Unknown'} | Composer: {m.music_composer or 'Unknown'} | PosterPath: {m.poster_path or ''}" 
            for m in sampled_candidates
        ])

        # 🧠 STEP 6: UNIFIED SPEED-FOCUSED CONCIERGE PROMPT
        system_instruction = """
        You are 'FlickFind AI', a film recommendation engine which will adapt according to the user's unique cinema taste without any bias towards any genre whatsoever.
        You are being handed the conversational history that you and the user have interacted with for you to pick the best film picks depending upon the user's emotional state and current mental state, while keeping his long term preference in mind, unless stated otherwise, a long-term user taste profile, and a candidate pool of mathematically matching movies from our local database warehouse context.

        YOUR OBJECTIVE IS TO EXECUTE A SINGLE PASS EVALUATION:

        1. Checking if the Context provided by the user is enough to provide the recommendations to him:
        --> If the user's conversation history does not seem to have enough context for providing a movie pick for him, (e.g., 'give me a movie','give me a film','give me a good or bad film'), set is_context_sufficient = false. In 'ai_followup_chat', ask appropriate questions but make sure not to drill too much to keep the user engaged. Try to go specific by tapping into his exact state of mind and mood to give the best recommendation according to his mood, and leave the 'recommendations' list completely empty.
        --> If the context has enough concrete details for you to decide upon good film recommendations or picks, set is_context_sufficient = true.

        2. DYNAMIC PROFILE OVERRIDE & SELECTION (Only applies if is_context_sufficient is true):
        --> Check if the user is explicitly trying to explore alternative genres that conflict with their long-term sidebar profile parameters (e.g., they ask for a 'romantic comedy' even though romance/comedy are in their exclude lists).
        --> If the user wants something new, explore something new, try different genres which are not in his long-term sidebar profile parameters, feel free to bypass the existing constraints imposed by the profile, and give full importance to the present conversational requests and commands completely. The user's present command and present query's priority exceeds the user's profile preferences. Select 5 matching films matching their new intent out of the candidates.
        --> If they are sticking to the usual preferences, favor candidates matching their Favorite Genres and filter out Disliked Genres. Only deviate from the usual preferences in their profile if explicitly implied or commanded in the present conversation.

        3. RESPONSE FORMULATION (CRITICAL LATENCY CONSTRAINTS):
        --> In 'ai_followup_chat', write a highly engaging, natural, punchy opening introductory response introducing your movie picks. Keep it under 3 lines max.
        --> Map all 5 chosen movies accurately to the response schema, copying structural data fields EXACTLY from the context text data. Map poster_path exactly. If a data string field shows 'Unknown' or is missing, use that string fallback exactly and absolutely do not hallucinate or invent unavailable data.
        --> For each movie card, write a compelling yet highly concise 2-to-3 sentence maximum 'hybrid_summary' explaining why it matches their mood, without revealing any major plot points or potentially spoiler content. Be direct and avoid fluffy text fillers.
        """

        generation_prompt = f"""
        [CONVERSATION STREAM MEMORY]
        {formatted_history}
        
        [LONG-TERM USER PROFILE MATRIX]
        {profile_context}
        
        [CANDIDATE CINEMATIC SELECTIONS AVAILABLE]
        {local_movie_context}
        
        Analyze the inputs above and output the final structured JSON package matching the response model.
        """

        # 🏎️ Fire the optimized, low-latency request turn
        unified_response = genai_client.models.generate_content(
            model='gemini-2.5-flash-lite',  # 👈 OPTIMIZATION 1: Switch to high-throughput Lite model
            contents=generation_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChattedRecommendationResponse,
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # 👈 OPTIMIZATION 2: Drop internal thinking delay
            ),
        )

        final_package = ChattedRecommendationResponse.model_validate_json(unified_response.text)

        if final_package.is_context_sufficient and final_package.recommendations:
            selected_ids = [m.id for m in final_package.recommendations]
            for movie in sampled_candidates:
                if movie.id in selected_ids:
                    movie.hit_count += 1
            db.commit()

        return final_package

    except Exception as e:
        import traceback
        print("🚨 CRITICAL UNIFIED ENGINE ERROR DETECTED:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversational Core Breakdown: {str(e)}")