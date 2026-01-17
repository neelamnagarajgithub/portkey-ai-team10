from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import logging
import json
from typing import Any

from backend.schemas import ReplayRequest, AnalysisReport
from backend.replay_engine import replay_engine
from backend.quality_scorer import quality_scorer
from backend.recommender import recommendation_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Cost-Quality Optimizer", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_float_encoder(obj: Any) -> Any:
    """Custom JSON encoder that formats floats without scientific notation"""
    if isinstance(obj, float):
        # Format very small numbers with 6 decimals
        if abs(obj) < 0.0001 and obj != 0:
            return float(f"{obj:.6f}")
        # Format small numbers (< 1) with 6 decimals
        elif abs(obj) < 1:
            return float(f"{obj:.6f}")
        # Format percentages/larger numbers with 2 decimals
        elif abs(obj) < 100:
            return round(obj, 4)
        else:
            return round(obj, 2)
    return obj


def serialize_for_json(obj: Any) -> Any:
    """Recursively serialize objects, formatting floats properly"""
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        return custom_float_encoder(obj)
    elif hasattr(obj, 'model_dump'):  # Pydantic model
        return serialize_for_json(obj.model_dump())
    elif hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    else:
        return obj


@app.get("/")
async def root():
    return {
        "message": "LLM Cost-Quality Optimizer API",
        "version": "1.0.0",
        "endpoints": {
            "replay": "/api/replay",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/replay")
async def replay_and_analyze(request: ReplayRequest):
    """
    Replay historical prompts across multiple models and generate recommendations
    """
    logger.info(f"Received replay request: {len(request.prompts)} prompts, {len(request.models)} models")
    
    # Run replay
    results = replay_engine.replay_batch(
        prompts=request.prompts,
        models=request.models,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    # Calculate quality metrics
    metrics_dict = quality_scorer.aggregate_metrics(results)
    
    # Generate recommendation
    recommendation = recommendation_engine.recommend(metrics_dict)
    
    # Find Pareto frontier
    pareto_frontier = recommendation_engine.find_pareto_frontier(metrics_dict)
    
    # Build report
    report = AnalysisReport(
        summary=metrics_dict,
        pareto_frontier=pareto_frontier,
        recommendation=recommendation,
        all_results=results
    )
    
    logger.info(f"Analysis complete. Recommended: {recommendation.recommended_model}")
    
    # Convert to dict
    report_dict = report.model_dump()
    
    # Serialize to JSON
    json_str = json.dumps(report_dict, indent=2, default=str)
    
    # **FIX: Replace all scientific notation with decimal notation**
    import re
    
    def replace_scientific(match):
        """Replace scientific notation with decimal"""
        num_str = match.group(0)
        num = float(num_str)
        
        # Format based on magnitude
        if abs(num) < 0.0001 and num != 0:
            return f"{num:.6f}"
        elif abs(num) < 1:
            return f"{num:.6f}"
        elif abs(num) < 100:
            return f"{num:.4f}"
        else:
            return f"{num:.2f}"
    
    # Pattern matches: 1.23e-05, 4.5e+10, etc.
    pattern = r'\d+\.?\d*e[+-]?\d+'
    json_str = re.sub(pattern, replace_scientific, json_str, flags=re.IGNORECASE)
    
    return Response(
        content=json_str,
        media_type="application/json"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)