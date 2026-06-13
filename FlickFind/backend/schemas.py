# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# Individual structural tracking block for a conversation turn
class ChatMessage(BaseModel):
    role: str = Field(description="Either 'user' or 'model'")
    text: str = Field(description="The actual textual sentence written during that turn")

class UserProfile(BaseModel):
    favorite_genres: List[str] = Field(default=[])
    disliked_genres: List[str] = Field(default=[])
    preferred_eras: List[str] = Field(default=[])
    taste_description: Optional[str] = Field(default=None)

class MoodRequest(BaseModel):
    mood_text: str = Field(description="The newest raw text input from the chat window")
    chat_history: List[ChatMessage] = Field(default=[], description="The full conversation history window up to this point")
    user_profile: Optional[UserProfile] = Field(default=None)
    # 🛑 ANTI-REPETITION RUNTIME TRACKER: Allows frontend to pass down IDs that shouldn't be loaded again
    displayed_movie_ids: Optional[List[int]] = Field(default=[], description="List of movie IDs already displayed in this chat session to prevent repetition")
class MovieCard(BaseModel):
    id: int
    title: str
    release_year: int
    imdb_rating: float
    runtime: int
    director: str
    director_of_photography: Optional[str] = "Unknown"
    music_composer: Optional[str] = "Unknown"
    poster_path: Optional[str] = None
    hybrid_summary: str

class ChattedRecommendationResponse(BaseModel):
    is_context_sufficient: bool = Field(description="True if we are ready to serve movie cards. False if we need to chat more.")
    ai_followup_chat: str = Field(description="The chatbot's reply text to display in the chat bubble window.")
    recommendations: List[MovieCard] = Field(default=[])

# schemas.py - Append this to the bottom of your file
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Valid communication address")
    password: str = Field(..., min_length=6, description="Raw plaintext to be hashed")

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    watcher_tier: str

    class Config:
        from_attributes = True


# schemas.py - Append these validation schemas to the bottom of the file

class WatchlistAction(BaseModel):
    user_id: int
    movie_id: int

class WatchedAction(BaseModel):
    user_id: int
    movie_id: int
    rating: Optional[float] = None
    critic_review: Optional[str] = None

class DislikeAction(BaseModel):
    user_id: int
    movie_id: int
    rejection_reason: str        

# schemas.py - Append to the bottom of the file
class CompiledContextPayload(BaseModel):
    dense_search_query: str = Field(description="The flattened, dense semantic search paragraph capturing all turns of historical and current conversation parameters.")
    should_bypass_profile: bool = Field(description="Set to true if the user explicitly or implicitly states they want something new, an override, a shift away from their usual taste profile, or an exploration of alternative genres.")