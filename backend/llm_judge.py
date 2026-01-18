"""
LLM-as-a-Judge Evaluator
Clean architecture following SOLID principles with dependency injection
"""
import json
import logging
import os
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from portkey_ai import Portkey

from backend.schemas import HistoricalPrompt
from backend.judge.schema import JudgeScore, ComparisonResult
from backend.client.portkey_client import portkey_client
from backend.promptbuilder.eval import EvalPromptBuilder

logger = logging.getLogger(__name__)



class ILLMClient(ABC):
    """Abstract interface for LLM clients (DIP - depend on abstractions)"""
    
    @abstractmethod
    def create_completion(self, model: str, messages: List[Dict], 
                         temperature: float, max_tokens: int) -> Dict:
        """Create a chat completion"""
        pass


class IJudgeModelSelector(ABC):
    """Abstract interface for selecting judge models"""
    
    @abstractmethod
    def select_model(self, tier: Optional[str] = None, 
                    models_being_tested: Optional[List[str]] = None) -> Dict[str, str]:
        """Select appropriate judge model configuration"""
        pass



class PortkeyLLMClient(ILLMClient):
    """Portkey implementation of LLM client (SRP - handles only API calls)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info(f"PortkeyLLMClient initialized with API key: {api_key[:8]}...")
    
    async def create_completion(self, model: str, messages: List[Dict], 
                         temperature: float = 0.0, max_tokens: int = 500,
                         provider: str = "openai") -> Dict:
        """
        Create completion via Portkey
        
        Returns:
            Dict with 'content', 'usage', and 'response' keys
        """
        portkey = Portkey(
            api_key=self.api_key,
            provider=provider
        )
        
        response = portkey.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'usage': response.usage,
            'response': response
        }


class JudgeModelSelector(IJudgeModelSelector):
    """Selects appropriate judge model (SRP - model selection logic only)"""
    
    def __init__(self, default_tier: str = "tier_2"):
        self.default_tier = default_tier
        self.prompt_builder = EvalPromptBuilder
    
    def select_model(self, tier: Optional[str] = None, 
                    models_being_tested: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Select appropriate judge model configuration
        
        Args:
            tier: Override default tier
            models_being_tested: Ensure judge is stronger than these
        
        Returns:
            Dict with 'model', 'provider', and metadata
        """
        tier = tier or self.default_tier
        judge_config = self.prompt_builder.get_judge_config(tier)
        
        # Upgrade to stronger judge if testing powerful models
        if models_being_tested:
            if any(m in ["claude-3-opus", "o1", "o1-preview", "gemini-2.5-pro"] 
                   for m in models_being_tested):
                judge_config = self.prompt_builder.get_judge_config("tier_1")
        
        return judge_config


class CostTracker:
    """Tracks costs for judge calls (SRP - cost tracking only)"""
    
    def __init__(self):
        self.call_count = 0
        self.total_cost = 0.0
    
    def record_call(self, provider: str, model: str, 
                   prompt_tokens: int, completion_tokens: int) -> float:
        """
        Record a judge call and calculate cost
        
        Returns:
            Cost in USD
        """
        try:
            cost = portkey_client.calculate_cost(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            self.total_cost += cost
            self.call_count += 1
            logger.debug(f"Judge call #{self.call_count}: ${cost:.6f}")
            return cost
        except Exception as e:
            logger.warning(f"Could not calculate cost: {e}")
            return 0.0
    
    def get_stats(self) -> Dict:
        """Get cost statistics"""
        return {
            "total_calls": self.call_count,
            "total_cost": self.total_cost,
            "avg_cost_per_call": self.total_cost / self.call_count if self.call_count > 0 else 0.0
        }




class LLMJudge:
    """
    LLM-as-a-Judge evaluator using dependency injection
    
    Follows SOLID principles:
    - S: Each component has single responsibility
    - O: Extensible via interfaces (add new LLM clients, selectors)
    - L: Interface implementations are substitutable
    - I: Small, focused interfaces (ILLMClient, IJudgeModelSelector)
    - D: Depends on abstractions (interfaces), not concrete implementations
    """
    
    def __init__(
        self, 
        llm_client: Optional[ILLMClient] = None,
        model_selector: Optional[IJudgeModelSelector] = None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        Initialize with dependency injection
        
        Args:
            llm_client: LLM client implementation (default: PortkeyLLMClient)
            model_selector: Model selector (default: JudgeModelSelector)
            cost_tracker: Cost tracker (default: CostTracker)
        """
        # Dependency Injection with sensible defaults
        self.llm_client = llm_client or self._create_default_client()
        self.model_selector = model_selector or JudgeModelSelector()
        self.cost_tracker = cost_tracker or CostTracker()
        self.prompt_builder = EvalPromptBuilder
    
    def _create_default_client(self) -> ILLMClient:
        """Factory method for default client"""
        api_key = "TqVI5Ll6jQNk4hfqHEGCK0G2tfBL"
        if not api_key:
            raise ValueError("PORTKEY_API_KEY not set in environment")
        return PortkeyLLMClient(api_key)
    
    async def evaluate_single(
        self,
        prompt: HistoricalPrompt,
        output: str,
        model_name: str,
        judge_config: Optional[Dict[str, str]] = None
    ) -> JudgeScore:
        """
        Evaluate a single model output
        
        Args:
            prompt: Original prompt
            output: Model's response
            model_name: Name of model being evaluated
            judge_config: Override default judge config
        
        Returns:
            JudgeScore with detailed evaluation
        """
        if not judge_config:
            judge_config = self.model_selector.select_model()
        
        judge_model = judge_config["model"]
        judge_provider = judge_config["provider"]
        
        try:
            # Format prompt using builder
            prompt_text = self._format_messages(prompt.messages)
            eval_prompt = self.prompt_builder.format_evaluation_prompt(
                prompt=prompt_text,
                output=output,
                model_name=model_name
            )
            
            messages = [{"role": "user", "content": eval_prompt}]
            
            # Call LLM via injected client
            result = await self.llm_client.create_completion(
                model=judge_model,
                messages=messages,
                temperature=0.0,
                max_tokens=500,
                provider=judge_provider
            )
            
            # Track cost
            usage = result['usage']
            self.cost_tracker.record_call(
                provider=judge_provider,
                model=judge_model,
                prompt_tokens=getattr(usage, 'prompt_tokens', 0),
                completion_tokens=getattr(usage, 'completion_tokens', 0)
            )
            
            # Parse response
            score_data = json.loads(result['content'])
            return JudgeScore(**score_data)
            
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}", exc_info=True)
            return self._create_fallback_score(str(e))
    
    async def compare_outputs(
        self,
        prompt: HistoricalPrompt,
        outputs: Dict[str, str],
        judge_config: Optional[Dict[str, str]] = None
    ) -> List[ComparisonResult]:
        """
        Pairwise comparison of model outputs
        
        Args:
            prompt: Original prompt
            outputs: Dict of {model_name: output}
            judge_config: Override default judge
        
        Returns:
            List of pairwise comparisons
        """
        if not judge_config:
            judge_config = self.model_selector.select_model(
                models_being_tested=list(outputs.keys())
            )
        
        judge_model = judge_config["model"]
        judge_provider = judge_config["provider"]
        
        results = []
        models = list(outputs.keys())
        
        # All pairs
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                model_a, model_b = models[i], models[j]
                
                try:
                    prompt_text = self._format_messages(prompt.messages)
                    comparison_prompt = self.prompt_builder.format_comparison_prompt(
                        prompt=prompt_text,
                        model_a=model_a,
                        output_a=outputs[model_a],
                        model_b=model_b,
                        output_b=outputs[model_b]
                    )
                    
                    messages = [{"role": "user", "content": comparison_prompt}]
                    
                    result = await self.llm_client.create_completion(
                        model=judge_model,
                        messages=messages,
                        temperature=0.0,
                        max_tokens=300,
                        provider=judge_provider
                    )
                    
                    comparison_data = json.loads(result['content'])
                    
                    # Normalize winner name
                    winner = model_a if comparison_data["winner"].lower() == "model_a" else model_b
                    loser = model_b if winner == model_a else model_a
                    
                    results.append(ComparisonResult(
                        winner=winner,
                        loser=loser,
                        confidence=comparison_data["confidence"],
                        margin=comparison_data["margin"],
                        reasoning=comparison_data["reasoning"]
                    ))
                    
                except Exception as e:
                    logger.error(f"Comparison failed for {model_a} vs {model_b}: {e}")
        
        return results
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages for display"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            formatted.append(f"[{role}]: {content}")
        return "\n".join(formatted)
    
    def _create_fallback_score(self, error_msg: str) -> JudgeScore:
        """Create neutral score on error"""
        return JudgeScore(
            score=50,
            correctness=50,
            helpfulness=50,
            instruction_following=50,
            reasoning=f"Evaluation failed: {error_msg}",
            strengths=[],
            weaknesses=["Evaluation error"]
        )
    
    def get_stats(self) -> Dict:
        """Get judge usage statistics"""
        return self.cost_tracker.get_stats()



llm_judge = LLMJudge()
