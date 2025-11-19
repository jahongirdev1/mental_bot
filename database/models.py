from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CheckIn(BaseModel):
    user_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    mood: str
    cause: str


class StressTestResult(BaseModel):
    user_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    score: int
    level: str
    details: Optional[list[str]] = None
