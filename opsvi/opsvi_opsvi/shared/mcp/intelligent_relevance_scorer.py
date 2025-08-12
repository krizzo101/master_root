#!/usr/bin/env python3
"""
Intelligent Relevance Scoring Agent

This specialized agent uses LLM intelligence to evaluate the relevance
of search results instead of basic keyword matching. It provides:

1. Semantic understanding of queries and content
2. Context-aware relevance assessment
3. Quality and authority evaluation
4. Intent analysis and domain knowledge
5. Detailed scoring with reasoning

This agent is embedded within the research workflow to provide
intelligent URL ranking for better research outcomes.
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add src to path if needed
if "src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class RelevanceEvaluation:
    """Result of intelligent relevance evaluation"""

    score: float  # 0.0 - 5.0 scale
    reasoning: str
    confidence: float  # 0.0 - 1.0
    key_factors: list[str]
    quality_indicators: list[str]


class IntelligentRelevanceScorer:
    """
    Specialized agent for intelligent relevance scoring using LLM analysis

    This agent evaluates search results using sophisticated prompts and
    semantic understanding rather than simple keyword matching.
    """

    def __init__(self, llm_client=None):
        """
        Initialize the relevance scoring agent

        Args:
            llm_client: Optional LLM client, will create default if not provided
        """
        self.llm_client = llm_client or self._create_default_llm_client()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_default_llm_client(self):
        """Create default LLM client for relevance scoring"""
        try:
            from openai import OpenAI

            return OpenAI()  # Uses environment variables for config
        except ImportError:
            self.logger.warning("OpenAI client not available, falling back to mock")
            return None

    def evaluate_relevance(
        self,
        query: str,
        url: str,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> RelevanceEvaluation:
        """
        Evaluate the relevance of a URL using intelligent LLM analysis

        Args:
            query: Original search query
            url: URL to evaluate
            title: Page/result title
            description: Page/result description
            context: Optional additional context about the research

        Returns:
            RelevanceEvaluation with score, reasoning, and analysis
        """

        # Create specialized prompt for relevance evaluation
        prompt = self._create_relevance_prompt(query, url, title, description, context)

        try:
            # Get LLM evaluation
            evaluation = self._get_llm_evaluation(prompt)

            # Parse and validate the evaluation
            return self._parse_evaluation_response(evaluation)

        except Exception as e:
            self.logger.error(f"Relevance evaluation failed: {e}")
            # Fallback to basic scoring if LLM fails
            return self._fallback_scoring(query, title, description)

    def _create_relevance_prompt(
        self,
        query: str,
        url: str,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Create specialized prompt for relevance evaluation"""

        context_info = ""
        if context:
            research_type = context.get("research_type", "general")
            domain = context.get("domain", "general")
            context_info = (
                f"\nResearch Context: {research_type} research in {domain} domain"
            )

        prompt = f"""You are a specialized relevance evaluation agent. Your task is to intelligently assess how relevant a search result is to a user's query using semantic understanding, not just keyword matching.

EVALUATION TASK:
Query: "{query}"
URL: {url}
Title: "{title}"
Description: "{description}"{context_info}

EVALUATION CRITERIA:
1. **Semantic Relevance**: Does the content semantically match what the user is looking for?
2. **Intent Analysis**: Does this result help fulfill the user's likely intent?
3. **Content Quality**: Is this likely to be a high-quality, authoritative source?
4. **Specificity**: How specifically does this address the query vs. being tangentially related?
5. **Usefulness**: How useful would this be for someone researching this topic?

SCORING SCALE:
- 5.0: Extremely relevant, exactly what the user needs
- 4.0: Highly relevant, very useful for the query
- 3.0: Moderately relevant, somewhat useful
- 2.0: Minimally relevant, tangentially related
- 1.0: Barely relevant, likely not useful
- 0.0: Not relevant, unrelated to query

DOMAIN KNOWLEDGE:
Use your knowledge of:
- Technical domains (programming, frameworks, tools)
- Academic and research contexts
- Documentation vs. tutorials vs. discussions
- Authority and credibility indicators
- Content freshness and currency

RESPONSE FORMAT:
Return a JSON object with:
{{
    "score": <float 0.0-5.0>,
    "reasoning": "<detailed explanation of why this score was assigned>",
    "confidence": <float 0.0-1.0>,
    "key_factors": ["<factor1>", "<factor2>", ...],
    "quality_indicators": ["<indicator1>", "<indicator2>", ...]
}}

EXAMPLE ANALYSIS:
Query: "python web frameworks"
Title: "Flask Quickstart Guide"
Analysis: Flask is a major Python web framework. This quickstart guide would be highly relevant for someone researching Python web frameworks, providing practical information about one of the most popular options. Score: 4.2

Now evaluate the given search result:"""

        return prompt

    def _get_llm_evaluation(self, prompt: str) -> str:
        """Get evaluation from LLM"""
        if not self.llm_client:
            # Mock response for testing
            return json.dumps(
                {
                    "score": 3.0,
                    "reasoning": "Mock evaluation - LLM client not available",
                    "confidence": 0.5,
                    "key_factors": ["mock evaluation"],
                    "quality_indicators": ["fallback response"],
                }
            )

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4.1-nano",  # Use fast, cost-effective model for evaluation
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized relevance evaluation agent. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"LLM evaluation request failed: {e}")
            raise

    def _parse_evaluation_response(self, response: str) -> RelevanceEvaluation:
        """Parse and validate LLM evaluation response"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")

            # Validate and create evaluation object
            score = float(data.get("score", 0.0))
            score = max(0.0, min(5.0, score))  # Clamp to valid range

            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range

            return RelevanceEvaluation(
                score=score,
                reasoning=data.get("reasoning", "No reasoning provided"),
                confidence=confidence,
                key_factors=data.get("key_factors", []),
                quality_indicators=data.get("quality_indicators", []),
            )

        except Exception as e:
            self.logger.error(f"Failed to parse evaluation response: {e}")
            # Return safe fallback
            return RelevanceEvaluation(
                score=2.0,
                reasoning=f"Parsing failed: {str(e)}",
                confidence=0.1,
                key_factors=["parsing_error"],
                quality_indicators=[],
            )

    def _fallback_scoring(
        self, query: str, title: str, description: str
    ) -> RelevanceEvaluation:
        """Fallback to basic scoring if LLM evaluation fails"""
        # Simple keyword-based fallback (the old method)
        score = 0.0
        query_lower = query.lower()

        if title and query_lower in title.lower():
            score += 2.0
        if description and query_lower in description.lower():
            score += 1.0

        # Convert to 0-5 scale
        score = min(5.0, score)

        return RelevanceEvaluation(
            score=score,
            reasoning="Fallback keyword-based scoring used due to LLM evaluation failure",
            confidence=0.3,
            key_factors=["keyword_matching"],
            quality_indicators=["fallback_method"],
        )

    async def batch_evaluate_urls(
        self,
        query: str,
        urls_data: list[dict[str, str]],
        context: dict[str, Any] | None = None,
    ) -> list[tuple[dict[str, str], RelevanceEvaluation]]:
        """
        Evaluate multiple URLs for relevance in batch

        Args:
            query: Search query
            urls_data: List of dicts with 'url', 'title', 'description' keys
            context: Optional research context

        Returns:
            List of (url_data, evaluation) tuples sorted by relevance score
        """
        evaluations = []

        for url_data in urls_data:
            evaluation = await self.evaluate_relevance(
                query=query,
                url=url_data.get("url", ""),
                title=url_data.get("title", ""),
                description=url_data.get("description", ""),
                context=context,
            )
            evaluations.append((url_data, evaluation))

        # Sort by relevance score (highest first)
        evaluations.sort(key=lambda x: x[1].score, reverse=True)

        return evaluations


# Convenience function for easy integration
async def intelligent_relevance_score(
    query: str,
    url: str,
    title: str,
    description: str,
    context: dict[str, Any] | None = None,
) -> float:
    """
    Convenience function to get intelligent relevance score

    Returns just the score (0.0-5.0) for simple integration
    """
    scorer = IntelligentRelevanceScorer()
    evaluation = await scorer.evaluate_relevance(
        query, url, title, description, context
    )
    return evaluation.score


# Export main classes and functions
__all__ = [
    "IntelligentRelevanceScorer",
    "RelevanceEvaluation",
    "intelligent_relevance_score",
]
