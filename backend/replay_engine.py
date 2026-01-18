"""
Core Replay Engine
Re-runs historical prompts across multiple models using Portkey Gateway
"""

import time
import logging
from typing import List, Dict
from portkey_ai import Portkey
from backend.schemas import HistoricalPrompt, ReplayResult
from backend.client.portkey_client import portkey_client
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
            "gpt-4o": "@openai/gpt-4o",
            "gpt-4o-mini": "@openai/gpt-4o-mini",
            "gpt-4": "@openai/gpt-4",
            "gpt-3.5-turbo": "@openai/gpt-3.5-turbo",
            "claude-3-5-sonnet-20250122": "@anthropic/claude-3-5-sonnet-20250122",
            "claude-3-5-haiku-20250122": "@anthropic/claude-3-5-haiku-20250122",
            "claude-3-opus-20240229": "@anthropic/claude-3-opus-20240229",
            "@vertex/gemini-2.5-pro": "@vertex/gemini-2.5-pro",
            "@vertex/meta.llama-3.2-90b-vision-instruct-maas": "@vertex/meta.llama-3.2-90b-vision-instruct-maas",
            "@vertex/llama3_1@llama-3.1-8b-instruct": "@vertex/llama3_1@llama-3.1-8b-instruct",
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
        max_tokens: int = 1000,
        use_validation: bool = True,
        validation_phase: str = "discovery"
    ) -> List[ReplayResult]:
        """
        Replay multiple prompts across multiple models via Portkey with automatic validation
        
        Args:
            prompts: List of prompts to replay
            models: Models to test
            temperature: Sampling temperature
            max_tokens: Max completion tokens
            use_validation: Enable hybrid validation (default: True)
            validation_phase: "discovery" or "production" (affects validation strategy)
        """
        # Import validator ONCE at the start
        hybrid_validator = None
        if use_validation:
            try:
                from backend.validator.hybrid_validator import hybrid_validator as validator
                hybrid_validator = validator
                logger.info("✅ Validation system loaded successfully")
            except ImportError as e:
                logger.error(f"❌ FAILED to import hybrid_validator: {e}")
                logger.error(f"   Make sure backend/validator/hybrid_validator.py exists")
                use_validation = False
        
        results = []
        total_calls = len(prompts) * len(models)
        
        logger.info(f"Starting replay via Portkey Model Catalog: {len(prompts)} prompts x {len(models)} models = {total_calls} calls")
        if use_validation:
            logger.info(f"✅ Validation ENABLED (phase: {validation_phase})")
        else:
            logger.warning(f"⚠️  Validation DISABLED")
        
        for i, prompt in enumerate(prompts):
            for model in models:
                logger.info(f"Replaying prompt {i+1}/{len(prompts)} with {model}")
                
                result = self.replay_single(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Validate output if enabled and successful
                if use_validation and hybrid_validator and result.success and result.output:
                    try:
                        logger.info(f"  🔍 Starting validation for {model}...")
                        
                        # Call validator (it's synchronous, not async)
                        validation = hybrid_validator.validate(
                            prompt=prompt,
                            output=result.output,
                            model=model,
                            phase=validation_phase
                        )
                        
                        # Add validation results
                        result.validation_score = validation.score
                        result.validation_method = validation.method
                        result.validation_confidence = validation.confidence
                        
                        logger.info(
                            f"  ✅ Validated: {validation.score:.1f}/100 "
                            f"({validation.method}, {validation.confidence})"
                        )
                        logger.info(f"  💾 Validation result stored in database")
                    except Exception as e:
                        logger.error(f"  ❌ Validation failed for {model}: {e}", exc_info=True)
                
                results.append(result)
                
                # Log result status
                if result.success:
                    validation_info = f", validation={result.validation_score:.1f}" if result.validation_score else ""
                    logger.info(f"✓ Success: {model} - {result.total_tokens} tokens, ${result.cost_usd:.6f}{validation_info}")
                else:
                    logger.error(f"✗ Failed: {model} - {result.error}")
        
        # Summary statistics
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        validated = sum(1 for r in results if r.validation_score is not None)
        total_cost = sum(r.cost_usd for r in results if r.success)
        
        logger.info(f"Replay complete: {successful} successful, {failed} failed, ${total_cost:.6f} total cost")
        logger.info(f"Validation: {validated}/{len(results)} results validated ({validated/len(results)*100:.1f}%)")
        
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