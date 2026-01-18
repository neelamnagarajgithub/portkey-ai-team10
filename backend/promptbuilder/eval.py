"""
Prompt Templates for LLM Judge Evaluation
Separated for easy modification and testing
"""

class EvalPromptBuilder:
    """Builds evaluation prompts for LLM judges"""
    
    # Judge model configurations (Open/Closed Principle - extend by adding tiers)
    JUDGE_MODELS = {
        "tier_1": {
            "model": "claude-3-5-sonnet-20250122",
            "provider": "anthropic",
            "cost_tier": "high",
            "quality_tier": "highest"
        },
        "tier_2": {
            "model": "gpt-4o",
            "provider": "openai",
            "cost_tier": "medium",
            "quality_tier": "high"
        },
        "tier_3": {
            "model": "gpt-4o-mini", 
            "provider": "openai",
            "cost_tier": "low",
            "quality_tier": "medium"
        }
    }
    
    EVALUATION_PROMPT = """You are an expert evaluator assessing the quality of an LLM's response.

Original User Query:
{prompt}

Model's Response:
{output}

Model Being Evaluated: {model_name}

Rate this response on the following criteria (0-100 for each):
1. **Correctness** - Is the information factually accurate?
2. **Helpfulness** - Does it fully address the user's query?
3. **Instruction Following** - Does it follow the prompt's requirements?

Also identify:
- **Strengths** - What did the model do well?
- **Weaknesses** - What could be improved?

Return your evaluation in JSON format:
{{
    "score": <overall score 0-100>,
    "correctness": <0-100>,
    "helpfulness": <0-100>,
    "instruction_following": <0-100>,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "reasoning": "Brief explanation of overall score"
}}

Be objective, precise, and constructive."""

    COMPARISON_PROMPT = """You are an expert evaluator comparing two LLM responses to the same prompt.

Original User Query:
{prompt}

Response A ({model_a}):
{output_a}

Response B ({model_b}):
{output_b}

Determine which response is better and by how much.

Consider:
- Correctness and accuracy
- Completeness and helpfulness
- Clarity and coherence
- Following instructions

Return your comparison in JSON format:
{{
    "winner": "<model_a or model_b>",
    "confidence": "<HIGH, MEDIUM, or LOW>",
    "margin": <score difference 0-100>,
    "reasoning": "Explanation of why winner is better"
}}

Be objective and fair."""

    @classmethod
    def get_judge_config(cls, tier: str) -> dict:
        """
        Get judge model configuration for a tier
        
        Args:
            tier: Model tier (tier_1, tier_2, tier_3)
            
        Returns:
            Dict with model, provider, and metadata
        """
        if tier not in cls.JUDGE_MODELS:
            raise ValueError(f"Unknown tier: {tier}. Available: {list(cls.JUDGE_MODELS.keys())}")
        return cls.JUDGE_MODELS[tier]
    
    @classmethod
    def format_evaluation_prompt(cls, prompt: str, output: str, model_name: str) -> str:
        """Format the evaluation prompt with actual content"""
        return cls.EVALUATION_PROMPT.format(
            prompt=prompt,
            output=output,
            model_name=model_name
        )
    
    @classmethod
    def format_comparison_prompt(cls, prompt: str, model_a: str, output_a: str, 
                                 model_b: str, output_b: str) -> str:
        """Format the comparison prompt with actual content"""
        return cls.COMPARISON_PROMPT.format(
            prompt=prompt,
            model_a=model_a,
            output_a=output_a,
            model_b=model_b,
            output_b=output_b
        )