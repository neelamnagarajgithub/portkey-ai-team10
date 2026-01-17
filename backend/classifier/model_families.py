"""
Model Family Configuration
Groups models by family for knowledge transfer
"""

MODEL_FAMILIES = {
    "openai_gpt4": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-4-turbo-preview"],
        "transfer_confidence": 0.85,  # 85% confidence in family transfer
        "provider": "openai"
    },
    "openai_gpt35": {
        "models": ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-1106"],
        "transfer_confidence": 0.90,
        "provider": "openai"
    },
    "anthropic_claude3": {
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "transfer_confidence": 0.80,
        "provider": "anthropic"
    },
    "anthropic_claude35": {
        "models": ["claude-3-5-sonnet", "claude-3-5-haiku", "claude-3-5-sonnet-20250122"],
        "transfer_confidence": 0.85,
        "provider": "anthropic"
    },
    "google_gemini": {
        "models": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
        "transfer_confidence": 0.80,
        "provider": "google"
    },
    "meta_llama3": {
        "models": [
            "meta.llama-3.2-90b-vision-instruct-maas",
            "meta.llama-3.1-405b-instruct-maas",
            "meta.llama-3.1-70b-instruct-maas",
            "llama-3.2-90b",
            "llama-3.1-405b",
            "llama-3.1-70b"
        ],
        "transfer_confidence": 0.80,
        "provider": "meta"
    }
}


def get_model_family(model: str) -> str:
    """
    Return model family for knowledge transfer
    
    Args:
        model: Model name (e.g., 'gpt-4o', 'claude-3-5-sonnet')
        
    Returns:
        Family name (e.g., 'openai_gpt4') or 'unknown'
    """
    model_lower = model.lower()
    
    for family, config in MODEL_FAMILIES.items():
        if any(m.lower() in model_lower for m in config["models"]):
            return family
    
    return "unknown"


def get_family_models(family: str) -> list:
    """Get all models in a family"""
    if family in MODEL_FAMILIES:
        return MODEL_FAMILIES[family]["models"]
    return []


def get_transfer_confidence(family: str) -> float:
    """Get confidence level for family transfer"""
    if family in MODEL_FAMILIES:
        return MODEL_FAMILIES[family]["transfer_confidence"]
    return 0.5  # Low confidence for unknown families


def extract_provider(model: str) -> str:
    """
    Extract provider from model name
    
    Args:
        model: Model name
        
    Returns:
        Provider name (openai, anthropic, google, meta, unknown)
    """
    model_lower = model.lower()
    
    # Check model families first (most accurate)
    family = get_model_family(model)
    if family != "unknown" and family in MODEL_FAMILIES:
        return MODEL_FAMILIES[family]["provider"]
    
    # Fallback to pattern matching
    if "gpt" in model_lower or "openai" in model_lower:
        return "openai"
    elif "claude" in model_lower or "anthropic" in model_lower:
        return "anthropic"
    elif "gemini" in model_lower or "vertex" in model_lower:
        return "google"
    elif "llama" in model_lower or "meta" in model_lower:
        return "meta"
    
    return "unknown"
