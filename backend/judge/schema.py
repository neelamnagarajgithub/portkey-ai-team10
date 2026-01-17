from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class JudgeScore(BaseModel):
    """Result from LLM judge evaluation"""
    score: float = Field(ge=0, le=100, description="Quality score from 0-100")
    reasoning: str = Field(description="Explanation of the score")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    correctness: float = Field(ge=0, le=100, description="Factual accuracy")
    helpfulness: float = Field(ge=0, le=100, description="How well it addresses query")
    instruction_following: float = Field(ge=0, le=100, description="Follows prompt requirements")


class ComparisonResult(BaseModel):
    """Pairwise comparison of two model outputs"""
    winner: str
    loser: str
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    reasoning: str
    margin: float = Field(description="Score difference")

