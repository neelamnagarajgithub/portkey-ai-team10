"""
Scenario Classification
Automatically detects prompt type for scenario-aware validation
"""

import re
from typing import Dict, List


class ScenarioClassifier:
    """Classifies prompts into scenarios for validation optimization"""
    
    SCENARIOS = {
        "code_generation": {
            "keywords": [
                "write code", "implement", "function", "class", "method",
                "create a", "build a", "code for", "program", "script",
                "algorithm", "data structure"
            ],
            "patterns": [
                r"\bdef\s+\w+",
                r"\bclass\s+\w+",
                r"\bfunction\s+\w+",
                r"write.*function",
                r"implement.*function",
                r"create.*function"
            ]
        },
        "factual_qa": {
            "keywords": [
                "what is", "what are", "explain", "define", "who is",
                "when was", "where is", "how many", "tell me about",
                "describe"
            ],
            "patterns": [
                r"^(what|who|when|where|why|how)\s",
                r"explain.*about",
                r"tell me about"
            ]
        },
        "creative_writing": {
            "keywords": [
                "write a story", "write a poem", "create a story",
                "compose", "creative", "imagine", "describe a scene",
                "write dialogue"
            ],
            "patterns": [
                r"\bstory\b",
                r"\bpoem\b",
                r"\bcreative\b",
                r"write.*story",
                r"create.*narrative"
            ]
        },
        "translation": {
            "keywords": [
                "translate", "translation", "convert to", "in spanish",
                "in french", "in german", "language"
            ],
            "patterns": [
                r"translate.*to\s+\w+",
                r"convert.*to\s+\w+",
                r"in\s+(spanish|french|german|chinese|japanese)"
            ]
        },
        "summarization": {
            "keywords": [
                "summarize", "summary", "brief", "tldr", "key points",
                "main ideas", "overview"
            ],
            "patterns": [
                r"summarize.*text",
                r"give.*summary",
                r"tl;?dr"
            ]
        },
        "analysis": {
            "keywords": [
                "analyze", "analysis", "evaluate", "assess", "compare",
                "contrast", "pros and cons", "advantages", "disadvantages"
            ],
            "patterns": [
                r"analyze.*data",
                r"compare.*with",
                r"pros.*cons"
            ]
        }
    }
    
    def classify(self, prompt: str) -> str:
        """
        Classify a prompt into a scenario
        
        Args:
            prompt: User prompt text
            
        Returns:
            Scenario name (e.g., 'code_generation', 'factual_qa', 'general')
        """
        if not prompt or len(prompt.strip()) == 0:
            return "general"
        
        prompt_lower = prompt.lower()
        
        # Score each scenario
        scores = {}
        for scenario, rules in self.SCENARIOS.items():
            score = 0
            
            # Check keywords
            for keyword in rules["keywords"]:
                if keyword in prompt_lower:
                    score += 2
            
            # Check regex patterns
            for pattern in rules["patterns"]:
                if re.search(pattern, prompt_lower, re.IGNORECASE):
                    score += 3
            
            scores[scenario] = score
        
        # Return scenario with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return "general"
    
    def classify_batch(self, prompts: List[str]) -> List[str]:
        """Classify multiple prompts"""
        return [self.classify(p) for p in prompts]
    
    def get_scenario_info(self, scenario: str) -> Dict:
        """Get keywords and patterns for a scenario"""
        return self.SCENARIOS.get(scenario, {})


# Global instance
scenario_classifier = ScenarioClassifier()
