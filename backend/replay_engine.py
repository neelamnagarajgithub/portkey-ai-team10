"""
Core Replay Engine
Re-runs historical prompts across multiple models using LiteLLM
"""

import time
import logging
from typing import List, Dict
from litellm import completion
from schemas import HistoricalPrompt, ReplayResult
from portkey_client import portkey_client

logger = logging.getLogger(__name__)


class ReplayEngine:
    """Replays historical LLM calls across different models"""
    
    def __init__(self):
        self.provider_map = {
            "gpt-4o": "openai",
            "gpt-4o-mini": "openai",
            "gpt-4": "openai",
            "gpt-3.5-turbo": "openai",
            "claude-3-5-sonnet-20250122": "anthropic",
            "claude-3-5-haiku-20250122": "anthropic",
            "claude-3-opus-20240229": "anthropic",
            "gemini-2.5-pro": "google",
            "gemini-2.5-flash": "google",
        }
    
    def get_provider(self, model: str) -> str:
        """Infer provider from model name"""
        # Direct match
        if model in self.provider_map:
            return self.provider_map[model]
        
        # Fuzzy match
        model_lower = model.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "vertex" in model_lower:
            return "google"
        
        # Default fallback
        return "openai"
    
    def replay_single(
        self,
        prompt: HistoricalPrompt,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> ReplayResult:
        """Replay a single prompt with a specific model"""
        
        provider = self.get_provider(model)
        
        try:
            start_time = time.time()
            
            # Call model via LiteLLM
            response = completion(
                model=model,
                messages=prompt.messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0
            completion_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
            total_tokens = usage.total_tokens if hasattr(usage, 'total_tokens') else (prompt_tokens + completion_tokens)
            
            # Calculate cost using Portkey
            cost_usd = portkey_client.calculate_cost(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Extract output
            output = response.choices[0].message.content
            
            # Check for refusals
            is_refusal = self._detect_refusal(output)
            
            return ReplayResult(
                prompt_id=prompt.id,
                model=model,
                provider=provider,
                success=True,
                output=output,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                is_refusal=is_refusal,
                schema_valid=True  # Will be validated separately if needed
            )
            
        except Exception as e:
            logger.error(f"Error replaying with {model}: {e}")
            
            return ReplayResult(
                prompt_id=prompt.id,
                model=model,
                provider=provider,
                success=False,
                error=str(e),
                is_refusal=False
            )
    
    def replay_batch(
        self,
        prompts: List[HistoricalPrompt],
        models: List[str],
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> List[ReplayResult]:
        """Replay multiple prompts across multiple models"""
        
        results = []
        total_calls = len(prompts) * len(models)
        
        logger.info(f"Starting replay: {len(prompts)} prompts x {len(models)} models = {total_calls} calls")
        
        for i, prompt in enumerate(prompts):
            for model in models:
                logger.info(f"Replaying prompt {i+1}/{len(prompts)} with {model}")
                
                result = self.replay_single(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                results.append(result)
        
        logger.info(f"Replay complete: {len(results)} results")
        return results
    
    def _detect_refusal(self, output: str) -> bool:
        """Detect if model refused to answer"""
        if not output:
            return False
        
        refusal_phrases = [
            "i cannot",
            "i can't",
            "i'm not able to",
            "i am not able to",
            "i don't have access",
            "i cannot provide",
            "i cannot assist",
            "i'm sorry, but i cannot",
            "against my programming",
            "violates my guidelines",
            "i'm not allowed to"
        ]
        
        output_lower = output.lower()
        
        for phrase in refusal_phrases:
            if phrase in output_lower:
                return True
        
        return False


# Singleton instance
replay_engine = ReplayEngine()
