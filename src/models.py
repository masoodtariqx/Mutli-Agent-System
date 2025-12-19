from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PredictionOutcome(str, Enum):
    YES = "YES"
    NO = "NO"

class KeyFact(BaseModel):
    claim: str
    source: str

class PredictionOutput(BaseModel):
    event_id: str
    prediction: PredictionOutcome
    probability: float = Field(ge=0.0, le=1.0)
    key_facts: List[KeyFact]
    rationale: str

class EventMetadata(BaseModel):
    event_id: str
    title: str
    description: str
    resolution_rules: str
    market_probability: Optional[float] = None
    liquidity: Optional[float] = None
    resolution_date: str
