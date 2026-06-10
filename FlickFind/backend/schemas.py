from pydantic import BaseModel, Field
from typing import List

# =====================================================================
# 📥 REQUEST SCHEMAS (What the React frontend sends TO your API)
# =====================================================================
class MoodRequest(BaseModel):
    mood_text: str = Field(description="The conversational text or prompt input from the user chat window.")


# =====================================================================
# 📤 RESPONSE SCHEMAS (What the Python API sends BACK to your frontend)
# =====================================================================

# 🎬 Blueprint for an individual movie card rendered on screen
class MovieCard(BaseModel):
    id: int
    title: str
    release_year: int
    director: str = Field(description="The director found by the Web Agent")
    poster_url: str = Field(description="The TMDB poster image link or web placeholder path")
    
    # 🧠 The combined text requirements
    hybrid_summary: str = Field(
        description="A seamless synthesis combining a brief summary of the movie plot AND the custom AI explanation of why it fits the user's specific mood request. Strict maximum limit of 4 sentences."
    )

# 📦 The full conversational agent packet sent across the HTTP wire
class ChattedRecommendationResponse(BaseModel):
    is_context_sufficient: bool = Field(
        description="True if the prompt has enough detail to recommend films. False if it is too vague or basic."
    )
    ai_followup_chat: str = Field(
        description="If context is insufficient, ask targeted, helpful clarifying questions. If sufficient, write an engaging opening intro to the picks."
    )
    recommendations: List[MovieCard] = Field(
        default=[],
        description="List of 5 recommended MovieCard objects if context is sufficient. Otherwise, leave empty."
    )