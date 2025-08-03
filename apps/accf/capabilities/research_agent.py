"""
ACCF Research Agent – Phase-5 Upgrade
====================================

Adds *Academic Research Integration* on top of the existing knowledge-graph +
web research stack.

Key additions
-------------
• `ArxivTool` wrapper for fast ArXiv searches.
• Heuristic **smart-routing** (`_should_use_academic_research`) that decides
  when an academic search is warranted.
• `_gather_academic_research` coroutine – searches ArXiv, converts papers into
  `FirecrawlResult`-compatible objects so the existing SynthesisAgent can
  remain untouched.
• Knowledge graph *persistence* for academic papers (re-use `upsert_page`).
• Unified pipeline order:

      1. Neo4j KG lookup
      2. Optional ArXiv search (if heuristic says so)
      3. External web research (Brave + Firecrawl)
      4. Synthesis

Public API and method names remain *unchanged* for full backward compatibility.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from typing import Any, Dict, List, Sequence, Set

import openai

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

from capabilities.tools.brave_search_tool import (  # noqa: WPS433
    BraveSearchResult,
    BraveSearchTool,
    BraveSearchUnavailableError,
)
from capabilities.neo4j_knowledge_graph import (
    KGResult,
    KnowledgeGraphUnavailableError,
    Neo4jKnowledgeGraph,
)
from capabilities.synthesis_agent import SynthesisAgent
from capabilities.tools.arxiv_tool import (
    ArxivPaperResult,
    ArxivTool,
    ArxivUnavailableError,
)
from capabilities.tools.context7_tool import (
    Context7Result,
    Context7Tool,
    Context7UnavailableError,
)
from capabilities.tools.firecrawl_tool import (
    FirecrawlResult,
    FirecrawlTool,
    FirecrawlUnavailableError,
)


class ResearchAgent:
    """Production-grade research agent with external tool integration."""

    # Tuning knobs – surfaced as class-vars for easier monkey-patch in tests.
    _LLM_MAX_RETRIES = 3
    _LLM_TIMEOUT_SEC = 60.0
    _LLM_BACKOFF_BASE_SEC = 2.0
    _CONCURRENCY_LIMIT = 5  # Max parallel network I/O (scrapes + searches).
    _MAX_SEARCH_QUERIES = 3
    _MAX_RESULTS_PER_QUERY = 5

    _ARXIV_MAX_RESULTS = 5
    _MIN_KG_RESULTS = 3

    # ------------------------------------------------------------------ #
    # Construction                                                       #
    # ------------------------------------------------------------------ #

    def __init__(self, api_key_env: str = "OPENAI_API_KEY") -> None:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise EnvironmentError(
                f"OpenAI API key environment variable '{api_key_env}' is not set."
            )

        self.llm = OpenAIResponsesInterface(api_key=api_key)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.research_db: List[Dict[str, Any]] = []

        # Lazy resources
        self._brave_tool: BraveSearchTool | None = None
        self._firecrawl_tool: FirecrawlTool | None = None
        self._arxiv_tool: ArxivTool | None = None
        self._context7_tool: Context7Tool | None = None
        self._synthesis_agent: SynthesisAgent | None = None
        self._kg: Neo4jKnowledgeGraph | None = None

        # Shared semaphore to cap network concurrency
        self._net_semaphore = asyncio.Semaphore(self._CONCURRENCY_LIMIT)

    # ------------------------------------------------------------------ #
    # Backward-compatible public API                                     #
    # ------------------------------------------------------------------ #

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Static canned answers – unchanged for contract stability."""
        if "Pride and Prejudice" in question:
            return {"answer": "Jane Austen", "sources": ["Wikipedia"]}
        return {"answer": f"No research found for: {question}", "sources": []}

    def answer_question_using_llm(self, question: str) -> Dict[str, Any]:
        """Answer a question using the LLM only (no external context)."""
        return self._call_llm(question)

    # ------------------------------------------------------------------ #
    # Phase-2: External Research Pipeline                                #
    # ------------------------------------------------------------------ #

    def _gather_external_research(self, question: str) -> Dict[str, Any]:
        """Best-effort Brave search + Firecrawl scrape (see Phase-2)."""
        self.logger.debug("External research started for '%s'", question)
        self._brave_tool = self._brave_tool or BraveSearchTool()
        self._firecrawl_tool = self._firecrawl_tool or FirecrawlTool()

        queries = self._transform_question_to_queries(question)
        self.logger.debug("Generated queries: %s", queries)

        # --- Brave search fan-out ------------------------------------------------
        brave_results: List[BraveSearchResult] = []

        # Run searches sequentially to avoid async issues
        for q in queries:
            try:
                results = self._brave_tool.search(q, self._MAX_RESULTS_PER_QUERY)
                brave_results.extend(results)
            except BraveSearchUnavailableError as exc:
                self.logger.warning("Brave search failed: %s", exc)

        seen: Set[str] = set()
        brave_results = [
            r for r in brave_results if not (r.url in seen or seen.add(r.url))
        ]

        # --- Firecrawl scrape ----------------------------------------------------
        scraped: List[FirecrawlResult] = []
        for res in brave_results:
            try:
                scraped_page = self._firecrawl_tool.scrape(res.url)
                scraped.append(scraped_page)
            except FirecrawlUnavailableError as exc:
                self.logger.warning("Firecrawl scrape failed: %s", exc)

        self.logger.debug(
            "Research done – brave=%s, scraped=%s",
            len(brave_results),
            len(scraped),
        )

        return {
            "brave_results": brave_results or None,
            "scraped_pages": scraped or None,
        }

    # ------------------------------------------------------------------ #
    # Sync wrapper – public                                               #
    # ------------------------------------------------------------------ #

    def answer_question_with_external_tools(self, question: str) -> Dict[str, Any]:
        """
        Intelligent multi-source research pipeline with sequential logic.

        Order of operations:
        1. Knowledge-graph retrieval.
        2. Web search (Brave → Firecrawl) for context education.
        3. Generate specialized queries based on web context.
        4. Academic search (ArXiv) with intelligent queries *if relevant*.
        5. Technical documentation search (Context7) with intelligent queries *if relevant*.
        6. Synthesis and storage.
        """
        self.logger.info("Answering (KG+web+academic+docs) question: %s", question)
        try:
            pages_to_use: List[FirecrawlResult] = []
            context7_results: List[Context7Result] = []

            # 1. --- Knowledge Graph ---------------------------------------
            kg_pages = self._kg_lookup(question)
            if kg_pages:
                pages_to_use.extend(kg_pages)

            # 2. --- Web research for context education -------------------
            ext = self._gather_external_research(question)
            web_pages: Sequence[FirecrawlResult] | None = ext.get("scraped_pages")
            brave_results: Sequence[BraveSearchResult] | None = ext.get("brave_results")

            if web_pages:
                pages_to_use.extend(web_pages)
                self._kg_upsert_all(web_pages)

            # 3. --- Extract web context for specialized queries ----------
            web_context = ""
            if brave_results and web_pages:
                web_context = self._extract_web_context(
                    list(brave_results), list(web_pages)
                )

            # 4. --- Academic research with intelligent queries -----------
            if self._should_use_academic_research(question) and web_context:
                arxiv_queries = self._generate_arxiv_queries(question, web_context)
                self.logger.info(f"Generated ArXiv queries: {arxiv_queries}")

                # Use ThreadPoolExecutor for async ArXiv calls
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._gather_academic_research_with_queries(arxiv_queries),
                    )
                    arxiv_papers = future.result()

                if arxiv_papers:
                    # Convert ArXiv papers to FirecrawlResult format with full content
                    for paper in arxiv_papers:
                        # Use downloaded content if available, otherwise fall back to abstract
                        if paper.content:
                            content = f"# {paper.title}\n\n{paper.content}"
                        else:
                            content = f"# {paper.title}\n\n{paper.abstract}"
                        pages_to_use.append(
                            FirecrawlResult(url=paper.pdf_url, content_md=content)
                        )
                    self._kg_upsert_all(pages_to_use[-len(arxiv_papers) :])

            # 5. --- Context7 documentation with intelligent queries ------
            context7_results = []
            if self._should_use_context7_docs(question) and web_context:
                context7_queries = self._generate_context7_queries(
                    question, web_context
                )
                self.logger.info(f"Generated Context7 queries: {context7_queries}")

                context7_results = self._gather_context7_docs_with_queries(
                    context7_queries
                )

            if not pages_to_use and not context7_results:
                raise RuntimeError("No context pages or documentation available")

            # Deduplicate by URL while preserving order
            seen: Set[str] = set()
            pages_to_use = [
                p for p in pages_to_use if not (p.url in seen or seen.add(p.url))
            ]

            # 6. --- Synthesis --------------------------------------------
            self._synthesis_agent = self._synthesis_agent or SynthesisAgent(self.llm)

            # Combine all sources for synthesis
            all_sources = pages_to_use.copy()

            # Add Context7 results as FirecrawlResult-compatible objects
            for ctx_result in context7_results:
                content = f"# {ctx_result.library_id}\n\n{ctx_result.content}"
                all_sources.append(
                    FirecrawlResult(
                        url=f"context7://{ctx_result.library_id}", content_md=content
                    )
                )

            synth = self._synthesis_agent.synthesise(question, all_sources)

            answer = synth.get("answer", "")
            confidence = synth.get("confidence", "0.0")
            sources = synth.get("sources", [])

            self._store_research_entry(question, answer, sources)
            return {
                "answer": answer,
                "confidence": confidence,
                "sources": sources,
            }
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Full pipeline failed – fallback (%s)", exc)
            return self.answer_question_using_llm(question)

    # ------------------------------------------------------------------ #
    # Academic research helpers                                          #
    # ------------------------------------------------------------------ #

    def _should_use_academic_research(self, question: str) -> bool:
        """
        Very simple heuristic:

        If the question contains any academic-style keywords, trigger ArXiv.
        """
        academic_keywords = {
            "paper",
            "study",
            "research",
            "journal",
            "arxiv",
            "dataset",
            "algorithm",
            "model",
        }
        q_lower = question.lower()
        return any(word in q_lower for word in academic_keywords)

    def _gather_academic_research(
        self,
        question: str,
    ) -> List[FirecrawlResult]:
        self._arxiv_tool = self._arxiv_tool or ArxivTool()
        try:
            # Simple approach: always use asyncio.run in a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._arxiv_tool.search(question, self._ARXIV_MAX_RESULTS),
                )
                papers: List[ArxivPaperResult] = future.result()
        except Exception as exc:
            self.logger.warning("Arxiv search failed: %s", exc)
            return []

        # Convert to FirecrawlResult-like objects so the existing synthesis
        # pipeline can stay unchanged.
        pages: List[FirecrawlResult] = []
        for p in papers:
            content = f"# {p.title}\n\n{p.abstract}"
            pages.append(FirecrawlResult(url=p.pdf_url, content_md=content))
        self.logger.debug("Gathered %s academic pages", len(pages))
        return pages

    def _should_use_context7_docs(self, question: str) -> bool:
        """Heuristic to decide if Context7 documentation search is warranted."""
        # Keywords that suggest technical documentation would be valuable
        tech_doc_keywords = {
            "api",
            "library",
            "framework",
            "sdk",
            "package",
            "module",
            "function",
            "method",
            "class",
            "interface",
            "documentation",
            "guide",
            "tutorial",
            "example",
            "usage",
            "installation",
            "configuration",
            "setup",
            "integration",
            "deployment",
            "development",
            "programming",
            "code",
            "implementation",
            "best practices",
            "reference",
            "manual",
        }

        question_lower = question.lower()
        return any(keyword in question_lower for keyword in tech_doc_keywords)

    def _extract_web_context(
        self, brave_results: List[BraveSearchResult], scraped: List[FirecrawlResult]
    ) -> str:
        """Extract context from web search results to inform specialized queries."""
        context_parts = []

        # Add titles and descriptions from Brave results
        for result in brave_results[:5]:  # Use top 5 results
            if result.title:
                context_parts.append(f"Title: {result.title}")
            if result.description:
                context_parts.append(f"Description: {result.description}")

        # Add content from scraped pages
        for page in scraped[:3]:  # Use top 3 scraped pages
            if page.content_md:
                # Take first 500 characters as context
                content_preview = page.content_md[:500].replace("\n", " ").strip()
                context_parts.append(f"Content: {content_preview}")

        return " | ".join(context_parts)

    def _generate_arxiv_queries(self, question: str, web_context: str) -> List[str]:
        """Generate ArXiv-specific queries based on question and web context."""
        try:
            prompt = f"""
Based on the research question and web context, generate 2-3 specific ArXiv search queries.
Focus on academic terminology, technical concepts, and research areas.

Question: {question}
Web Context: {web_context}

Generate queries that would find relevant academic papers. Use technical terms, avoid generic words.
Format as JSON array of strings.
"""

            response = self._call_llm(prompt)
            if response and "answer" in response:
                import json

                try:
                    queries = json.loads(response["answer"])
                    if isinstance(queries, list):
                        return [str(q) for q in queries[:3]]  # Limit to 3 queries
                except (json.JSONDecodeError, TypeError):
                    pass

            # Fallback: simple query transformation
            return [
                f"{question} research",
                f"{question} algorithm",
                f"{question} methodology",
            ]

        except Exception as exc:
            self.logger.warning(f"ArXiv query generation failed: {exc}")
            return [question]

    def _generate_context7_queries(self, question: str, web_context: str) -> List[str]:
        """Generate Context7-specific queries based on question and web context."""
        try:
            prompt = f"""
Based on the research question and web context, identify 2-3 specific library names that would have relevant documentation in Context7.

Question: {question}
Web Context: {web_context}

Identify specific library names (not generic terms like "python" or "javascript") that would have documentation relevant to this question.
Focus on actual library/package names like "openai", "react", "next.js", "fastapi", "django", "express", etc.

Return ONLY a JSON array of library names as strings, with no additional text or explanation.

Example format: ["openai", "react", "next.js"]
"""

            response = self._call_llm(prompt)
            if response and "answer" in response:
                import json

                try:
                    # Try to extract JSON from the response
                    answer_text = response["answer"].strip()

                    # Remove any markdown code blocks if present
                    if answer_text.startswith("```json"):
                        answer_text = answer_text[7:]
                    if answer_text.endswith("```"):
                        answer_text = answer_text[:-3]

                    libraries = json.loads(answer_text.strip())
                    if isinstance(libraries, list):
                        return [
                            str(lib) for lib in libraries[:3]
                        ]  # Limit to 3 libraries
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.warning(f"Failed to parse LLM response as JSON: {e}")
                    self.logger.debug(f"Raw response: {response['answer']}")

            # Fallback: extract potential library names from context using a more specific prompt
            fallback_prompt = f"""
Extract specific library/package names from this text. Return ONLY a JSON array of library names.

Text: {question} {web_context}

Examples of what to look for:
- "openai" (not "python")
- "react" (not "javascript")
- "next.js" (not "framework")
- "fastapi" (not "python web framework")
- "django" (not "python")
- "express" (not "node.js")

Return ONLY: ["library1", "library2"]
"""

            fallback_response = self._call_llm(fallback_prompt)
            if fallback_response and "answer" in fallback_response:
                try:
                    answer_text = fallback_response["answer"].strip()
                    if answer_text.startswith("```json"):
                        answer_text = answer_text[7:]
                    if answer_text.endswith("```"):
                        answer_text = answer_text[:-3]

                    libraries = json.loads(answer_text.strip())
                    if isinstance(libraries, list):
                        return [str(lib) for lib in libraries[:3]]
                except (json.JSONDecodeError, TypeError):
                    pass

            # Last resort: return empty list if we can't extract anything
            self.logger.warning("Could not extract library names from LLM response")
            return []

        except Exception as exc:
            self.logger.warning(f"Context7 query generation failed: {exc}")
            return []

    async def _gather_academic_research_with_queries(
        self, queries: List[str]
    ) -> List[ArxivPaperResult]:
        """Gather academic research using specific queries."""
        try:
            self._arxiv_tool = self._arxiv_tool or ArxivTool()
            all_papers = []

            for query in queries:
                try:
                    # Use the enhanced search method with paper downloading
                    papers = await self._arxiv_tool.search(
                        query, max_results=3, download_papers=True
                    )
                    all_papers.extend(papers)
                except ArxivUnavailableError as exc:
                    self.logger.warning(
                        f"ArXiv search failed for query '{query}': {exc}"
                    )
                    continue

            return all_papers[: self._ARXIV_MAX_RESULTS]

        except Exception as exc:
            self.logger.error(f"Academic research gathering failed: {exc}")
            return []

    def _gather_context7_docs_with_queries(
        self, queries: List[str]
    ) -> List[Context7Result]:
        """Gather Context7 documentation using specific library queries."""
        try:
            self._context7_tool = self._context7_tool or Context7Tool()
            all_docs = []

            for library_name in queries:
                try:
                    # Use ThreadPoolExecutor for async Context7 calls
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # Create a new event loop in the thread
                        def run_async_context7():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return loop.run_until_complete(
                                    self._context7_tool.search_and_get_docs(
                                        library_name=library_name, tokens=5000
                                    )
                                )
                            finally:
                                loop.close()

                        future = executor.submit(run_async_context7)
                        result = future.result()
                        if result.success:
                            all_docs.append(result)
                except Exception as exc:
                    self.logger.warning(
                        f"Context7 search failed for library '{library_name}': {exc}"
                    )
                    continue

            return all_docs

        except Exception as exc:
            self.logger.error(f"Context7 documentation gathering failed: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Knowledge-graph helpers                                            #
    # ------------------------------------------------------------------ #

    def _kg_lookup(self, question: str) -> List[FirecrawlResult] | None:
        try:
            self._kg = self._kg or Neo4jKnowledgeGraph()
            # Simple approach: always use asyncio.run in a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._kg.query(question))
                kg_hits: List[KGResult] = future.result()

            return [
                FirecrawlResult(url=hit.url, content_md=hit.content_md)
                for hit in kg_hits
            ]
        except Exception as exc:
            self.logger.warning("Knowledge graph lookup failed: %s", exc)
            return None

    def _kg_upsert_all(self, pages: Sequence[FirecrawlResult]) -> None:
        if not pages:
            return
        try:
            self._kg = self._kg or Neo4jKnowledgeGraph()
            # Simple approach: always use asyncio.run in a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    asyncio.gather(*(self._kg.upsert_page(p) for p in pages)),
                )
                future.result()

            self.logger.debug("Persisted %s pages to KG", len(pages))
        except Exception as exc:
            self.logger.warning("Could not persist to KG: %s", exc)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _transform_question_to_queries(self, question: str) -> List[str]:
        """
        Deterministic heuristic that converts a question into multiple
        search-engine-friendly queries (no extra LLM call).

        Strategy (simplified clone of reference Stage-2):
        • Lower-case, strip punctuation.
        • Remove common stop-words.
        • Create variations with / without quoted phrases.
        """
        lowered = "".join(
            ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in question
        )
        tokens = [
            tok
            for tok in lowered.split()
            if tok not in {"the", "is", "a", "an", "of", "in", "to"}
        ]
        base_query = " ".join(tokens)
        queries = [base_query]

        # Add quoted phrase version for more precise search
        if len(tokens) > 2:
            queries.append(f'"{base_query}"')

        # Add shorter variant if long
        if len(tokens) > 5:
            queries.append(" ".join(tokens[:5]))

        return queries[: self._MAX_SEARCH_QUERIES]

    async def _run_with_sem(self, coro, *args, **kwargs):  # type: ignore[no-self-use]
        """
        Helper to run an async callable under the shared semaphore (concurrency
        guard).  Separate function used so we can `create_task` it easily.
        """
        async with self._net_semaphore:
            return await coro(*args, **kwargs)

    # ----------------------------- #
    # OpenAI call with retries      #
    # ----------------------------- #

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Wrapper around the OpenAI interface with resiliency."""
        last_exc: Exception | None = None
        for attempt in range(1, self._LLM_MAX_RETRIES + 1):
            try:
                start_ts = time.monotonic()
                # Use Chat Completions API with Structured Outputs for reliable parsing
                import concurrent.futures
                import openai

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        asyncio.wait_for(
                            openai.AsyncOpenAI().chat.completions.create(
                                model="gpt-4.1-mini",  # Approved model for agent execution with Structured Outputs
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a helpful research assistant. Provide comprehensive answers with sources.",
                                    },
                                    {"role": "user", "content": prompt},
                                ],
                                response_format={
                                    "type": "json_schema",
                                    "json_schema": {
                                        "name": "research_response",
                                        "strict": True,
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "answer": {
                                                    "type": "string",
                                                    "description": "The comprehensive answer to the research question",
                                                },
                                                "sources": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "List of source URLs or references used",
                                                },
                                            },
                                            "required": ["answer", "sources"],
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
                    self.logger.warning(
                        "LLM refused to answer: %s", response.choices[0].message.refusal
                    )
                    return {"answer": "[Refused to answer]", "sources": []}

                # Parse the structured response
                try:
                    import json

                    content = response.choices[0].message.content
                    if content:
                        parsed = json.loads(content)
                        answer = parsed.get("answer", "")
                        sources = parsed.get("sources", [])
                        if isinstance(sources, str):
                            sources = [sources]
                    else:
                        answer = ""
                        sources = []
                except (json.JSONDecodeError, KeyError) as exc:
                    self.logger.error("Failed to parse structured response: %s", exc)
                    answer = "[Parse error]"
                    sources = []

                self._store_research_entry(prompt, answer, sources)
                return {"answer": answer, "sources": sources}
            except Exception as exc:
                last_exc = exc
                elapsed = time.monotonic() - start_ts
                backoff = self._LLM_BACKOFF_BASE_SEC * (
                    2 ** (attempt - 1)
                )  # exponential
                backoff += random.uniform(0, 1)  # jitter
                self.logger.warning(
                    "LLM call failed (attempt %s/%s, %.1fs): %s – retrying in %.1fs",
                    attempt,
                    self._LLM_MAX_RETRIES,
                    elapsed,
                    exc,
                    backoff,
                )
                if attempt < self._LLM_MAX_RETRIES:
                    time.sleep(backoff)

        assert last_exc is not None
        self.logger.error("LLM call ultimately failed: %s", last_exc)
        return {"answer": f"[Error: {last_exc}]", "sources": []}

    def _store_research_entry(
        self,
        prompt: str,
        answer: str,
        sources: Sequence[str],
    ) -> None:
        """Persist a research interaction in memory (placeholder DB)."""
        self.research_db.append(
            {
                "prompt": prompt,
                "answer": answer,
                "sources": list(sources),
            }
        )
        self.logger.debug("Stored research entry. Total: %s", len(self.research_db))
