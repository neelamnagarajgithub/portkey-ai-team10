"""
Supabase Database using REST API
Bypasses PostgreSQL network issues
"""

import os
import requests
import logging
from typing import Optional, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DBResult(BaseModel):
    """Result from database lookup"""
    avg_score: float = Field(ge=0, le=100)
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    similar_count: int = Field(description="Number of similar prompts found")
    method: str = "historical_db"


class SupabaseDB:
    """
    Supabase database using REST API
    """
    
    def __init__(self):
        """Initialize Supabase REST API client"""
        self.url = os.getenv("SUPABASE_URL", "https://jzjxtztthwzkhczwbtsq.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "sb_publishable_wu7VJZeDC3f7N0V1892ycg_gG8Ex_R0")
        
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        self.table = "validation_results"
        logger.info(f"SupabaseDB initialized (REST API): {self.url}")
        logger.info(f"Table: {self.table}")
        
        # Verify credentials are set
        if not self.url or not self.key:
            logger.warning("⚠️ Supabase URL or KEY not set - database storage will fail!")
            logger.warning(f"   SUPABASE_URL: {'SET' if self.url else 'MISSING'}")
            logger.warning(f"   SUPABASE_KEY: {'SET' if self.key else 'MISSING'}")
        else:
            logger.info(f"✅ Supabase credentials configured")
            logger.debug(f"   API Key (first 10 chars): {self.key[:10]}..." if len(self.key) > 10 else "   API Key: [SHORT]")
    
    def store_validation(
        self,
        prompt_text: str,
        model: str,
        provider: str,
        scenario: str,
        output: str,
        score: float,
        method: str,
        confidence: str,
        procedure: str = "validation"
    ):
        """Store validation via REST API"""
        try:
            url = f"{self.url}/rest/v1/{self.table}"
            
            data = {
                "input": prompt_text,
                "provider": provider,
                "scenario": scenario,
                "model": model,
                "output": output,
                "validation_score": score,
                "validation_method": method,
                "confidence": confidence,
                "procedure": procedure
            }
            
            logger.info(f"📤 Storing validation to Supabase: model={model}, score={score:.1f}, method={method}")
            logger.debug(f"   URL: {url}")
            logger.debug(f"   Data keys: {list(data.keys())}")
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully stored validation for {model}: {score}/100 (method: {method})")
                return True
            else:
                logger.error(f"❌ Failed to store validation: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                logger.error(f"   URL: {url}")
                logger.error(f"   Model: {model}, Score: {score}, Method: {method}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error storing validation: {e}")
            logger.error(f"   URL: {url if 'url' in locals() else 'N/A'}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error storing validation: {e}", exc_info=True)
            return False
    
    def find_similar(
        self,
        prompt_text: str,
        model: str,
        scenario: Optional[str] = None,
        limit: int = 5
    ) -> Optional[DBResult]:
        """Find similar prompts via REST API"""
        try:
            url = f"{self.url}/rest/v1/{self.table}"
            
            # Try exact match first
            params = {
                "model": f"eq.{model}",
                "input": f"eq.{prompt_text}",
                "select": "validation_score,confidence",
                "limit": limit,
                "order": "created_at.desc"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                results = response.json()
                
                if results:
                    scores = [r['validation_score'] for r in results if r.get('validation_score')]
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        
                        return DBResult(
                            avg_score=avg_score,
                            confidence="HIGH",
                            similar_count=len(results)
                        )
            
            # Fall back to scenario matching
            if scenario:
                params = {
                    "model": f"eq.{model}",
                    "scenario": f"eq.{scenario}",
                    "select": "validation_score,confidence",
                    "limit": limit,
                    "order": "created_at.desc"
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results:
                        scores = [r['validation_score'] for r in results if r.get('validation_score')]
                        if scores:
                            avg_score = sum(scores) / len(scores)
                            
                            confidence = "MEDIUM" if len(results) >= 3 else "LOW"
                            
                            return DBResult(
                                avg_score=avg_score,
                                confidence=confidence,
                                similar_count=len(results)
                            )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find similar prompts: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            url = f"{self.url}/rest/v1/{self.table}"
            
            # Get all records with count
            headers = {**self.headers, "Prefer": "count=exact"}
            params = {"select": "validation_score,model,scenario"}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                content_range = response.headers.get("Content-Range", "")
                total = int(content_range.split("/")[1]) if "/" in content_range else 0
                
                results = response.json()
                
                scores = [r['validation_score'] for r in results if r.get('validation_score')]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                unique_models = len(set(r['model'] for r in results if r.get('model')))
                unique_scenarios = len(set(r['scenario'] for r in results if r.get('scenario')))
                
                return {
                    "total_validations": total,
                    "unique_models": unique_models,
                    "unique_scenarios": unique_scenarios,
                    "avg_score": avg_score
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def clear(self):
        """Clear all validation records"""
        try:
            url = f"{self.url}/rest/v1/{self.table}"
            
            # Delete all records
            params = {"procedure": "eq.test_validation"}
            
            response = requests.delete(url, headers=self.headers, params=params)
            
            if response.status_code in [200, 204]:
                logger.info("Cleared test validation results")
            else:
                logger.warning(f"Clear returned: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to clear: {e}")


# Singleton instance
historical_db = SupabaseDB()
