"""
Scenario-specific validation configuration
Different strategies per scenario type
"""

SCENARIO_CONFIG = {
    "code_generation": {
        # Cache strategy
        "cache_ttl_days": 7,  # Code changes fast
        "min_samples_for_transfer": 5,
        "similarity_threshold": 0.80,  # Stricter for code
        
        # LLM Judge
        "llm_judge_rate": 0.20,  # 20% for new code prompts
        "judge_tier": "high",  # Use better models
        
        # Validation weights
        "heuristic_weight": 0.40,  # High weight (syntax checks)
        "db_weight": 0.60,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 85,
        
        # Model preferences
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet"],
        "avoid_models": []
    },
    
    "factual_qa": {
        # Cache strategy
        "cache_ttl_days": 90,  # Facts don't change often
        "min_samples_for_transfer": 3,
        "similarity_threshold": 0.90,  # Very strict for facts
        
        # LLM Judge
        "llm_judge_rate": 0.15,  # 15% for facts
        "judge_tier": "high",
        
        # Validation weights
        "heuristic_weight": 0.30,
        "db_weight": 0.70,  # High trust in cached facts
        "llm_judge_weight": 0.60,
        "min_confidence_score": 90,
        
        # Model preferences
        "preferred_models": ["gpt-4o", "gpt-4-turbo"],
        "avoid_models": []
    },
    
    "creative_writing": {
        # Cache strategy
        "cache_ttl_days": 30,
        "min_samples_for_transfer": 10,  # Need more samples (subjective)
        "similarity_threshold": 0.70,  # Looser (more variance)
        
        # LLM Judge
        "llm_judge_rate": 0.05,  # Only 5% (subjective)
        "judge_tier": "medium",
        
        # Validation weights
        "heuristic_weight": 0.20,  # Low weight (subjective)
        "db_weight": 0.30,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 60,
        
        # Model preferences
        "preferred_models": ["claude-3-5-sonnet", "gpt-4o"],
        "avoid_models": ["gpt-3.5-turbo"]
    },
    
    "translation": {
        # Cache strategy
        "cache_ttl_days": 60,
        "min_samples_for_transfer": 5,
        "similarity_threshold": 0.85,
        
        # LLM Judge
        "llm_judge_rate": 0.10,
        "judge_tier": "medium",
        
        # Validation weights
        "heuristic_weight": 0.25,
        "db_weight": 0.50,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 80,
        
        # Model preferences
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet"],
        "avoid_models": []
    },
    
    "summarization": {
        # Cache strategy
        "cache_ttl_days": 14,
        "min_samples_for_transfer": 5,
        "similarity_threshold": 0.75,
        
        # LLM Judge
        "llm_judge_rate": 0.10,
        "judge_tier": "medium",
        
        # Validation weights
        "heuristic_weight": 0.30,
        "db_weight": 0.50,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 75,
        
        # Model preferences
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet"],
        "avoid_models": []
    },
    
    "analysis": {
        # Cache strategy
        "cache_ttl_days": 30,
        "min_samples_for_transfer": 5,
        "similarity_threshold": 0.80,
        
        # LLM Judge
        "llm_judge_rate": 0.15,
        "judge_tier": "high",
        
        # Validation weights
        "heuristic_weight": 0.30,
        "db_weight": 0.60,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 85,
        
        # Model preferences
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet"],
        "avoid_models": []
    },
    
    "general": {
        # Default config
        "cache_ttl_days": 30,
        "min_samples_for_transfer": 5,
        "similarity_threshold": 0.80,
        
        # LLM Judge
        "llm_judge_rate": 0.10,  # 10% default
        "judge_tier": "medium",
        
        # Validation weights
        "heuristic_weight": 0.25,
        "db_weight": 0.50,
        "llm_judge_weight": 0.60,
        "min_confidence_score": 75,
        
        # Model preferences
        "preferred_models": [],
        "avoid_models": []
    }
}


def get_scenario_config(scenario: str) -> dict:
    """
    Get configuration for a scenario
    
    Args:
        scenario: Scenario name
        
    Returns:
        Configuration dict with weights, rates, etc.
    """
    return SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["general"])


def should_use_llm_judge(scenario: str, db_confidence: str = None) -> bool:
    """
    Decide if LLM judge should be used based on scenario and DB confidence
    
    Args:
        scenario: Scenario name
        db_confidence: Confidence from DB (HIGH, MEDIUM, LOW, None)
        
    Returns:
        True if LLM judge should be used
    """
    import random
    
    config = get_scenario_config(scenario)
    base_rate = config["llm_judge_rate"]
    
    # Skip if DB is highly confident
    if db_confidence == "HIGH":
        return random.random() < 0.01  # Only 1% for verification
    
    # Use scenario-specific rate
    return random.random() < base_rate
