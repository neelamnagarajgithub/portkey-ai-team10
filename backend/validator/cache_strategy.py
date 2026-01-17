"""
Smart Cache Strategy - 4-Level Lookup
Maximizes cache hits through intelligent fallback hierarchy
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
# Line 8 - fix import path
from backend.classifier.model_families import get_model_family, get_family_models, get_transfer_confidence


@dataclass
class CacheResult:
    """Result from cache lookup"""
    score: float
    confidence: str  # HIGH, MEDIUM, LOW
    source: str  # exact_match, scenario_similar, model_family, scenario_baseline
    method: str  # historical_db, family_transfer, etc.
    reasoning: str
    sample_count: int = 1
    adjustment: float = 0.0  # Score adjustment for confidence


class SmartCacheStrategy:
    """
    4-level cache lookup strategy to maximize hits:
    
    Level 1: Exact Match (prompt + model + scenario)
    Level 2: Similar Prompt (same model + scenario)
    Level 3: Model Family (similar prompt + family + scenario)
    Level 4: Scenario Baseline (any model in scenario)
    """
    
    def __init__(self, historical_db):
        self.db = historical_db
    
    def lookup(
        self, 
        prompt: str, 
        model: str, 
        scenario: str,
        min_confidence: str = "MEDIUM"
    ) -> Optional[CacheResult]:
        """
        Perform 4-level cache lookup
        
        Args:
            prompt: User prompt text
            model: Target model name
            scenario: Classified scenario
            min_confidence: Minimum confidence to accept (HIGH, MEDIUM, LOW)
            
        Returns:
            CacheResult or None if no acceptable cache hit
        """
        
        # Level 1: Exact match
        result = self._exact_match(prompt, model, scenario)
        if result and self._meets_min_confidence(result.confidence, min_confidence):
            return result
        
        # Level 2: Similar prompt, same model, same scenario
        result = self._scenario_similar(prompt, model, scenario)
        if result and self._meets_min_confidence(result.confidence, min_confidence):
            return result
        
        # Level 3: Model family match
        result = self._model_family_match(prompt, model, scenario)
        if result and self._meets_min_confidence(result.confidence, min_confidence):
            return result
        
        # Level 4: Scenario baseline (use with caution)
        if min_confidence == "LOW":
            result = self._scenario_baseline(scenario)
            if result:
                return result
        
        return None
    
    def _exact_match(
        self, 
        prompt: str, 
        model: str, 
        scenario: str
    ) -> Optional[CacheResult]:
        """Level 1: Exact match lookup"""
        result = self.db.find_similar(
            prompt_text=prompt,
            model=model,
            scenario=scenario,
            limit=1
        )
        
        if result and result.avg_score is not None:
            # Exact match if similarity very high
            if hasattr(result, 'similarity') and result.similarity >= 0.95:
                return CacheResult(
                    score=result.avg_score,
                    confidence="HIGH",
                    source="exact_match",
                    method="historical_db",
                    reasoning=f"Exact match found (similarity: {result.similarity:.2f})",
                    sample_count=result.count if hasattr(result, 'count') else 1
                )
        
        return None
    
    def _scenario_similar(
        self, 
        prompt: str, 
        model: str, 
        scenario: str
    ) -> Optional[CacheResult]:
        """Level 2: Similar prompt in same scenario"""
        result = self.db.find_similar(
            prompt_text=prompt,
            model=model,
            scenario=scenario,
            limit=5
        )
        
        if result and result.avg_score is not None:
            # Accept if similarity is good
            similarity = getattr(result, 'similarity', 0.0)
            if similarity >= 0.85:
                return CacheResult(
                    score=result.avg_score,
                    confidence="HIGH",
                    source="scenario_similar",
                    method="historical_db",
                    reasoning=f"Similar prompt in same scenario (similarity: {similarity:.2f})",
                    sample_count=result.count if hasattr(result, 'count') else 1
                )
        
        return None
    
    def _model_family_match(
        self, 
        prompt: str, 
        model: str, 
        scenario: str
    ) -> Optional[CacheResult]:
        """Level 3: Model family transfer"""
        family = get_model_family(model)
        
        if family == "unknown":
            return None
        
        family_models = get_family_models(family)
        confidence_mult = get_transfer_confidence(family)
        
        # Try each family member
        for family_model in family_models:
            if family_model == model:
                continue  # Skip same model (already tried in Level 1/2)
            
            result = self.db.find_similar(
                prompt_text=prompt,
                model=family_model,
                scenario=scenario,
                limit=3
            )
            
            if result and result.avg_score is not None:
                sample_count = result.count if hasattr(result, 'count') else 1
                
                # Need at least 3 samples for family transfer
                if sample_count >= 3:
                    # Adjust score based on family confidence
                    adjusted_score = result.avg_score * confidence_mult
                    adjustment = result.avg_score - adjusted_score
                    
                    return CacheResult(
                        score=adjusted_score,
                        confidence="MEDIUM",
                        source="model_family",
                        method="family_transfer",
                        reasoning=f"Transferred from {family_model} ({sample_count} samples, {confidence_mult:.0%} confidence)",
                        sample_count=sample_count,
                        adjustment=-adjustment
                    )
        
        return None
    
    def _scenario_baseline(self, scenario: str) -> Optional[CacheResult]:
        """Level 4: Scenario average (use sparingly)"""
        # This would need a new DB method to get scenario averages
        # For now, return None to be conservative
        # TODO: Implement scenario-wide statistics
        return None
    
    def _meets_min_confidence(self, confidence: str, min_confidence: str) -> bool:
        """Check if confidence meets minimum threshold"""
        levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return levels.get(confidence, 0) >= levels.get(min_confidence, 0)
