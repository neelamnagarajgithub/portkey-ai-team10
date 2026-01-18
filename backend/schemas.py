from pydantic import BaseModel, Field, field_serializer
from typing import List, Dict, Optional, Any
from datetime import datetime


class HistoricalPrompt(BaseModel):
    """A single historical LLM call to replay"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    messages: List[Dict[str, str]] = Field(description="Chat messages in OpenAI format")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    original_model: Optional[str] = None
    original_cost: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "What is 2+2?"}
                ],
                "metadata": {"use_case": "math_qa"}
            }
        }


class ReplayResult(BaseModel):
    """Result of replaying a prompt with a specific model"""
    prompt_id: str
    model: str
    provider: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    
    # Cost metrics
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    
    @field_serializer('cost_usd')
    def serialize_cost(self, value: float) -> float:
        """Round cost to 8 decimal places to avoid scientific notation"""
        return round(value, 8) if value else 0.0
    
    # Performance metrics
    latency_ms: float = 0.0
    
    # Quality indicators
    is_refusal: bool = False
    schema_valid: bool = True
    
    # Validation scores (from hybrid validator)
    validation_score: Optional[float] = None
    validation_method: Optional[str] = None
    validation_confidence: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)


class QualityMetrics(BaseModel):
    """Aggregated quality metrics for a model across all replays"""
    model: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    refusal_rate: float
    
    # Cost aggregates
    avg_cost_per_call: float
    total_cost: float
    
    # Performance aggregates
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    
    # Quality scores
    consistency_score: float = Field(ge=0.0, le=1.0, description="How consistent outputs are")
    schema_compliance_rate: float = Field(ge=0.0, le=1.0)
    avg_validation_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Average validation score from hybrid validator")


class ParetoPoint(BaseModel):
    """A point on the Pareto frontier"""
    model: str
    cost: float
    quality: float
    is_optimal: bool = False


class Recommendation(BaseModel):
    """Smart recommendation for model selection"""
    recommended_model: str
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    
    # Comparison to baseline (usually most expensive model)
    baseline_model: str
    cost_savings_pct: float
    cost_savings_usd_per_1k: float
    quality_retention_pct: float
    
    # Supporting evidence
    reasoning: str
    tested_on_calls: int
    
    # Risk assessment
    risks: List[str] = Field(default_factory=list)


class ReplayRequest(BaseModel):
    """API request to trigger replay"""
    prompts: List[HistoricalPrompt]
    models: List[str] = Field(
        description="Models to test",
        examples=[["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20250122"]]
    )
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0, le=4096)


class AnalysisReport(BaseModel):
    """Complete analysis report"""
    summary: Dict[str, QualityMetrics]
    pareto_frontier: List[ParetoPoint]
    recommendation: Recommendation
    all_results: List[ReplayResult]
    generated_at: datetime = Field(default_factory=datetime.now)
