"""
OpenAI Codex MCP Server Implementation

Provides MCP tools for code generation, completion, and analysis using OpenAI's models.
"""

import asyncio
import json
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from fastmcp import FastMCP
from openai import AsyncOpenAI
import aiofiles

from .config import CodexConfig
from .models import CodexRequest, CodexResponse, CodexMode, CodeContext

logger = logging.getLogger(__name__)


class OpenAICodexServer:
    """MCP Server for OpenAI Codex/GPT-4 code operations"""

    def __init__(self, config: Optional[CodexConfig] = None):
        self.config = config or CodexConfig()
        self.mcp = FastMCP("openai-codex-server")
        self.client = AsyncOpenAI(api_key=self.config.openai_api_key)

        # Setup MCP tools
        self._setup_tools()

    def _setup_tools(self):
        """Register MCP tools for Codex operations"""

        @self.mcp.tool()
        async def codex_complete(
            code: str, language: Optional[str] = None, max_tokens: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Complete partial code using OpenAI Codex/GPT-4.

            Args:
                code: Partial code to complete
                language: Programming language (optional)
                max_tokens: Maximum tokens to generate

            Returns:
                Completed code and metadata
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.COMPLETE,
                language=language,
                max_tokens=max_tokens,
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_generate(
            prompt: str,
            language: Optional[str] = None,
            context_files: Optional[List[str]] = None,
            temperature: Optional[float] = None,
        ) -> Dict[str, Any]:
            """
            Generate code from natural language description.

            Args:
                prompt: Natural language description
                language: Target programming language
                context_files: Files to include as context
                temperature: Creativity level (0.0-1.0)

            Returns:
                Generated code and metadata
            """
            request = CodexRequest(
                prompt=prompt,
                mode=CodexMode.GENERATE,
                language=language,
                context_files=context_files,
                temperature=temperature,
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_explain(
            code: str, language: Optional[str] = None, detail_level: str = "medium"
        ) -> Dict[str, Any]:
            """
            Explain what code does in natural language.

            Args:
                code: Code to explain
                language: Programming language
                detail_level: Level of detail (brief, medium, detailed)

            Returns:
                Explanation and insights
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.EXPLAIN,
                language=language,
                metadata={"detail_level": detail_level},
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_refactor(
            code: str, language: Optional[str] = None, goals: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Refactor code for better quality.

            Args:
                code: Code to refactor
                language: Programming language
                goals: Refactoring goals (e.g., ["performance", "readability"])

            Returns:
                Refactored code and improvements made
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.REFACTOR,
                language=language,
                metadata={"goals": goals or ["readability", "efficiency"]},
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_debug(
            code: str,
            error_message: Optional[str] = None,
            language: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Debug code and suggest fixes.

            Args:
                code: Code with potential bugs
                error_message: Error message if available
                language: Programming language

            Returns:
                Fixed code and debugging insights
            """
            prompt = f"{code}\n\nError: {error_message}" if error_message else code

            request = CodexRequest(
                prompt=prompt, mode=CodexMode.DEBUG, language=language
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_test(
            code: str,
            language: Optional[str] = None,
            test_framework: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Generate tests for code.

            Args:
                code: Code to test
                language: Programming language
                test_framework: Testing framework to use

            Returns:
                Generated tests
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.TEST,
                language=language,
                metadata={"test_framework": test_framework},
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_document(
            code: str, language: Optional[str] = None, style: str = "docstring"
        ) -> Dict[str, Any]:
            """
            Generate documentation for code.

            Args:
                code: Code to document
                language: Programming language
                style: Documentation style (docstring, markdown, jsdoc)

            Returns:
                Documented code
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.DOCUMENT,
                language=language,
                metadata={"style": style},
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_review(
            code: str,
            language: Optional[str] = None,
            focus_areas: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """
            Review code and provide feedback.

            Args:
                code: Code to review
                language: Programming language
                focus_areas: Areas to focus on (security, performance, etc.)

            Returns:
                Review feedback and suggestions
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.REVIEW,
                language=language,
                metadata={
                    "focus_areas": focus_areas or ["quality", "security", "performance"]
                },
            )

            response = await self._process_request(request)
            return response.dict()

        @self.mcp.tool()
        async def codex_translate(
            code: str,
            from_language: str,
            to_language: str,
            preserve_comments: bool = True,
        ) -> Dict[str, Any]:
            """
            Translate code between programming languages.

            Args:
                code: Code to translate
                from_language: Source language
                to_language: Target language
                preserve_comments: Whether to preserve comments

            Returns:
                Translated code
            """
            request = CodexRequest(
                prompt=code,
                mode=CodexMode.TRANSLATE,
                language=to_language,
                metadata={
                    "from_language": from_language,
                    "preserve_comments": preserve_comments,
                },
            )

            response = await self._process_request(request)
            return response.dict()

    async def _process_request(self, request: CodexRequest) -> CodexResponse:
        """Process a Codex request"""

        start_time = time.time()

        try:
            # Check cache if enabled
            if self.config.enable_cache:
                cached_result = await self._get_cached_result(request)
                if cached_result:
                    return cached_result

            # Build the prompt based on mode
            system_prompt, user_prompt = self._build_prompts(request)

            # Load context if needed
            if request.context_files and self.config.include_file_context:
                context = await self._load_context_files(request.context_files)
                user_prompt = f"{context}\n\n{user_prompt}"

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                top_p=self.config.top_p,
                stop=request.stop_sequences or self.config.stop_sequences,
                stream=self.config.streaming,
            )

            # Process response
            if self.config.streaming:
                result = await self._process_stream(response)
            else:
                result = response.choices[0].message.content

            # Create response object
            codex_response = CodexResponse(
                success=True,
                mode=request.mode,
                result=result,
                tokens_used=response.usage.total_tokens
                if hasattr(response, "usage")
                else 0,
                execution_time=time.time() - start_time,
                cached=False,
            )

            # Cache result if enabled
            if self.config.enable_cache:
                await self._cache_result(request, codex_response)

            return codex_response

        except Exception as e:
            logger.error(f"Codex request failed: {e}")
            return CodexResponse(
                success=False,
                mode=request.mode,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def _build_prompts(self, request: CodexRequest) -> tuple[str, str]:
        """Build system and user prompts based on mode"""

        mode_prompts = {
            CodexMode.COMPLETE: (
                "You are a code completion assistant. Complete the given code snippet naturally and idiomatically.",
                f"Complete this {request.language or 'code'}:\n\n{request.prompt}",
            ),
            CodexMode.GENERATE: (
                "You are a code generation expert. Generate clean, efficient, and well-structured code based on the description.",
                f"Generate {request.language or 'code'} for: {request.prompt}",
            ),
            CodexMode.EXPLAIN: (
                "You are a code explanation expert. Explain code clearly and concisely.",
                f"Explain this code:\n\n{request.prompt}",
            ),
            CodexMode.REFACTOR: (
                f"You are a code refactoring expert. Improve code for: {request.metadata.get('goals', ['quality'])}",
                f"Refactor this code:\n\n{request.prompt}",
            ),
            CodexMode.DEBUG: (
                "You are a debugging expert. Identify and fix bugs in code.",
                f"Debug and fix this code:\n\n{request.prompt}",
            ),
            CodexMode.TEST: (
                f"You are a testing expert. Generate comprehensive tests using {request.metadata.get('test_framework', 'best practices')}.",
                f"Generate tests for:\n\n{request.prompt}",
            ),
            CodexMode.DOCUMENT: (
                f"You are a documentation expert. Generate {request.metadata.get('style', 'docstring')} style documentation.",
                f"Document this code:\n\n{request.prompt}",
            ),
            CodexMode.REVIEW: (
                f"You are a code review expert. Focus on: {request.metadata.get('focus_areas', ['quality'])}",
                f"Review this code:\n\n{request.prompt}",
            ),
            CodexMode.TRANSLATE: (
                f"You are a code translation expert. Translate from {request.metadata.get('from_language')} to {request.language}.",
                f"Translate this code:\n\n{request.prompt}",
            ),
        }

        return mode_prompts.get(
            request.mode, ("You are a helpful coding assistant.", request.prompt)
        )

    async def _load_context_files(self, file_paths: List[str]) -> str:
        """Load context from files"""

        context_parts = ["### Context Files ###"]

        for path in file_paths[:5]:  # Limit to 5 files
            try:
                async with aiofiles.open(path, "r") as f:
                    content = await f.read()
                    context_parts.append(
                        f"\n--- {path} ---\n{content[:2000]}..."
                    )  # Limit each file
            except Exception as e:
                logger.warning(f"Failed to load context file {path}: {e}")

        return "\n".join(context_parts)

    async def _process_stream(self, response) -> str:
        """Process streaming response"""

        result_parts = []
        async for chunk in response:
            if chunk.choices[0].delta.content:
                result_parts.append(chunk.choices[0].delta.content)

        return "".join(result_parts)

    async def _get_cached_result(
        self, request: CodexRequest
    ) -> Optional[CodexResponse]:
        """Get cached result if available"""

        cache_key = self._get_cache_key(request)
        cache_file = Path(self.config.cache_dir) / f"{cache_key}.json"

        if cache_file.exists():
            try:
                # Check if cache is still valid
                if time.time() - cache_file.stat().st_mtime < self.config.cache_ttl:
                    async with aiofiles.open(cache_file, "r") as f:
                        data = json.loads(await f.read())
                        response = CodexResponse(**data)
                        response.cached = True
                        return response
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        return None

    async def _cache_result(self, request: CodexRequest, response: CodexResponse):
        """Cache a result"""

        cache_key = self._get_cache_key(request)
        cache_file = Path(self.config.cache_dir) / f"{cache_key}.json"

        try:
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(json.dumps(response.dict()))
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def _get_cache_key(self, request: CodexRequest) -> str:
        """Generate cache key for request"""

        key_parts = [
            request.mode.value,
            request.prompt[:100],
            request.language or "",
            str(request.max_tokens),
            str(request.temperature),
        ]

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def run(self):
        """Run the MCP server"""
        await self.mcp.run()


# Entry point for running as standalone server
if __name__ == "__main__":
    import asyncio

    server = OpenAICodexServer()
    asyncio.run(server.run())
