from pydantic import BaseModel, Field

class MoodRequest(BaseModel):
    # This field captures the natural language prompt from the user
    mood_text: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="The natural language description of the user's current emotional state."
    )