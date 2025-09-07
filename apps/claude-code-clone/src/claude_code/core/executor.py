"""Claude Code executor for headless operations."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from pathlib import Path
import aiofiles
import json

from opsvi_foundation import BaseComponent, ComponentError
from ..config import ClaudeCodeConfig
from ..providers.llm_adapter import LLMAdapter, LLMAdapterError

logger = logging.getLogger(__name__)


class ClaudeCodeExecutorError(ComponentError):
    """Error in Claude Code executor operations."""

    pass


class ClaudeCodeExecutor(BaseComponent):
    """Main executor for Claude Code Clone operations."""

    def __init__(self, config: ClaudeCodeConfig):
        """Initialize the Claude Code executor."""
        super().__init__(name="ClaudeCodeExecutor")
        self.config = config
        self.llm_adapter = LLMAdapter(config)
        self.working_directory = Path(config.working_directory).resolve()

        # Ensure working directory exists
        self.working_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized Claude Code executor in {self.working_directory}")

    async def _initialize_impl(self) -> None:
        """Initialize the executor."""
        logger.info("Claude Code executor initialized")

    async def _shutdown_impl(self) -> None:
        """Shutdown the executor."""
        await self.close()
        logger.info("Claude Code executor shutdown")

    async def _health_check_impl(self) -> bool:
        """Check if the executor is healthy."""
        try:
            # Basic health check - verify LLM adapter is available
            return self.llm_adapter is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def execute_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Execute a prompt and return the response."""
        try:
            # Build context-aware prompt
            enhanced_prompt = self._build_enhanced_prompt(prompt, context)

            # Create messages
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": enhanced_prompt},
            ]

            if stream:
                return self._stream_response(messages)
            else:
                response = await self.llm_adapter.chat_completion(messages)
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to execute prompt: {e}")
            raise ClaudeCodeExecutorError(f"Prompt execution failed: {e}") from e

    async def analyze_file(
        self,
        file_path: str,
        analysis_type: str = "general",
        context: Optional[str] = None,
    ) -> str:
        """Analyze a file and return analysis results."""
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.working_directory / file_path

            if not file_path.exists():
                raise ClaudeCodeExecutorError(f"File not found: {file_path}")

            # Read file content
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Determine language from file extension
            language = self._get_language_from_extension(file_path.suffix)

            # Analyze the code
            analysis = await self.llm_adapter.analyze_code(
                code=content,
                language=language,
                analysis_type=analysis_type,
                context=context,
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            raise ClaudeCodeExecutorError(f"File analysis failed: {e}") from e

    async def generate_file(
        self,
        file_path: str,
        prompt: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """Generate a file based on a prompt."""
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.working_directory / file_path

            # Determine language if not provided
            if not language:
                language = self._get_language_from_extension(file_path.suffix)

            # Generate code
            code = await self.llm_adapter.generate_code(
                prompt=prompt, language=language, context=context
            )

            # Write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(code)

            logger.info(f"Generated file: {file_path}")
            return code

        except Exception as e:
            logger.error(f"Failed to generate file {file_path}: {e}")
            raise ClaudeCodeExecutorError(f"File generation failed: {e}") from e

    async def refactor_file(
        self,
        file_path: str,
        refactor_type: str = "improve",
        context: Optional[str] = None,
    ) -> str:
        """Refactor a file and return the refactored code."""
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.working_directory / file_path

            if not file_path.exists():
                raise ClaudeCodeExecutorError(f"File not found: {file_path}")

            # Read file content
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Determine language from file extension
            language = self._get_language_from_extension(file_path.suffix)

            # Refactor the code
            refactored_code = await self.llm_adapter.refactor_code(
                code=content,
                refactor_type=refactor_type,
                language=language,
                context=context,
            )

            # Write refactored code back to file
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(refactored_code)

            logger.info(f"Refactored file: {file_path}")
            return refactored_code

        except Exception as e:
            logger.error(f"Failed to refactor file {file_path}: {e}")
            raise ClaudeCodeExecutorError(f"File refactoring failed: {e}") from e

    async def batch_analyze(
        self,
        file_patterns: List[str],
        analysis_type: str = "general",
        context: Optional[str] = None,
    ) -> Dict[str, str]:
        """Analyze multiple files in batch."""
        results = {}

        for pattern in file_patterns:
            files = list(self.working_directory.glob(pattern))
            for file_path in files:
                if file_path.is_file() and self._is_allowed_file(file_path):
                    try:
                        analysis = await self.analyze_file(
                            str(file_path), analysis_type=analysis_type, context=context
                        )
                        results[str(file_path)] = analysis
                    except Exception as e:
                        logger.error(f"Failed to analyze {file_path}: {e}")
                        results[str(file_path)] = f"Analysis failed: {e}"

        return results

    def _build_enhanced_prompt(
        self, prompt: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Build an enhanced prompt with context."""
        enhanced = prompt

        if context:
            if "files" in context:
                enhanced += f"\n\nRelevant files: {', '.join(context['files'])}"

            if "working_directory" in context:
                enhanced += f"\n\nWorking directory: {context['working_directory']}"

            if "project_type" in context:
                enhanced += f"\n\nProject type: {context['project_type']}"

        return enhanced

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the executor."""
        base_prompt = """You are Claude Code, an AI coding assistant. You help with:

1. Code analysis and review
2. Code generation and modification
3. Bug fixing and debugging
4. Code refactoring and optimization
5. Documentation and comments
6. Best practices and patterns

You are working in a headless environment and should provide clear, actionable responses.
Always consider security, performance, and maintainability in your suggestions.

Current working directory: {working_directory}
Allowed file extensions: {allowed_extensions}
"""

        if self.config.custom_instructions:
            base_prompt += f"\nCustom instructions: {self.config.custom_instructions}"

        return base_prompt.format(
            working_directory=self.working_directory,
            allowed_extensions=", ".join(self.config.allowed_file_extensions),
        )

    def _get_language_from_extension(self, extension: str) -> str:
        """Get programming language from file extension."""
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "bash",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".xml": "xml",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            ".md": "markdown",
            ".txt": "text",
            ".rst": "rst",
            ".tex": "latex",
            ".latex": "latex",
        }

        return language_map.get(extension.lower(), "text")

    def _is_allowed_file(self, file_path: Path) -> bool:
        """Check if file is allowed based on configuration."""
        if not self.config.enable_file_operations:
            return False

        if file_path.suffix not in self.config.allowed_file_extensions:
            return False

        if file_path.stat().st_size > self.config.max_file_size:
            return False

        return True

    async def _stream_response(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream response from LLM."""
        try:
            async for chunk in await self.llm_adapter.chat_completion(
                messages, stream=True
            ):
                if hasattr(chunk, "choices") and chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"Error: {e}"

    async def close(self) -> None:
        """Close the executor and cleanup resources."""
        await self.llm_adapter.close()
        logger.info("Claude Code executor closed")
