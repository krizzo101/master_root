"""
SynthesisAgent
==============

Phase-3 component that generates a *single*, coherent answer from multiple
Firecrawl pages while assigning a lightweight confidence / quality score.

Patterns extracted from reference code
--------------------------------------
1. Deduplication & ranking (see `.reference/.../synthesis_agent.py`)
2. Token-based relevance scoring (simplified Stage-6 in `research_workflow.py`)
3. LLM-powered synthesis with explicit, structured prompt and best-effort
   validation (953-openai-api-standards – JSON output, defensive parsing)

The implementation purposefully keeps the public surface minimal – one
entry-point `synthesise`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import time
from collections import Counter
from typing import Dict, List, Sequence, Tuple

import openai

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

from capabilities.tools.firecrawl_tool import FirecrawlResult

# --------------------------------------------------------------------------- #
# Utility helpers                                                             #
# --------------------------------------------------------------------------- #


_STOP_WORDS = {
    "the",
    "is",
    "of",
    "a",
    "an",
    "and",
    "in",
    "to",
    "for",
    "with",
    "on",
    "by",
    "as",
}


def _tokenise(text: str) -> List[str]:
    """Lower-case + alnum tokenisation with stop-word removal."""
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [tok for tok in tokens if tok not in _STOP_WORDS]


def _relevance_score(text: str, question_tokens: Counter) -> float:
    """Simple tf-idf-inspired relevance proxy used for page ranking."""
    tokens = Counter(_tokenise(text))
    overlap = sum(min(tokens[t], question_tokens[t]) for t in tokens)
    if not overlap:
        return 0.0
    # Normalise by question length (cosine-ish).
    return overlap / math.sqrt(sum(tokens.values()) * sum(question_tokens.values()))


# --------------------------------------------------------------------------- #
# Main synthesis agent                                                        #
# --------------------------------------------------------------------------- #


class SynthesisAgent:  # pylint: disable=too-few-public-methods
    """Aggregates multiple pages into a single answer with confidence score."""

    _LLM_TIMEOUT_SEC = 60.0
    _MAX_PAGES_FOR_PROMPT = 5

    def __init__(
        self,
        llm: OpenAIResponsesInterface,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._llm = llm
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    # --------------------------------------------------------------------- #
    # Public API                                                            #
    # --------------------------------------------------------------------- #

    def synthesise(
        self,
        question: str,
        pages: Sequence[FirecrawlResult],
    ) -> Dict[str, str]:
        """
        Return a JSON dict: {"answer": str, "confidence": str, "sources": list[str]}.

        The coroutine *never raises* on LLM issues – callers can treat failures
        as low-confidence answers.
        """
        if not pages:
            return {"answer": "", "confidence": "0.0", "sources": []}

        ranked = self._rank_and_deduplicate(pages, question)
        top_pages = ranked[: self._MAX_PAGES_FOR_PROMPT]

        prompt = self._build_prompt(question, top_pages)

        try:
            # Use Chat Completions API with Structured Outputs for reliable parsing
            import concurrent.futures
            import openai

            # Simple approach: always use asyncio.run in a new thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    asyncio.wait_for(
                        openai.AsyncOpenAI().chat.completions.create(
                            model="gpt-4.1-mini",  # Approved model for agent execution
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a senior research assistant.",
                                },
                                {"role": "user", "content": prompt},
                            ],
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "synthesis_response",
                                    "strict": True,
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "answer": {
                                                "type": "string",
                                                "description": "The synthesized answer based on the provided sources",
                                            }
                                        },
                                        "required": ["answer"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                        ),
                        timeout=self._LLM_TIMEOUT_SEC,
                    ),
                )
                response = future.result()

            # Handle structured response with proper error checking
            if response.choices[0].message.refusal:
                self._logger.warning(
                    "LLM refused to synthesize: %s", response.choices[0].message.refusal
                )
                answer_text = ""
            else:
                # Parse the structured response
                try:
                    import json

                    content = response.choices[0].message.content
                    if content:
                        parsed = json.loads(content)
                        answer_text = parsed.get("answer", "")
                    else:
                        answer_text = ""
                except (json.JSONDecodeError, KeyError) as exc:
                    self._logger.error("Failed to parse structured response: %s", exc)
                    answer_text = ""
        except Exception as exc:
            self._logger.warning("LLM synthesis failed: %s", exc)
            return {"answer": "", "confidence": "0.0", "sources": []}

        confidence = f"{self._heuristic_confidence(answer_text):.2f}"
        return {
            "answer": answer_text,
            "confidence": confidence,
            "sources": [p.url for p, _score in top_pages],
        }

    # --------------------------------------------------------------------- #
    # Internal helpers                                                      #
    # --------------------------------------------------------------------- #

    @staticmethod
    def _build_prompt(
        question: str, ranked_pages: Sequence[Tuple[FirecrawlResult, float]]
    ) -> str:  # noqa: E501
        """Embed the *markdown* of ranked pages in a structured system prompt."""
        context_blobs = "\n\n".join(
            f"[Source {idx+1}] URL: {res.url}\n{res.content_md}"
            for idx, (res, _score) in enumerate(ranked_pages)
        )

        return (
            "You are a senior research assistant.\n\n"
            "Task:\n"
            "1. Use ONLY the information provided in the Sources section.\n"
            "2. Answer the question in a concise paragraph.\n"
            "3. Do NOT fabricate content.\n"
            '4. Output MUST be valid JSON: {"answer": str}\n\n'
            f"Question:\n{question}\n\n"
            f"Sources:\n{context_blobs}\n"
        )

    def _rank_and_deduplicate(
        self,
        pages: Sequence[FirecrawlResult],
        question: str,
    ) -> List[Tuple[FirecrawlResult, float]]:
        """Order pages by relevance; drop exact-duplicate URLs."""
        seen_urls = set()
        unique_pages: List[FirecrawlResult] = []
        for page in pages:
            if page.url not in seen_urls:
                unique_pages.append(page)
                seen_urls.add(page.url)

        q_tokens = Counter(_tokenise(question))
        scored = [(p, _relevance_score(p.content_md, q_tokens)) for p in unique_pages]
        scored.sort(key=lambda tup: tup[1], reverse=True)
        return scored

    @staticmethod
    def _heuristic_confidence(answer: str) -> float:
        """Crude confidence score based on length – placeholder for future ML."""
        words = len(answer.split())
        if words < 20:
            return 0.25
        if words < 60:
            return 0.6
        return 0.85


# --------------------------------------------------------------------------- #
# Quick CLI usage: python -m capabilities.synthesis_agent "QUESTION" <url...> #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import sys

    async def _demo() -> None:
        q = sys.argv[1] if len(sys.argv) > 1 else "What is the Turing test?"
        # Fake pages for demonstration only
        pages = [
            FirecrawlResult(
                url="https://example.com", content_md="The Turing test is ..."
            ),
        ]

        llm_stub = OpenAIResponsesInterface(api_key="DUMMY")  # type: ignore[arg-type]
        agent = SynthesisAgent(llm_stub)
        result = await agent.synthesise(q, pages)
        print(json.dumps(result, indent=2))

    asyncio.run(_demo())
