"""
Core Replay Engine
Re-runs historical prompts across multiple models using Portkey Gateway
"""

import time
import logging
from typing import List, Dict
from portkey_ai import Portkey
from backend.schemas import HistoricalPrompt, ReplayResult
from backend.portkey_client import portkey_client
import os

logger = logging.getLogger(__name__)


class ReplayEngine:
    """Replays historical LLM calls across different models via Portkey"""
    
    def __init__(self):
        # Portkey API key
        self.portkey_api_key = os.environ.get("PORTKEY_API_KEY", "TqVI5Ll6jQNk4hfqHEGCK0G2tfBL")
        
        if not self.portkey_api_key:
            logger.error("PORTKEY_API_KEY not set in environment variables")
            raise ValueError("PORTKEY_API_KEY is required. Set it in your .env file")
        
        logger.info(f"Portkey API key configured: {self.portkey_api_key[:8]}...")
        
        # Provider to model mapping
        self.provider_map = {
            "gpt-4o": "openai",
            "gpt-4o-mini": "openai",
            "gpt-4": "openai",
            "gpt-3.5-turbo": "openai",
            "claude-3-5-sonnet-20250122": "anthropic",
            "claude-3-5-haiku-20250122": "anthropic",
            "claude-3-opus-20240229": "anthropic",
            "gemini-2.0-flash-exp": "vertex-ai",
            "gemini-1.5-pro": "vertex-ai",
        }
        
        logger.info("ReplayEngine initialized successfully with Model Catalog")
    
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
            return "vertex-ai"
        
        # Default fallback
        logger.warning(f"Unknown provider for model {model}, defaulting to openai")
        return "openai"
    
    def replay_single(
        self,
        prompt: HistoricalPrompt,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> ReplayResult:
        """Replay a single prompt with a specific model via Portkey"""
        
        provider = self.get_provider(model)
        
        try:
            start_time = time.time()
            
            # Create Portkey client with provider header
            # This tells Portkey which provider's API key to use from Model Catalog
            portkey = Portkey(
                api_key=self.portkey_api_key,
                provider=provider  # Required: tells Portkey which provider to route to
            )
            
            # Call model - Portkey will use the provider API key configured in Model Catalog
            response = portkey.chat.completions.create(
                model=model,
                messages=prompt.messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token usage
            usage = response.usage
            prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            completion_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = getattr(usage, 'total_tokens', prompt_tokens + completion_tokens)
            
            # Calculate cost using Portkey Pricing API
            try:
                cost_usd = portkey_client.calculate_cost(
                    provider=provider,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )
            except Exception as cost_error:
                logger.warning(f"Could not calculate cost for {model}: {cost_error}")
                cost_usd = 0.0
            
            # Extract output
            output = response.choices[0].message.content
            
            # Check for refusals
            is_refusal = self._detect_refusal(output)
            
            logger.info(f"Successfully called {model} via Portkey ({provider})")
            
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
                schema_valid=True
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error replaying with {model} via Portkey: {error_msg}", exc_info=True)
            
            # Provide helpful error messages for Model Catalog
            if "x-portkey-provider" in error_msg or "x-portkey-config" in error_msg:
                error_msg += f"\n\n⚠️  Provider configuration required. Make sure {provider.upper()} API key is set in Portkey Model Catalog at https://app.portkey.ai/settings/api-keys"
            elif "401" in error_msg or "authentication" in error_msg.lower():
                error_msg += f"\n\n⚠️  Authentication failed. Add your {provider.upper()} API key at https://app.portkey.ai/settings/api-keys"
            elif "not found" in error_msg.lower() or "404" in error_msg:
                error_msg += f"\n\n⚠️  Model '{model}' not found. Check model name is correct."
            
            return ReplayResult(
                prompt_id=prompt.id,
                model=model,
                provider=provider,
                success=False,
                error=error_msg,
                is_refusal=False
            )
    
    def replay_batch(
        self,
        prompts: List[HistoricalPrompt],
        models: List[str],
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> List[ReplayResult]:
        """Replay multiple prompts across multiple models via Portkey"""
        
        results = []
        total_calls = len(prompts) * len(models)
        
        logger.info(f"Starting replay via Portkey Model Catalog: {len(prompts)} prompts x {len(models)} models = {total_calls} calls")
        
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
                
                # Log result status
                if result.success:
                    logger.info(f"✓ Success: {model} - {result.total_tokens} tokens, ${result.cost_usd:.6f}")
                else:
                    logger.error(f"✗ Failed: {model} - {result.error}")
        
        # Summary statistics
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_cost = sum(r.cost_usd for r in results if r.success)
        
        logger.info(f"Replay complete: {successful} successful, {failed} failed, ${total_cost:.6f} total cost")
        
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
            "i'm not allowed to",
            "i must decline",
            "i won't be able to",
            "i'm unable to"
        ]
        
        output_lower = output.lower()
        check_text = output_lower[:200]
        
        for phrase in refusal_phrases:
            if phrase in check_text:
                return True
        
        return False


# Singleton instance
replay_engine = ReplayEngine()