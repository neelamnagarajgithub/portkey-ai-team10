"""
Portkey Pricing Client
Fetches accurate pricing for 2000+ models from 40+ providers
API: https://api.portkey.ai/model-configs/pricing/{provider}/{model}
"""

import requests
from typing import Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class PortkeyPricingClient:
    """Client for Portkey Models API"""
    
    BASE_URL = "https://api.portkey.ai/model-configs/pricing"
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        
    def _normalize_model_name(self, provider: str, model: str) -> tuple[str, str]:
        """Normalize provider and model names for Portkey Pricing API"""
        
        # Clean provider name (remove @ prefixes and extract actual provider)
        clean_provider = provider.replace("@openai/", "").replace("@anthropic/", "").replace("@vertex/", "")
        
        # If provider still looks like a model name (e.g., "gpt-4o"), extract the real provider
        if any(x in clean_provider.lower() for x in ["gpt", "o1", "davinci", "turbo"]):
            clean_provider = "openai"
        elif any(x in clean_provider.lower() for x in ["claude", "anthropic"]):
            clean_provider = "anthropic"
        elif any(x in clean_provider.lower() for x in ["gemini", "llama", "vertex"]):
            clean_provider = "google"
    
        # Map internal providers to Portkey API providers
        provider_mapping = {
            "openai": "openai",
            "anthropic": "anthropic",
            "google": "vertex-ai",
            "vertex-ai": "vertex-ai",
        }
        
        # Map to API provider
        api_provider = provider_mapping.get(clean_provider.lower(), "openai")
        
        # Clean model name (remove prefixes like @openai/, @vertex/, etc.)
        clean_model = model.replace("@openai/", "").replace("@vertex/", "").replace("@anthropic/", "")
        
        # Special handling for Vertex models
        if api_provider == "vertex-ai":
            vertex_model_mapping = {
                "gemini-2.5-pro": "gemini-pro-002",
                "gemini-2.0-flash-exp": "gemini-flash-exp",
            }
            clean_model = vertex_model_mapping.get(clean_model, clean_model)
    
        logger.debug(f"Normalized: provider='{provider}' → '{api_provider}', model='{model}' → '{clean_model}'")
    
        return (api_provider, clean_model)
        
    @lru_cache(maxsize=1000)
    def get_pricing(self, provider: str, model: str) -> Optional[Dict]:
        """
        Fetch pricing for a specific model
        
        Returns dict with structure:
        {
            "pay_as_you_go": {
                "request_token": {"price": 0.00025},
                "response_token": {"price": 0.001},
                ...
            }
        }
        """
        # Normalize names for API
        api_provider, api_model = self._normalize_model_name(provider, model)
        cache_key = f"{api_provider}/{api_model}"
        
        # Check memory cache first
        if cache_key in self._cache:
            logger.debug(f"💾 Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        try:
            url = f"{self.BASE_URL}/{api_provider}/{api_model}"
            logger.debug(f"🌐 Fetching pricing from {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = data
                logger.info(f"✅ Fetched pricing for {cache_key}")
                return data
            elif response.status_code == 404:
                logger.warning(f"⚠️  Pricing not found for {cache_key} (404) - using fallback")
                return None
            else:
                logger.error(f"❌ Error fetching pricing for {cache_key}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout fetching pricing for {cache_key}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🔌 Request exception for {cache_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"💥 Unexpected error for {cache_key}: {e}")
            return None
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int = 0
    ) -> float:
        """Calculate cost in USD for a model call"""
        pricing = self.get_pricing(provider, model)
        
        if not pricing:
            logger.debug(f"📊 Using fallback pricing for {model}")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
        
        try:
            # Portkey API returns pay_as_you_go directly
            pay_as_you_go = pricing.get("pay_as_you_go", {})
            
            if not pay_as_you_go:
                logger.warning(f"⚠️  No pay_as_you_go pricing for {model}")
                return self._estimate_cost(model, prompt_tokens, completion_tokens)
            
            # Extract prices (dollars per 1,000 tokens)
            input_price_per_1k = pay_as_you_go.get("request_token", {}).get("price", 0)
            output_price_per_1k = pay_as_you_go.get("response_token", {}).get("price", 0)
            cache_price_per_1k = pay_as_you_go.get("cache_read_input_token", {}).get("price", 0)
            
            # Calculate cost
            cost_usd = (
                (prompt_tokens / 1000) * input_price_per_1k +
                (completion_tokens / 1000) * output_price_per_1k +
                (cache_read_tokens / 1000) * cache_price_per_1k
            )
            
            logger.debug(
                f"💰 {model}: "
                f"{prompt_tokens} input × ${input_price_per_1k:.4f}/1K + "
                f"{completion_tokens} output × ${output_price_per_1k:.4f}/1K = "
                f"${cost_usd:.8f}"
            )
            
            return cost_usd
            
        except Exception as e:
            logger.error(f"❌ Error calculating cost for {model}: {e}")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
    
    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Fallback pricing estimates ($/1M tokens)"""
        pricing_map = {
            # OpenAI models (updated Jan 2026)
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "o1-preview": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            
            # Anthropic models (updated Jan 2026)
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
            "claude-3-opus": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            
            # Google Gemini models
            "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            
            # Vertex AI - Llama models
            "meta.llama-3.2-90b": {"input": 0.27, "output": 0.27},
            "meta.llama-3.1-405b": {"input": 0.80, "output": 0.80},
            "llama-3.1-8b": {"input": 0.05, "output": 0.05},
        }
        
        model_lower = model.lower()
        
        # Find matching pricing (fuzzy match)
        for key, prices in pricing_map.items():
            if key in model_lower:
                input_cost = (prompt_tokens / 1_000_000) * prices["input"]
                output_cost = (completion_tokens / 1_000_000) * prices["output"]
                total_cost = input_cost + output_cost
                
                logger.debug(
                    f"📊 Fallback pricing for {model} (matched '{key}'): "
                    f"{prompt_tokens} input × ${prices['input']}/1M + "
                    f"{completion_tokens} output × ${prices['output']}/1M = "
                    f"${total_cost:.8f}"
                )
                return total_cost
        
        # Ultra fallback: $2/1M tokens average
        fallback_cost = ((prompt_tokens + completion_tokens) / 1_000_000) * 2.0
        logger.warning(
            f"⚠️  No pricing data for {model}, using default $2.00/1M: "
            f"${fallback_cost:.8f}"
        )
        
        return fallback_cost
    
    def get_model_info(self, provider: str, model: str) -> Dict:
        """Get full model configuration including pricing and capabilities"""
        pricing = self.get_pricing(provider, model)
        
        if not pricing:
            return {
                "provider": provider,
                "model": model,
                "pricing_available": False
            }
        
        pay_as_you_go = pricing.get("pay_as_you_go", {})
        
        return {
            "provider": provider,
            "model": model,
            "pricing_available": True,
            "pricing": pricing,
            "supports_cache": "cache_read_input_token" in pay_as_you_go,
            "input_price_per_1m": pay_as_you_go.get("request_token", {}).get("price", 0) * 1_000,
            "output_price_per_1m": pay_as_you_go.get("response_token", {}).get("price", 0) * 1_000,
            "currency": "USD"
        }
    
    def clear_cache(self):
        """Clear the pricing cache"""
        self._cache.clear()
        self.get_pricing.cache_clear()
        logger.info("🧹 Pricing cache cleared")


# Singleton instance
portkey_client = PortkeyPricingClient()