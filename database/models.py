from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CheckIn(BaseModel):
    user_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    mood: str
    cause: str
    mood_score: Optional[int] = None


class StressTestResult(BaseModel):
    user_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    score: int
    level: str
    details: Optional[list[str]] = None
