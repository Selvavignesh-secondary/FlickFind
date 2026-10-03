from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    text: str

class UserProfile(BaseModel):
    favorite_genres: List[str] = Field(default=[])
    disliked_genres: List[str] = Field(default=[])
    preferred_eras: List[str] = Field(default=[])
    taste_description: Optional[str] = Field(default=None)

class MoodRequest(BaseModel):
    mood_text: str
    chat_history: List[ChatMessage] = Field(default=[])
    user_profile: Optional[UserProfile] = None
    displayed_movie_ids: Optional[List[int]] = Field(default=[])


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
    is_context_sufficient: bool
    ai_followup_chat: str
    recommendations: List[MovieCard] = Field(default=[])


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


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


class CompiledContextPayload(BaseModel):
    dense_search_query: str = Field(description="The flattened, dense semantic search paragraph capturing all turns of historical and current conversation parameters.")
    should_bypass_profile: bool = Field(description="Set to true if the user explicitly or implicitly states they want something new, an override, a shift away from their usual taste profile, or an exploration of alternative genres.")