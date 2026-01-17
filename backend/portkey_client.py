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
                    "request_token": {"price": 0.0000025},  # dollars per token
                    "response_token": {"price": 0.00001},
                    "cache_read_input_token": {"price": 0.00000125},
                    ...
                },
                "currency": "USD"
            }
        }
        """
        cache_key = f"{provider}/{model}"
        
        # Check memory cache first
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        try:
            url = f"{self.BASE_URL}/{provider}/{model}"
            logger.debug(f"Fetching pricing from {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = data
                logger.info(f"Fetched pricing for {cache_key}")
                return data
            elif response.status_code == 404:
                logger.warning(f"Pricing not found for {cache_key} (404)")
                return None
            else:
                logger.error(f"Error fetching pricing for {cache_key}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching pricing for {cache_key}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception fetching pricing for {cache_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching pricing for {cache_key}: {e}")
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
        
        Note: Portkey prices are in dollars per token (e.g., 0.0000025 = $2.50 per 1M tokens)
        """
        pricing = self.get_pricing(provider, model)
        
        if not pricing:
            logger.warning(f"No pricing data available for {provider}/{model}, using fallback estimates")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
        
        try:
            pay_as_you_go = pricing.get("pricing_config", {}).get("pay_as_you_go", {})
            
            if not pay_as_you_go:
                logger.warning(f"No pay_as_you_go pricing for {provider}/{model}")
                return self._estimate_cost(model, prompt_tokens, completion_tokens)
            
            # Extract prices (in dollars per token)
            input_price = pay_as_you_go.get("request_token", {}).get("price", 0)
            output_price = pay_as_you_go.get("response_token", {}).get("price", 0)
            cache_price = pay_as_you_go.get("cache_read_input_token", {}).get("price", 0)
            
            # Calculate total cost in USD
            cost_usd = (
                (prompt_tokens * input_price) +
                (completion_tokens * output_price) +
                (cache_read_tokens * cache_price)
            )
            
            logger.debug(
                f"Cost calculation for {model}: "
                f"{prompt_tokens} input @ ${input_price} + "
                f"{completion_tokens} output @ ${output_price} = "
                f"${cost_usd:.6f}"
            )
            
            return cost_usd
            
        except KeyError as e:
            logger.error(f"Missing key in pricing data for {provider}/{model}: {e}")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
        except Exception as e:
            logger.error(f"Error calculating cost for {provider}/{model}: {e}")
            return self._estimate_cost(model, prompt_tokens, completion_tokens)
    
    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Fallback pricing estimates when Portkey data unavailable
        Based on common model pricing as of January 2025
        Prices in $/1M tokens
        """
        pricing_map = {
            # OpenAI models
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            
            # Anthropic models
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
            "claude-3-opus": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            
            # Google models
            "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        }
        
        model_lower = model.lower()
        
        # Find matching pricing (fuzzy match)
        for key, prices in pricing_map.items():
            if key in model_lower:
                input_cost = (prompt_tokens / 1_000_000) * prices["input"]
                output_cost = (completion_tokens / 1_000_000) * prices["output"]
                total_cost = input_cost + output_cost
                
                logger.debug(
                    f"Using estimated pricing for {model} (matched '{key}'): "
                    f"${total_cost:.6f}"
                )
                
                return total_cost
        
        # Ultra fallback: assume moderate pricing ($2/1M tokens average)
        fallback_cost = ((prompt_tokens + completion_tokens) / 1_000_000) * 2.0
        logger.warning(
            f"No pricing estimate found for {model}, using default rate: "
            f"${fallback_cost:.6f}"
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
        
        pay_as_you_go = pricing.get("pricing_config", {}).get("pay_as_you_go", {})
        
        return {
            "provider": provider,
            "model": model,
            "pricing_available": True,
            "pricing": pricing,
            "supports_cache": "cache_read_input_token" in pay_as_you_go,
            "input_price_per_1m": pay_as_you_go.get("request_token", {}).get("price", 0) * 1_000_000,
            "output_price_per_1m": pay_as_you_go.get("response_token", {}).get("price", 0) * 1_000_000,
            "currency": pricing.get("pricing_config", {}).get("currency", "USD")
        }
    
    def clear_cache(self):
        """Clear the pricing cache (useful for testing or forcing refresh)"""
        self._cache.clear()
        self.get_pricing.cache_clear()
        logger.info("Pricing cache cleared")


# Singleton instance
portkey_client = PortkeyPricingClient()