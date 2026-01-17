"""
FastAPI Main Application
Exposes REST API for the Cost-Quality Optimization System
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

from schemas import (
    ReplayRequest,
    AnalysisReport,
    HistoricalPrompt,
    ReplayResult,
    QualityMetrics,
    Recommendation,
    ParetoPoint
)
from replay_engine import replay_engine
from quality_scorer import quality_scorer
from recommender import recommendation_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


@app.post("/api/replay", response_model=AnalysisReport)
async def replay_and_analyze(request: ReplayRequest):
    """
    Main endpoint: Replay prompts across models and return analysis
    
    - Replays all prompts with all specified models
    - Calculates quality metrics per model
    - Finds Pareto frontier
    - Generates smart recommendation
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
            max_tokens=request.max_tokens
        )
        print(results)
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
        
        return report
        
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
        "openai": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20250122",
            "claude-3-5-haiku-20250122",
            "claude-3-opus-20240229"
        ],
        "google": [
            "gemini-2.5-pro",
            "gemini-2.5-flash"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
