from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Research topic to review")
