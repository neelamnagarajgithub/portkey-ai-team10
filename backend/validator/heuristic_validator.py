"""
Heuristic Validators
Fast, rule-based quality checks without LLM calls
"""

import logging
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HeuristicScore(BaseModel):
    """Result from heuristic validation"""
    score: float = Field(ge=0, le=100)
    confidence: str = Field(description="HIGH, MEDIUM, or LOW")
    reasoning: str
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)


class HeuristicValidator:
    """Fast rule-based validation without LLM calls"""
    
    # Common refusal patterns
    REFUSAL_PATTERNS = [
        r"i cannot",
        r"i can't",
        r"i'm not able to",
        r"i am not able to",
        r"i don't have access",
        r"i cannot provide",
        r"i cannot assist",
        r"i'm sorry, but i cannot",
        r"against my programming",
        r"violates my guidelines",
        r"i'm not allowed to",
        r"as an ai",
        r"as a language model"
    ]
    
    # Error indicators
    ERROR_PATTERNS = [
        r"error:",
        r"exception:",
        r"failed to",
        r"could not",
        r"unable to",
        r"traceback",
        r"stack trace"
    ]
    
    def validate(
        self, 
        output: str, 
        expected_schema: Optional[dict] = None,
        min_length: int = 10,
        expected_language: str = "en"
    ) -> HeuristicScore:
        """
        Run all heuristic checks on output
        
        Args:
            output: Model output to validate
            expected_schema: Optional JSON schema for structured outputs
            min_length: Minimum acceptable output length
            expected_language: Expected language code
        
        Returns:
            HeuristicScore with overall assessment
        """
        score = 100
        confidence = "HIGH"
        checks_passed = []
        checks_failed = []
        
        if not output or len(output.strip()) == 0:
            return HeuristicScore(
                score=0,
                confidence="HIGH",
                reasoning="Empty output",
                checks_failed=["non_empty"]
            )
        
        # Check 1: Not a refusal
        if self._is_refusal(output):
            score = 0
            confidence = "HIGH"
            checks_failed.append("refusal_check")
            return HeuristicScore(
                score=score,
                confidence=confidence,
                reasoning="Model refused to answer",
                checks_failed=checks_failed
            )
        else:
            checks_passed.append("refusal_check")
        
        # Check 2: Sufficient length
        if len(output) < min_length:
            score -= 40
            checks_failed.append("length_check")
        else:
            checks_passed.append("length_check")
        
        # Check 3: No error messages
        if self._contains_errors(output):
            score -= 30
            checks_failed.append("error_check")
        else:
            checks_passed.append("error_check")
        
        # Check 4: Schema validation (if applicable)
        if expected_schema:
            if self._validate_schema(output, expected_schema):
                score += 10  # Bonus
                checks_passed.append("schema_check")
            else:
                score -= 20
                checks_failed.append("schema_check")
        
        # Check 5: Language detection
        detected_lang = self._detect_language(output)
        if detected_lang != expected_language:
            score -= 30
            checks_failed.append("language_check")
        else:
            checks_passed.append("language_check")
        
        # Check 6: Formatting quality
        formatting_score = self._check_formatting(output)
        score += (formatting_score - 50) * 0.2  # Small influence
        if formatting_score > 60:
            checks_passed.append("formatting_check")
        else:
            checks_failed.append("formatting_check")
        
        # Determine confidence
        if score < 20 or score > 85:
            confidence = "HIGH"
        elif 30 <= score <= 75:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # Clamp score
        score = max(0, min(100, score))
        
        reasoning = self._generate_reasoning(checks_passed, checks_failed, score)
        
        return HeuristicScore(
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            checks_passed=checks_passed,
            checks_failed=checks_failed
        )
    
    def _is_refusal(self, output: str) -> bool:
        """Check if output is a refusal"""
        output_lower = output.lower()
        for pattern in self.REFUSAL_PATTERNS:
            if re.search(pattern, output_lower):
                return True
        return False
    
    def _contains_errors(self, output: str) -> bool:
        """Check if output contains error messages"""
        output_lower = output.lower()
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, output_lower):
                return True
        return False
    
    def _validate_schema(self, output: str, schema: dict) -> bool:
        """Validate JSON structure against schema"""
        try:
            data = json.loads(output)
            # Simple schema validation (can be enhanced)
            for key in schema.get("required", []):
                if key not in data:
                    return False
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection
        Returns: ISO language code
        """
        # Very basic detection - in production use langdetect or similar
        text_lower = text.lower()
        
        # Check for common non-English patterns
        if re.search(r'[\u4e00-\u9fff]', text):  # Chinese
            return "zh"
        elif re.search(r'[\u0600-\u06ff]', text):  # Arabic
            return "ar"
        elif re.search(r'[\u0400-\u04ff]', text):  # Cyrillic/Russian
            return "ru"
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):  # Japanese
            return "ja"
        
        # Default to English
        return "en"
    
    def _check_formatting(self, output: str) -> float:
        """
        Check formatting quality (0-100)
        Considers: capitalization, punctuation, paragraphs
        """
        score = 50  # Baseline
        
        # Has proper capitalization
        if output[0].isupper():
            score += 10
        
        # Ends with punctuation
        if output.strip()[-1] in ".!?":
            score += 10
        
        # Has paragraphs (multiple lines)
        if "\n" in output:
            score += 10
        
        # Not all caps
        if not output.isupper():
            score += 10
        
        # Has proper sentences
        sentence_count = len(re.findall(r'[.!?]+\s', output))
        if sentence_count > 0:
            score += min(10, sentence_count * 2)
        
        return min(100, score)
    
    def _generate_reasoning(
        self, 
        passed: List[str], 
        failed: List[str],
        score: float
    ) -> str:
        """Generate human-readable reasoning"""
        if score == 0:
            return "Output failed critical checks (refusal or empty)"
        
        if not failed:
            return f"All heuristic checks passed ({len(passed)} checks)"
        
        if not passed:
            return f"All checks failed ({len(failed)} failures)"
        
        return f"Passed {len(passed)} checks, failed {len(failed)} checks"


# Singleton instance
heuristic_validator = HeuristicValidator()
