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