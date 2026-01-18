"""
FastAPI Main Application
Exposes REST API for the Cost-Quality Optimization System
"""

import logging
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
import json
from datetime import datetime
from decimal import Decimal

from backend.schemas import (
    ReplayRequest,
    AnalysisReport,
    HistoricalPrompt,
    ReplayResult,
    QualityMetrics,
    Recommendation,
    ParetoPoint
)
from backend.replay_engine import replay_engine
from backend.quality_scorer import quality_scorer
from backend.recommender import recommendation_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def custom_json_serializer(obj):
    """Custom serializer for datetime objects and decimals"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def convert_floats_in_dict(obj):
    """Recursively convert scientific notation floats to regular floats in dict/list"""
    if isinstance(obj, dict):
        return {k: convert_floats_in_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_in_dict(item) for item in obj]
    elif isinstance(obj, float):
        # Convert to string without scientific notation
        if abs(obj) < 0.0001 and obj != 0:
            return float(f"{obj:.10f}".rstrip('0').rstrip('.'))
        elif abs(obj) < 1:
            return float(f"{obj:.10f}".rstrip('0').rstrip('.'))
        else:
            return obj
    else:
        return obj


# Create FastAPI app
app = FastAPI(
    title="Cost-Quality Optimization System",
    description="Replay historical LLM prompts across models to find optimal cost-quality trade-offs",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Cost-Quality Optimization System",
        "version": "1.0.0"
    }


@app.post("/api/replay")
async def replay_and_analyze(request: ReplayRequest):
    """
    Main endpoint: Replay prompts across models and return analysis
    """
    
    try:
        logger.info(f"Received replay request: {len(request.prompts)} prompts, {len(request.models)} models")
        
        # Validate input
        if not request.prompts:
            raise HTTPException(status_code=400, detail="No prompts provided")
        
        if not request.models:
            raise HTTPException(status_code=400, detail="No models specified")
        
        if len(request.models) < 2:
            raise HTTPException(status_code=400, detail="At least 2 models required for comparison")
        
        # Step 1: Replay prompts across all models
        results = replay_engine.replay_batch(
            prompts=request.prompts,
            models=request.models,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_validation=True,
            validation_phase="production"
        )
        
        # Step 2: Calculate quality metrics per model
        metrics_dict = quality_scorer.aggregate_metrics(results)
        
        # Step 3: Find Pareto frontier
        pareto_frontier = recommendation_engine.find_pareto_frontier(metrics_dict)
        
        # Step 4: Generate recommendation
        recommendation = recommendation_engine.recommend(metrics_dict)
        
        # Build response
        report = AnalysisReport(
            summary=metrics_dict,
            pareto_frontier=pareto_frontier,
            recommendation=recommendation,
            all_results=results
        )
        
        logger.info(f"Analysis complete. Recommended: {recommendation.recommended_model}")
        
        # Convert to dict
        report_dict = report.model_dump()
        
        # Convert scientific notation floats BEFORE JSON serialization
        report_dict = convert_floats_in_dict(report_dict)
        
        # Return as JSONResponse (FastAPI handles serialization)
        return JSONResponse(
            content=json.loads(
                json.dumps(report_dict, default=custom_json_serializer)
            )
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error during replay: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/quick-test")
async def quick_test(models: List[str]):
    """
    Quick test endpoint - replays a simple prompt across specified models
    Useful for testing the system
    """
    
    test_prompt = HistoricalPrompt(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one sentence."}
        ],
        metadata={"test": True}
    )
    
    request = ReplayRequest(
        prompts=[test_prompt],
        models=models,
        temperature=0.0,
        max_tokens=100
    )
    
    return await replay_and_analyze(request)


@app.get("/api/models")
async def get_supported_models():
    """Return list of commonly supported models"""
    return {
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
            {"id": "claude-3-5-sonnet-20250122", "name": "Claude 3.5 Sonnet", "provider": "Anthropic"},
            {"id": "claude-3-5-haiku-20250122", "name": "Claude 3.5 Haiku", "provider": "Anthropic"},
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
