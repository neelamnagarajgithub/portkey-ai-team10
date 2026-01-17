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
        
    @lru_cache(maxsize=1000)
    def get_pricing(self, provider: str, model: str) -> Optional[Dict]:
        """
        Fetch pricing for a specific model
        
        Returns dict with structure:
        {
            "pricing_config": {
                "pay_as_you_go": {
                    "request_token": {"price": 0.00025},  # cents per token
                    "response_token": {"price": 0.001},
                    "cache_read_input_token": {"price": 0.000125},
                    ...
                },
                "currency": "USD"
            }
        }
        """
        cache_key = f"{provider}/{model}"
        
        # Check memory cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            url = f"{self.BASE_URL}/{provider}/{model}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = data
                logger.info(f"Fetched pricing for {cache_key}")
                return data
            elif response.status_code == 404:
                logger.warning(f"Pricing not found for {cache_key}")
                return None
            else:
                logger.error(f"Error fetching pricing for {cache_key}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching pricing for {cache_key}: {e}")
            return None
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int = 0
    ) -> float:
        """
        Calculate cost in USD for a model call
        
        Note: Portkey prices are in CENTS per token, we convert to dollars
        """
        pricing = self.get_pricing(provider, model)
        
        if not pricing:
            # Fallback to estimated pricing if Portkey doesn't have it
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
        
        try:
            pay_as_you_go = pricing.get("pricing_config", {}).get("pay_as_you_go", {})
            
            # Extract prices (in cents per token)
            input_price = pay_as_you_go.get("request_token", {}).get("price", 0)
            output_price = pay_as_you_go.get("response_token", {}).get("price", 0)
            cache_price = pay_as_you_go.get("cache_read_input_token", {}).get("price", 0)
            
            # Calculate total cost
            cost_cents = (
                (prompt_tokens * input_price) +
                (completion_tokens * output_price) +
                (cache_read_tokens * cache_price)
            )
            
            # Convert cents to dollars
            cost_usd = cost_cents / 100
            
            return cost_usd
            
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
    
    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Fallback pricing estimates when Portkey data unavailable
        Based on common model pricing as of Jan 2026
        """
        # Rough estimates in $/1M tokens
        pricing_map = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
            "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        }
        
        # Find matching pricing
        for key, prices in pricing_map.items():
            if key in model.lower():
                input_cost = (prompt_tokens / 1_000_000) * prices["input"]
                output_cost = (completion_tokens / 1_000_000) * prices["output"]
                return input_cost + output_cost
        
        # Ultra fallback: assume moderate pricing
        logger.warning(f"No pricing found for {model}, using default estimate")
        return ((prompt_tokens + completion_tokens) / 1_000_000) * 2.0
    
    def get_model_info(self, provider: str, model: str) -> Dict:
        """Get full model configuration (future enhancement)"""
        pricing = self.get_pricing(provider, model)
        if not pricing:
            return {}
        
        return {
            "provider": provider,
            "model": model,
            "pricing": pricing,
            "supports_cache": "cache_read_input_token" in str(pricing)
        }


# Singleton instance
portkey_client = PortkeyPricingClient()
