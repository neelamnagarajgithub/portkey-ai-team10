"""
Hybrid Validator
Combines multiple validation methods with intelligent fallback
"""

import logging
import random
from typing import Optional
from pydantic import BaseModel, Field
from schemas import HistoricalPrompt
from llm_judge import llm_judge
from judge.schema import JudgeScore
from validator.heuristic_validator import heuristic_validator, HeuristicScore
from db.historical_db import historical_db, DBResult
from classifier import scenario_classifier, extract_provider, get_model_family
from classifier.scenario_config import get_scenario_config, should_use_llm_judge
from validator.cache_strategy import SmartCacheStrategy

logger = logging.getLogger(__name__)


class ValidationScore(BaseModel):
    """Unified validation result"""
    score: float = Field(ge=0, le=100, description="Quality score 0-100")
    method: str = Field(description="Primary validation method used")
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    reasoning: str
    
    # Supporting evidence
    llm_judge_score: Optional[float] = None
    heuristic_score: Optional[float] = None
    db_score: Optional[float] = None
    
    # Metadata
    methods_used: list = Field(default_factory=list)


class HybridValidator:
    """
    Intelligent validation using multiple methods with fallback
    """
    
    def __init__(
        self,
        use_llm_judge: bool = True,
        llm_judge_budget: float = 100.0,  # Max $ for judge calls
        llm_judge_sample_rate: float = 1.0  # Use judge on % of prompts
    ):
        """
        Initialize Hybrid Validator
        
        Args:
            use_llm_judge: Whether to use LLM judge
            llm_judge_budget: Maximum budget for LLM judge calls
            llm_judge_sample_rate: Percentage of prompts to validate with LLM judge (0.0-1.0)
        """
        self.use_llm_judge = use_llm_judge
        self.llm_judge_budget = llm_judge_budget
        self.llm_judge_sample_rate = llm_judge_sample_rate
        self.llm_judge_cost = 0.0
        self.cache_strategy = SmartCacheStrategy(historical_db)
        self.scenario_classifier = scenario_classifier
        
        self.stats = {
            "llm_judge_calls": 0,
            "heuristic_calls": 0,
            "db_hits": 0,
            "db_misses": 0
        }
    
    def validate(
        self,
        prompt: HistoricalPrompt,
        output: str,
        model: str,
        phase: str = "discovery",
        force_llm_judge: bool = False
    ) -> ValidationScore:
        """
        Validate output using multiple methods with intelligent fallback
        
        Args:
            prompt: Original prompt
            output: Model's response
            model: Model name
            phase: "discovery" or "production" (affects strategy)
            force_llm_judge: Force LLM judge usage (ignore budget/sampling)
        
        Returns:
            ValidationScore with consolidated result
        """
        methods_used = []
        
        # Step 1: Classify scenario
        prompt_text = self._format_prompt(prompt)
        scenario = self.scenario_classifier.classify(prompt_text)
        scenario_config = get_scenario_config(scenario)
        
        # Step 2: Smart Cache Lookup (4-level)
        cache_result = self.cache_strategy.lookup(
            prompt=prompt_text,
            model=model,
            scenario=scenario,
            min_confidence="MEDIUM"  # Accept MEDIUM or higher
        )
        
        if cache_result and cache_result.confidence == "HIGH":
            # High confidence from smart cache
            self.stats["db_hits"] += 1
            
            # Cache result, store for future
            self._cache_result(prompt, output, model, cache_result.score, cache_result.method, cache_result.confidence, scenario)
            
            return ValidationScore(
                score=cache_result.score,
                method=cache_result.source,
                confidence=cache_result.confidence,
                reasoning=cache_result.reasoning,
                db_score=cache_result.score,
                methods_used=[cache_result.source]
            )
        
        if cache_result:
            methods_used.append(cache_result.source)
        else:
            self.stats["db_misses"] += 1
        
        # Step 3: Run Heuristics (always - fast and free!)
        heuristic_result = self._run_heuristics(output)
        methods_used.append("heuristics")
        
        if heuristic_result.confidence == "HIGH":
            # Heuristics are confident, potentially use them
            
            # If it's a clear failure (score < 30), trust heuristics
            if heuristic_result.score < 30:
                score = self._combine_scores(
                    heuristic_score=heuristic_result.score,
                    db_score=cache_result.score if cache_result else None,
                    scenario_config=scenario_config
                )
                
                # Store result
                self._cache_result(prompt, output, model, score, "heuristics", "HIGH", scenario)
                
                return ValidationScore(
                    score=score,
                    method="heuristics",
                    confidence="HIGH",
                    reasoning=heuristic_result.reasoning,
                    heuristic_score=heuristic_result.score,
                    db_score=cache_result.score if cache_result else None,
                    methods_used=methods_used
                )
        
        # Step 4: LLM Judge (expensive, use strategically with scenario config)
        should_use_judge = force_llm_judge or should_use_llm_judge(
            scenario=scenario,
            db_confidence=cache_result.confidence if cache_result else None
        )
        
        if should_use_judge and self.use_llm_judge:
            judge_result = self._run_llm_judge(prompt, output, model)
            
            if judge_result:
                methods_used.append("llm_judge")
                
                # Combine all available scores
                score = self._combine_scores(
                    llm_judge_score=judge_result.score,
                    heuristic_score=heuristic_result.score,
                    db_score=cache_result.score if cache_result else None,
                    scenario_config=scenario_config
                )
                
                # Cache this result for future lookups
                return ValidationScore(
                    score=score,
                    method="ensemble",
                    confidence="HIGH",
                    reasoning=judge_result.reasoning,
                    llm_judge_score=judge_result.score,
                    heuristic_score=heuristic_result.score,
                    db_score=cache_result.score if cache_result else None,
                    methods_used=methods_used
                )
        
        # Fallback: Use heuristics + DB
        score = self._combine_scores(
            heuristic_score=heuristic_result.score,
            db_score=cache_result.score if cache_result else None
        )
        
        confidence = "MEDIUM" if cache_result else heuristic_result.confidence
        
        # Cache heuristic result
        self._cache_result(prompt, model, output, score, "heuristics", confidence)
        
        return ValidationScore(
            score=score,
            method="heuristics" if not cache_result else "heuristics+db",
            confidence=confidence,
            reasoning=heuristic_result.reasoning,
            heuristic_score=heuristic_result.score,
            db_score=cache_result.score if cache_result else None,
            methods_used=methods_used
        )
    
    def _check_db(self, prompt: HistoricalPrompt, model: str) -> Optional[DBResult]:
        """Check historical database for similar prompts"""
        try:
            prompt_text = self._format_prompt(prompt)
            return historical_db.find_similar(prompt_text, model)
        except Exception as e:
            logger.error(f"DB lookup failed: {e}")
            return None
    
    def _run_heuristics(self, output: str) -> HeuristicScore:
        """Run heuristic validation"""
        self.stats["heuristic_calls"] += 1
        return heuristic_validator.validate(output)
    
    def _run_llm_judge(
        self, 
        prompt: HistoricalPrompt, 
        output: str, 
        model: str
    ) -> Optional[JudgeScore]:
        """Run LLM judge evaluation (async-aware)"""
        try:
            import asyncio
            
            # Estimate cost (rough)
            estimated_cost = 0.01  # ~$0.01 per judge call
            
            if self.llm_judge_cost + estimated_cost > self.llm_judge_budget:
                logger.warning(f"LLM judge budget exhausted (${self.llm_judge_cost:.2f})")
                return None
            
            # Call async function and handle coroutine
            result = llm_judge.evaluate_single(prompt, output, model)
            
            # If it's a coroutine, run it
            if hasattr(result, '__await__'):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # In running loop, use run_in_executor
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, result)
                            result = future.result(timeout=30)
                    else:
                        result = asyncio.run(result)
                except RuntimeError:
                    # No event loop, create one
                    result = asyncio.run(result)
            
            self.stats["llm_judge_calls"] += 1
            self.llm_judge_cost += estimated_cost
            
            return result
            
        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return None
    
    def _should_use_llm_judge(self, phase: str) -> bool:
        """Decide whether to use LLM judge based on phase and sampling"""
        if phase == "discovery":
            # Always use in discovery phase (within budget)
            return random.random() < self.llm_judge_sample_rate
        else:
            # Production: 10% sampling
            return random.random() < 0.1
    
    def _combine_scores(
        self,
        llm_judge_score: Optional[float] = None,
        heuristic_score: Optional[float] = None,
        db_score: Optional[float] = None,
        scenario_config: dict = None
    ) -> float:
        """
        Combine multiple scores using scenario-aware weighted average
        
        Args:
            llm_judge_score: Score from LLM judge (0-100)
            heuristic_score: Score from heuristics (0-100)
            db_score: Score from historical DB (0-100)
            scenario_config: Scenario-specific configuration with weights
            
        Returns:
            Combined score (0-100)
        """
        # Use default weights if no scenario_config
        if scenario_config is None:
            scenario_config = get_scenario_config("general")
        
        scores = []
        weights = []
        
        if llm_judge_score is not None:
            scores.append(llm_judge_score)
            weights.append(scenario_config.get("llm_judge_weight", 0.60))
        
        if heuristic_score is not None:
            scores.append(heuristic_score)
            weights.append(scenario_config.get("heuristic_weight", 0.25))
        
        if db_score is not None:
            scores.append(db_score)
            weights.append(scenario_config.get("db_weight", 0.15))
        
        if not scores:
            return 50.0  # Default neutral score
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return sum(scores) / len(scores)
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / total_weight
    
    def _cache_result(
        self,
        prompt: HistoricalPrompt,
        output: str,
        model: str,
        score: float,
        method: str,
        confidence: str,
        scenario: str = None
    ):
        """Cache validation result in historical DB"""
        try:
            prompt_text = self._format_prompt(prompt)
            
            # Auto-extract provider if not provided
            provider = extract_provider(model)
            
            # Auto-classify scenario if not provided
            if scenario is None:
                scenario = self.scenario_classifier.classify(prompt_text)
            
            historical_db.store_validation(
                prompt_text=prompt_text,
                model=model,
                provider=provider,
                scenario=scenario,
                output=output,
                score=score,
                method=method,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
    
    def _format_prompt(self, prompt: HistoricalPrompt) -> str:
        """Format prompt for storage/lookup"""
        return " ".join(msg.get("content", "") for msg in prompt.messages)
    
    def get_stats(self):
        """Get validator statistics"""
        return {
            **self.stats,
            "llm_judge_cost": self.llm_judge_cost,
            "db_stats": historical_db.get_stats(),
            "judge_stats": llm_judge.get_stats()
        }


# Singleton instance
hybrid_validator = HybridValidator()
