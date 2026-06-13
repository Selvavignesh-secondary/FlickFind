# main.py
import os
import random
from dotenv import load_dotenv
# 🔋 Load environment configuration first
load_dotenv()
from sqlalchemy import func
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional, List

from schemas import (
    MoodRequest, 
    ChattedRecommendationResponse, 
    MovieCard, 
    WatchlistAction, 
    WatchedAction, 
    DislikeAction,
    UserCreate, 
    UserLogin, 
    UserResponse,
    CompiledContextPayload
)
from auth_utils import hash_user_password, verify_user_password
from ai_service import ai_engine
import database
import models

from google import genai
from google.genai import types

genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# =====================================================================
# 🎛️ THE FLICKFIND DISCOVERY CONFIGURATION BOARD
# =====================================================================
# =====================================================================
# 🎛️ THE FLICKFIND DISCOVERY CONFIGURATION BOARD (UPDATED FOR METRIC BALANCE)
# =====================================================================
ALGORITHM_CONFIG = {
    "MIN_RATING": 6.0,              # 🎯 Hard premium floor: Filters out anything below a solid 6.0
    "MIN_VOTES": 300,               # 🚫 Obscurity guard: Wipes out unverified indie media
    "MIN_RUNTIME": 60,              # ⏳ Runtime floor: Captures standard feature lengths
    "CANDIDATE_POOL_LIMIT": 35,     # 📦 Size of candidate warehouse chunk passed into Gemini
    
    # 🧬 BALANCED VECTOR VS. METADATA COEFFICIENTS
    # Popularity is now compressed logarithmically. This multiplier ensures well-known films
    # get a clean, controlled nudge up without destroying semantic mood mapping.
    "POPULARITY_MULTIPLIER": 0.05,  
    "RATING_MULTIPLIER": 0.02,
    
    # 🧬 TASTE WEIGHT: How heavily to bias results toward their long-term profile history.
    "LONG_TERM_PERSONA_WEIGHT": 0.3
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

# =====================================================================
# 🔐 USER AUTHENTICATION & MANAGEMENT ENDPOINTS
# =====================================================================

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(database.get_db)):
    # 🚫 Check if username or email already exists in the system
    existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username is already taken.")
        
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    # 🔒 Securely hash the plaintext password using our bcrypt setup
    secure_hash = hash_user_password(user_data.password)

    # 🧬 INITIAL PERSONA VECTOR SEEDING
    # When a new user signs up, they don't have a history yet. We seed them with a neutral 
    # baseline 768-dimensional vector (filled with zeros) so the SQL math doesn't break on nulls.
    blank_persona_vector = [0.0] * 768

    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=secure_hash,
        watcher_tier="BASIC_WATCHER",  # Default baseline classification tier
        persona_vector_data=blank_persona_vector
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/v1/auth/login")
async def login_user(credentials: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    # 🔐 Verify the password string against the encrypted database hash safely
    if not verify_user_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    return {
        "message": "Authentication successful!",
        "user_id": user.id,
        "username": user.username,
        "watcher_tier": user.watcher_tier
    }

# =====================================================================
# 📊 USER ENGAGEMENT & FEEDBACK PIPELINE
# =====================================================================

@app.post("/api/v1/user/watchlist", status_code=200)
async def toggle_watchlist_item(action: WatchlistAction, db: Session = Depends(database.get_db)):
    # Check if already in watchlist to handle toggle (add/remove)
    existing = db.query(models.UserWatchlist).filter(
        models.UserWatchlist.user_id == action.user_id,
        models.UserWatchlist.movie_id == action.movie_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed", "message": "Movie removed from watchlist successfully."}
        
    new_item = models.UserWatchlist(user_id=action.user_id, movie_id=action.movie_id)
    db.add(new_item)
    db.commit()
    return {"status": "added", "message": "Movie added to watchlist successfully."}

# main.py - Insert right below your @app.post("/api/v1/user/watchlist") endpoint

@app.get("/api/v1/user/watchlist/{user_id}", response_model=List[MovieCard])
async def get_user_watchlist(user_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieves the full, rich metadata of all films saved inside a user's database queue.
    Performs a relational JOIN between watchlists and movies to avoid front-end data starvation.
    """
    try:
        # Relational Join Query: Grab full Movie structures linked to the target User ID
        watchlist_movies = (
            db.query(models.Movie)
            .join(models.UserWatchlist, models.UserWatchlist.movie_id == models.Movie.id)
            .filter(models.UserWatchlist.user_id == user_id)
            .order_by(models.UserWatchlist.added_at.desc())
            .all()
        )
        
        # Format database output records to conform perfectly to the MovieCard Pydantic validation schema
        response_cards = []
        for m in watchlist_movies:
            response_cards.append(MovieCard(
                id=m.id,
                title=m.title,
                release_year=m.release_year,
                imdb_rating=m.imdb_rating,
                runtime=m.runtime or 0,
                director=m.director or "Unknown Director",
                director_of_photography=m.director_of_photography or "Unknown",
                music_composer=m.music_composer or "Unknown",
                poster_path=m.poster_path,
                hybrid_summary=m.overview or "" # Fallback safely to overview context fields
            ))
            
        return response_cards
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch persistent user watchlist: {str(e)}")

@app.post("/api/v1/user/watched", status_code=200)
async def log_watched_movie(action: WatchedAction, db: Session = Depends(database.get_db)):
    # 1. Save the interaction record
    history_entry = models.UserWatchedHistory(
        user_id=action.user_id,
        movie_id=action.movie_id,
        rating=action.rating,
        critic_review=action.critic_review
    )
    db.add(history_entry)
    
    # 2. DYNAMIC PERSONA VECTOR OPTIMIZATION
    # We fetch the target user and the movie they just watched
    user = db.query(models.User).filter(models.User.id == action.user_id).first()
    movie = db.query(models.Movie).filter(models.Movie.id == action.movie_id).first()
    
    if user and movie and movie.mood_vector_data is not None:
        # Convert the stored pgvector array out of database rows cleanly
        movie_vector = list(movie.mood_vector_data)
        user_vector = list(user.persona_vector_data)
        
        # Calculate a running Exponential Moving Average (EMA).
        # This allows their long-term profile to slowly adapt to their new tastes.
        learning_rate = 0.15  # 15% shift weight per movie watched
        updated_vector = [
            (1 - learning_rate) * u + learning_rate * m 
            for u, m in zip(user_vector, movie_vector)
        ]
        
        user.persona_vector_data = updated_vector
        
        # 🕵️‍♂️ AUTOMATED PERSONA TIER CLASSIFICATION
        # Count total watched movies to classify user sophistication tier dynamically
        total_watched = db.query(models.UserWatchedHistory).filter(models.UserWatchedHistory.user_id == action.user_id).count()
        
        if total_watched >= 15:
            user.watcher_tier = "CRITIC"
        elif total_watched >= 5:
            user.watcher_tier = "DEEP_DIVER"
        else:
            user.watcher_tier = "BASIC_WATCHER"

    db.commit()
    return {
        "status": "success", 
        "message": "Watched history compiled.",
        "updated_tier": user.watcher_tier if user else "BASIC_WATCHER"
    }


@app.post("/api/v1/user/dislike", status_code=200)
async def log_disliked_movie(
    action: DislikeAction, 
    db: Session = Depends(database.get_db)
):
    try:
        # 1. Log the absolute filter trace so the specific ID is hidden from SQL views immediately
        dislike_entry = models.UserDislikedFilter(
            user_id=action.user_id,
            movie_id=action.movie_id,
            rejection_reason=action.rejection_reason
        )
        db.add(dislike_entry)
        db.commit()

        # 2. 🧬 SEMANTIC PROFILE ADJUSTMENT: Shift preference weights away from the dislike vector reason
        # This applies if the user is authenticated and has provided an active reason string.
        if action.user_id and action.rejection_reason:
            current_user = db.query(models.User).filter(models.User.id == action.user_id).first()
            
            if current_user:
                print(f"🧬 [FlickFind Taste Engine] Tuning persona vector for user {current_user.username}...")
                print(f"📡 Vectorizing negative feedback reason: '{action.rejection_reason}'")
                
                # Generate a 768-dimensional local Nomic vector matching their rejection reason text
                negative_vibe_vector = ai_engine.generate_vector(action.rejection_reason)
                
                # Initialize profile coordinate track to a clean blank zero array if empty
                if current_user.persona_vector_data is None:
                    current_user.persona_vector_data = [0.0] * 768

                # 📉 Apply Vector Subtraction: Vector coordinates shift opposite to the disliked vibe
                # A penalty rate of 0.15 gives the choice a noticeable, controlled nudge
                PENALTY_RATE = 0.15
                updated_coordinates = []
                
                for current_coord, negative_coord in zip(current_user.persona_vector_data, negative_vibe_vector):
                    updated_coordinates.append(current_coord - (PENALTY_RATE * negative_coord))
                
                # Commit updated long-term profile array positions back to Postgres
                current_user.persona_vector_data = updated_coordinates
                db.commit()
                print("✅ [FlickFind Taste Engine] Long-term user profile vector updated successfully.")

        return {"status": "success", "message": "Dislike metrics tracked successfully and preference profile shifted."}

    except Exception as e:
        import traceback
        print("🚨 DISLIKE CAPTURE FAILURE:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Tracking pipeline fault: {str(e)}")

from schemas import UserCreate, UserLogin, UserResponse
from auth_utils import hash_user_password, verify_user_password
# main.py - High-Throughput Latency Optimization Phase


@app.post("/api/v1/recommend/mood", response_model=ChattedRecommendationResponse)
async def analyze_mood_chat(
    request: MoodRequest, 
    user_id: Optional[int] = None,  # Dynamic authenticated user tracker injected
    db: Session = Depends(database.get_db)
):
    user_message = request.mood_text
    
    try:
        # 🧼 STEP 1: CONCATENATE LIVE CHAT MEMORY STREAM
        # 🧼 STEP 1: CONCATENATE LIVE CHAT MEMORY STREAM
        formatted_history = ""
        for msg in request.chat_history:
            formatted_history += f"{msg.role.upper()}: {msg.text}\n"
        formatted_history += f"USER CURRENT COMMAND: {user_message}"

        # 🧠 STEP 2: STRUCTURED HIGH-SPEED CONTEXT COMPILER & OVERRIDE SWITCH (Gemini Pass)
        # We leverage the compiler to generate both the text payload and evaluate profile bypasses intelligently.
        context_compile_prompt = f"""
        You are an expert cinematic context extractor and routing gatekeeper. Review the following conversational stream history between a user and an AI film assistant.
        
        TASK 1: Extract all explicit and implicit movie preferences, emotional layers, pacing requests, atmospheres, visual descriptions, 
        and sonic elements mentioned across ALL turns of the dialogue into a single dense, continuous search query paragraph for 'dense_search_query'.
        Focus strictly on thematic elements, tone, and cinematic styles requested. Do not include introductory text.

        TASK 2: Evaluate 'should_bypass_profile'. Set this field to true if the user explicitly or implicitly requests a change of pace, 
        wants to ignore their profile context, desires 'something completely new/different', or describes a mood/genre direction 
        that intentionally breaks away from their long-term established sidebar parameters. Otherwise, default to false.

        [CONVERSATION STREAM MEMORY]
        {formatted_history}
        """

        compiled_context_turn = genai_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=context_compile_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CompiledContextPayload, # 👈 Drives structured engine compilation
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        
        # Validate and unpack the compiler payload structure safely
        compiler_result = CompiledContextPayload.model_validate_json(compiled_context_turn.text)
        
        dense_search_context = compiler_result.dense_search_query.strip()
        explicit_override = compiler_result.should_bypass_profile
        
        print(f"\n📡 [FlickFind Context Compiler] Intelligent Profile Bypass Switch Active: {explicit_override}")
        print(f"📡 [FlickFind Context Compiler] Flattened Search Input:\n{dense_search_context}\n")

        # 🏎️ STEP 3: RUN LOCAL VECTOR INFERENCE ON THE ACCUMULATED CONTEXT
        vector_signature = ai_engine.generate_vector(dense_search_context)
        
        # 🛡️ STEP 4: CLEAN UP PARAMETER WEIGHTING BASED ON LLM ROUTING SWITCH
        min_runtime = ALGORITHM_CONFIG["MIN_RUNTIME"]
        min_rating = ALGORITHM_CONFIG["MIN_RATING"]
        min_votes = ALGORITHM_CONFIG["MIN_VOTES"]
        
        # The switch dynamically scales out the weight thresholds based on deep intent understanding
        pop_w = ALGORITHM_CONFIG["POPULARITY_MULTIPLIER"] if not explicit_override else 0.0
        rat_w = ALGORITHM_CONFIG["RATING_MULTIPLIER"] if not explicit_override else 0.0
        # 🧠 STEP 5: RETRIEVE AND EVALUATE HISTORIC TASTE PERSONA MAPPING
        persona_vector = None
        if user_id and not explicit_override:
            current_user = db.query(models.User).filter(models.User.id == user_id).first()
            if current_user and current_user.persona_vector_data is not None:
                if any(v != 0.0 for v in current_user.persona_vector_data):
                    persona_vector = current_user.persona_vector_data

        # 🎯 STEP 6: CONSTRUCT CORES POLL AND APPLY EXCLUSIONS
        from sqlalchemy import func
        movie_query = db.query(models.Movie).filter(
            models.Movie.runtime >= min_runtime,
            models.Movie.imdb_rating >= min_rating,
            models.Movie.imdb_votes >= min_votes
        )

        # Apply user account dislike blacklists
        if user_id:
            disliked_records = db.query(models.UserDislikedFilter.movie_id).filter(
                models.UserDislikedFilter.user_id == user_id
            ).all()
            if disliked_records:
                flat_disliked_ids = [record[0] for record in disliked_records]
                movie_query = movie_query.filter(~models.Movie.id.in_(flat_disliked_ids))

        # 🛑 ANTI-REPETITION FILTER: Exclude entries already loaded or seen in the frontend session frame
        if request.displayed_movie_ids:
            movie_query = movie_query.filter(~models.Movie.id.in_(request.displayed_movie_ids))

        # Calculate distances
        prompt_distance = models.Movie.mood_vector_data.cosine_distance(vector_signature)
        
        if persona_vector is not None:
            persona_weight = ALGORITHM_CONFIG["LONG_TERM_PERSONA_WEIGHT"]
            sorting_metric = ((1.0 - persona_weight) * prompt_distance) + (persona_weight * models.Movie.mood_vector_data.cosine_distance(persona_vector))
        else:
            sorting_metric = prompt_distance

        # Logarithmic scaling to keep raw popularity integers from breaking the vector coordinates
        log_popularity = func.ln(models.Movie.popularity + 1)

        raw_candidates = (
            movie_query.order_by(
                sorting_metric - 
                (log_popularity * pop_w) - 
                (models.Movie.imdb_rating * rat_w)
            )
            .limit(ALGORITHM_CONFIG["CANDIDATE_POOL_LIMIT"])
            .all()
        )
        
        # 🔄 AUTOMATIC ESCAPE HATCH: If strict filters yield nothing, drop thresholds
        if not raw_candidates:
            print("⚠️ [FlickFind Engine] Strict filters returned 0 rows. Executing baseline recovery pass...")
            fallback_query = db.query(models.Movie)
            if request.displayed_movie_ids:
                fallback_query = fallback_query.filter(~models.Movie.id.in_(request.displayed_movie_ids))
            raw_candidates = (
                fallback_query.order_by(prompt_distance)
                .limit(30)
                .all()
            )
        
        if not raw_candidates:
            return ChattedRecommendationResponse(
                is_context_sufficient=True,
                ai_followup_chat="Our movie data catalog is completely unpopulated. Please make sure to run your database seeder pipeline script!",
                recommendations=[]
            )

        # 🧠 STEP 7: IN-MEMORY MOOD BOUNDED SHUFFLING
        absolute_best_matches = raw_candidates[:5]
        deeper_mood_pool = raw_candidates[5:]
        
        sampled_variance = random.sample(deeper_mood_pool, min(len(deeper_mood_pool), 25))
        sampled_candidates = absolute_best_matches + sampled_variance

        # 🛡️ STEP 8: BUNDLE PERSISTENT SIDEBAR PROFILE METRICS
        profile_context = "No profile constraints tracking active."
        if request.user_profile:
            p = request.user_profile
            profile_context = f"Favorite Genres: {p.favorite_genres} | Disliked/Exclude Genres: {p.disliked_genres} | Preferred Eras: {p.preferred_eras}"

        local_movie_context = "\n".join([
            f"ID: {m.id} | Title: {m.title} | Year: {m.release_year} | Rating: {m.imdb_rating} | Runtime: {m.runtime}m | Genres: {m.genres or 'N/A'} | Director: {m.director or 'Unknown'} | Cinematographer: {m.director_of_photography or 'Unknown'} | Composer: {m.music_composer or 'Unknown'} | PosterPath: {m.poster_path or ''}" 
            for m in sampled_candidates
        ])

        # 🧠 STEP 9: UNIFIED SPEED-FOCUSED CONCIERGE PROMPT
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

        unified_response = genai_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=generation_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChattedRecommendationResponse,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
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