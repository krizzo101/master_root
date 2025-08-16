"""
File Operations Module

Handles file extraction, creation, and management for the Smart Decomposition Agent.
Extracted from smart_decomposition_agent.py for better modularity.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.sd_logging import LoggerFactory


class FileOperationsManager:
    """Handles all file operations for the Smart Decomposition Agent"""

    def __init__(self, logger_factory: LoggerFactory):
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_debug_logger()

    async def extract_and_create_files(self, state: SmartDecompositionState):
        """Extract files from agent outputs and create them in the project directory"""
        self.logger.info("Extracting and creating files from agent outputs...")

        agent_outputs = state.get("agent_outputs", {})
        if not agent_outputs:
            self.logger.warning("No agent outputs available for file extraction")
            return

        files_created = 0

        for agent_role, output in agent_outputs.items():
            # Output is the raw string content from the agent, not a dict
            if not output or not isinstance(output, str) or len(output.strip()) == 0:
                self.logger.warning(
                    f"Skipping {agent_role}: no output or empty response"
                )
                continue

            # Use the raw output content directly
            agent_result = output

            try:
                # 🎯 SIMPLE APPROACH: Scan project directory for files created during agent execution
                self.logger.info(
                    f"🔍 {agent_role}: Scanning project directory for files created during execution"
                )

                # Get project path from global context
                from src.applications.oamat_sd.src.utils.project_context import (
                    project_context,
                )

                project_path = project_context.get_project_path()
                if not project_path:
                    self.logger.error(f"❌ No project path available for {agent_role}")
                    extracted_files = []
                else:
                    # Scan for files created during this execution
                    import time
                    from pathlib import Path

                    project_dir = Path(project_path)
                    current_time = time.time()
                    extracted_files = []

                    # Find files modified in the last few minutes (agent execution window)
                    if project_dir.exists():
                        for file_path in project_dir.rglob("*"):
                            if file_path.is_file() and not file_path.name.startswith(
                                "."
                            ):
                                # Skip log files and system files
                                if "logs/" in str(file_path) or file_path.suffix in [
                                    ".log",
                                    ".jsonl",
                                ]:
                                    continue

                                # Check if file was recently modified (within last 10 minutes)
                                file_mtime = file_path.stat().st_mtime
                                if current_time - file_mtime < 600:  # 10 minutes
                                    try:
                                        with open(file_path, encoding="utf-8") as f:
                                            content = f.read()

                                        relative_path = str(
                                            file_path.relative_to(project_dir)
                                        )
                                        extracted_files.append(
                                            {
                                                "filename": relative_path,
                                                "content": content,
                                                "language": self._detect_language_from_extension(
                                                    file_path.suffix
                                                ),
                                                "agent": agent_role,
                                            }
                                        )
                                    except Exception as e:
                                        self.logger.warning(
                                            f"Could not read file {file_path}: {e}"
                                        )

                    self.logger.info(
                        f"✅ Found {len(extracted_files)} files created by {agent_role} during execution"
                    )

            except Exception as e:
                self.logger.error(f"❌ File scanning failed for {agent_role}: {e}")
                extracted_files = []

            # NOTE: In new architecture, files are created directly by agents using write_file tool
            # This scanning is just for reporting what was created
            files_created += len(extracted_files)

            if extracted_files:
                self.logger.info(
                    f"📊 Detected {len(extracted_files)} files from {agent_role}:"
                )
                for file_info in extracted_files:
                    self.logger.info(
                        f"  📄 {file_info['filename']} ({len(file_info.get('content', ''))} chars)"
                    )

        self.logger.info(f"File extraction complete: {files_created} files created")

    def _extract_content_from_agent_output(self, agent_output) -> str:
        """Extract actual content from LangGraph agent output format"""
        try:
            self.logger.debug(
                f"DEBUG: Extracting content from agent output type: {type(agent_output)}"
            )

            preview_length = ConfigManager().content_limits.preview_length
            self.logger.debug(
                f"DEBUG: Agent output preview: {str(agent_output)[:preview_length]}..."
            )

            # Handle string representation of message objects
            if isinstance(agent_output, str):
                self.logger.debug("DEBUG: Processing string output")

                # First try to extract from dict structure if present
                if "'messages':" in agent_output and "AIMessage(" in agent_output:
                    import re

                    self.logger.debug("DEBUG: Found messages dict structure")

                    # Extract all AIMessage content (the actual agent responses)
                    ai_messages = re.findall(
                        r"AIMessage\(content='([^']*(?:''[^']*)*)'",
                        agent_output,
                        re.DOTALL,
                    )
                    if ai_messages:
                        # Combine all AIMessage content (there might be multiple)
                        combined_content = "\n\n".join(
                            msg.replace("\\'", "'") for msg in ai_messages
                        )
                        # CRITICAL: Unescape the newlines from the string representation
                        combined_content = combined_content.replace(
                            "\\n", "\n"
                        ).replace("\\t", "\t")
                        self.logger.debug(
                            f"DEBUG: Extracted {len(ai_messages)} AIMessage(s): {combined_content[:200]}..."
                        )
                        return combined_content

                # Fallback: Parse individual message patterns
                if "HumanMessage(content=" in agent_output:
                    # Extract content from HumanMessage format
                    import re

                    self.logger.debug("DEBUG: Found HumanMessage pattern")

                    content_match = re.search(
                        r"HumanMessage\(content=[\"'](.*?)[\"'](?:,|\))",
                        agent_output,
                        re.DOTALL,
                    )
                    if content_match:
                        extracted = content_match.group(1)
                        self.logger.debug(
                            f"DEBUG: Extracted from HumanMessage: {extracted[:200]}..."
                        )
                        return extracted

                # Check for AIMessage content as well
                if "AIMessage(content=" in agent_output:
                    import re

                    self.logger.debug("DEBUG: Found AIMessage pattern")
                    # Look for AIMessage content with more flexible regex
                    ai_content_match = re.search(
                        r"AIMessage\(content='([^']*(?:''[^']*)*)'",
                        agent_output,
                        re.DOTALL,
                    )
                    if ai_content_match:
                        extracted = ai_content_match.group(1).replace("\\'", "'")
                        self.logger.debug(
                            f"DEBUG: Extracted from AIMessage: {extracted[:200]}..."
                        )
                        return extracted

                # If it's already plain content, return as-is
                self.logger.debug("DEBUG: Using raw string content")
                return agent_output

            # Handle actual message objects
            elif hasattr(agent_output, "content"):
                self.logger.debug("DEBUG: Extracting from object.content")
                return agent_output.content
            elif isinstance(agent_output, dict) and "content" in agent_output:
                self.logger.debug("DEBUG: Extracting from dict['content']")
                return agent_output["content"]
            elif isinstance(agent_output, dict) and "messages" in agent_output:
                # Extract from messages list
                self.logger.debug("DEBUG: Extracting from dict['messages']")
                messages = agent_output["messages"]
                if messages and hasattr(messages[-1], "content"):
                    return messages[-1].content

            # Fallback to string conversion
            self.logger.debug("DEBUG: Using fallback string representation")
            return str(agent_output)

        except Exception as e:
            self.logger.warning(f"Failed to extract content from agent output: {e}")
            return str(agent_output)

    async def _parse_files_from_content(
        self, content: str, agent_role: str | None = None
    ) -> list[dict[str, str]]:
        """Parse files from agent response content using comprehensive modern patterns"""
        # Use config default if agent_role not specified - NO HARDCODED VALUES
        if agent_role is None:
            agent_role = self.ConfigManager().status_values.agents["unknown_role"]

        files = []

        self.logger.debug(f"DEBUG: Parsing files from content for {agent_role}")
        self.logger.debug(f"DEBUG: Content length: {len(content)} chars")
        self.logger.debug(f"DEBUG: Content preview: {content[:500]}...")

        # Pattern 0A: NEW - JSON deliverables format (PRIORITY PATTERN)
        try:
            import json
            import re

            # Look for JSON objects with deliverables array - multiple patterns
            json_patterns = [
                # Pattern 1: Plain JSON format
                r'\{\s*["\']?deliverables["\']?\s*:\s*\[(.*?)\]\s*\}',
                # Pattern 2: Markdown-wrapped JSON format
                r'```json\s*\n\{\s*["\']?deliverables["\']?\s*:\s*\[(.*?)\]\s*\}\s*```',
                # Pattern 3: More flexible JSON matching
                r'\{\s*["\']deliverables["\']\s*:\s*\[([^}]*?)\]\s*\}',
            ]

            for pattern in json_patterns:
                json_matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

                for json_match in json_matches:
                    try:
                        # Get the full JSON content
                        json_content = json_match.group(0)

                        # Strip markdown wrapper if present
                        if json_content.startswith("```json"):
                            json_content = (
                                json_content.replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )

                        self.logger.debug(
                            f"DEBUG: Found JSON deliverables: {json_content[:200]}..."
                        )

                        # Try to clean up the JSON content for parsing
                        # Handle common escape issues
                        cleaned_json = json_content

                        # Try parsing the JSON directly first
                        try:
                            deliverables_data = json.loads(cleaned_json)
                        except json.JSONDecodeError:
                            # If direct parsing fails, try to fix common issues
                            # Replace problematic escape sequences
                            cleaned_json = cleaned_json.replace("\\n", "\\\\n")
                            cleaned_json = cleaned_json.replace("\\t", "\\\\t")
                            cleaned_json = cleaned_json.replace('\\"', '\\\\"')
                            try:
                                deliverables_data = json.loads(cleaned_json)
                            except json.JSONDecodeError:
                                # Last resort: manual parsing for our specific structure
                                self.logger.debug(
                                    "DEBUG: JSON parsing failed, trying manual extraction"
                                )
                                continue

                        if "deliverables" in deliverables_data:
                            for deliverable in deliverables_data["deliverables"]:
                                if (
                                    isinstance(deliverable, dict)
                                    and "file_pattern" in deliverable
                                    and "content" in deliverable
                                ):
                                    filename = deliverable["file_pattern"]
                                    file_content = deliverable["content"]

                                    # Clean up file content - handle escaped sequences
                                    if isinstance(file_content, str):
                                        file_content = file_content.replace("\\n", "\n")
                                        file_content = file_content.replace("\\t", "\t")
                                        file_content = file_content.replace('\\"', '"')
                                        file_content = file_content.replace(
                                            "\\\\", "\\"
                                        )

                                    # Extract language from file extension
                                    language = self._detect_language_from_extension(
                                        filename
                                    )

                                    self.logger.debug(
                                        f"DEBUG: JSON Pattern - filename: {filename}, language: {language}"
                                    )

                                    files.append(
                                        {
                                            "filename": filename,
                                            "content": file_content,
                                            "language": language,
                                            "agent": agent_role,
                                        }
                                    )

                    except json.JSONDecodeError as e:
                        self.logger.debug(
                            f"DEBUG: Failed to parse JSON deliverables: {e}"
                        )
                        continue
                    except Exception as e:
                        self.logger.debug(f"DEBUG: Error processing deliverables: {e}")
                        continue

        except Exception as e:
            self.logger.debug(f"DEBUG: Error in JSON deliverables parsing: {e}")

        # Alternative approach: Manual pattern extraction for JSON-like structures
        try:
            # Enhanced manual pattern - look for deliverables with file_pattern and content fields
            # More robust pattern that handles various formats
            deliverable_patterns = [
                # Pattern 1: Full content field
                r'"file_pattern"\s*:\s*"([^"]+)".*?"content"\s*:\s*"((?:[^"\\]|\\.)*)"',
                # Pattern 2: Content with triple quotes or other delimiters
                r'"file_pattern"\s*:\s*"([^"]+)".*?"content"\s*:\s*"""(.*?)"""',
                # Pattern 3: Content with single quotes
                r'"file_pattern"\s*:\s*"([^"]+)".*?"content"\s*:\s*\'((?:[^\'\\]|\\.)*)\'',
            ]

            for pattern in deliverable_patterns:
                deliverable_matches = re.finditer(
                    pattern, content, re.DOTALL | re.IGNORECASE
                )

                for match in deliverable_matches:
                    filename = match.group(1)
                    file_content = match.group(2)

                    # Clean up file content - handle escaped sequences
                    file_content = file_content.replace("\\n", "\n")
                    file_content = file_content.replace("\\t", "\t")
                    file_content = file_content.replace('\\"', '"')
                    file_content = file_content.replace("\\\\", "\\")

                    # Extract language from file extension
                    language = self._detect_language_from_extension(filename)

                    self.logger.debug(
                        f"DEBUG: Manual Pattern - filename: {filename}, language: {language}"
                    )

                    files.append(
                        {
                            "filename": filename,
                            "content": file_content,
                            "language": language,
                            "agent": agent_role,
                        }
                    )

        except Exception as e:
            self.logger.debug(f"DEBUG: Error in manual deliverables parsing: {e}")

        # Pattern 0: Explicit file creation statements
        created_file_pattern = r"\s*I have created the file\s+([^\s]+)\s+with the following content:\s*\n\n```([a-zA-Z]*)\s*\n(.*?)```"
        created_matches = re.finditer(
            created_file_pattern, content, re.DOTALL | re.IGNORECASE
        )

        self.logger.debug(
            f"DEBUG: Testing Pattern 0 against content: {content[:100]}..."
        )

        for match in created_matches:
            filename = match.group(1).strip()
            lang_str = match.group(2).strip()
            language = (
                lang_str
                if lang_str
                else ConfigManager().file_processing.language_defaults[
                    "default_language"
                ]
            )
            file_content = match.group(3).strip()

            self.logger.debug(
                f"DEBUG: Pattern 0 match - filename: {filename}, language: {language}"
            )

            files.append(
                {
                    "filename": filename,
                    "content": file_content,
                    "language": language,
                    "agent": agent_role,
                }
            )

        # Pattern 1: Code blocks with filename prefixes
        filename_pattern = (
            r"(?:File:|Filename:|Name:)\s*([^\n]+)\s*\n\s*```([a-zA-Z]*)\s*\n(.*?)```"
        )
        matches = re.finditer(filename_pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            filename = match.group(1).strip()
            lang_str = match.group(2).strip()
            language = (
                lang_str
                if lang_str
                else ConfigManager().file_processing.language_defaults[
                    "default_language"
                ]
            )
            file_content = match.group(3).strip()

            self.logger.debug(
                f"DEBUG: Pattern 1 match - filename: {filename}, language: {language}"
            )

            files.append(
                {
                    "filename": filename,
                    "content": file_content,
                    "language": language,
                    "agent": agent_role,
                }
            )

        # Pattern 2: FastAPI Application Detection
        fastapi_patterns = [
            (r"```python\s*\n(.*?from fastapi.*?(?:if __name__|$).*?)```", "main.py"),
            (r"```python\s*\n(.*?FastAPI.*?app = FastAPI.*?)```", "main.py"),
            (r"```python\s*\n(.*?@app\.(?:get|post|put|delete).*?)```", "main.py"),
            (
                r"```python\s*\n(.*?APIRouter.*?)```",
                f"routers/{agent_role}.py",
            ),
        ]

        for pattern, default_filename in fastapi_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: FastAPI pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "python",
                        "agent": agent_role,
                    }
                )

        # Pattern 3: SQLAlchemy/Database Models
        database_patterns = [
            (r"```python\s*\n(.*?from sqlalchemy.*?Base\.metadata.*?)```", "models.py"),
            (r"```python\s*\n(.*?class.*?\(Base\).*?)```", "models.py"),
            (r"```python\s*\n(.*?create_async_engine.*?)```", "database.py"),
            (r"```python\s*\n(.*?sessionmaker.*?)```", "database.py"),
        ]

        for pattern, default_filename in database_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: Database pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "python",
                        "agent": agent_role,
                    }
                )

        # Pattern 4: Configuration Files
        config_patterns = [
            (r"```python\s*\n(.*?class.*?Settings.*?BaseSettings.*?)```", "config.py"),
            (
                r"```python\s*\n(.*?from pydantic import BaseSettings.*?)```",
                "config.py",
            ),
            (r"```python\s*\n(.*?JWT_SECRET_KEY.*?)```", "config.py"),
        ]

        for pattern, default_filename in config_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: Config pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "python",
                        "agent": agent_role,
                    }
                )

        # Pattern 5: Authentication & Security
        auth_patterns = [
            (r"```python\s*\n(.*?JWT.*?Token.*?)```", "auth.py"),
            (r"```python\s*\n(.*?OAuth2PasswordBearer.*?)```", "auth.py"),
            (r"```python\s*\n(.*?verify_password.*?)```", "auth.py"),
            (r"```python\s*\n(.*?get_current_user.*?)```", "dependencies.py"),
        ]

        for pattern, default_filename in auth_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: Auth pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "python",
                        "agent": agent_role,
                    }
                )

        # Pattern 6: Docker Files
        docker_patterns = [
            (r"```dockerfile\s*\n(.*?)```", "Dockerfile"),
            (r"```yaml\s*\n(.*?version:.*?services:.*?)```", "docker-compose.yml"),
            (r"```yml\s*\n(.*?version:.*?services:.*?)```", "docker-compose.yml"),
        ]

        for pattern, default_filename in docker_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: Docker pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": (
                            "docker" if "Dockerfile" in default_filename else "yaml"
                        ),
                        "agent": agent_role,
                    }
                )

        # Pattern 7: Requirements and Dependencies
        requirements_patterns = [
            (r"```(?:txt|text)\s*\n(.*?fastapi.*?)```", "requirements.txt"),
            (
                r"```\s*\n((?:.*==.*\n?)+)```",
                "requirements.txt",
            ),  # Version pinned packages
            (
                r"```toml\s*\n(.*?\[tool\.poetry\.dependencies\].*?)```",
                "pyproject.toml",
            ),
        ]

        for pattern, default_filename in requirements_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(
                    f"DEBUG: Requirements pattern match - {default_filename}"
                )
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "text",
                        "agent": agent_role,
                    }
                )

        # Pattern 8: SQL Schema Files
        sql_patterns = [
            (r"```sql\s*\n(.*?)```", "schema.sql"),
            (r"```postgresql\s*\n(.*?)```", "schema.sql"),
        ]

        for pattern, default_filename in sql_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: SQL pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "sql",
                        "agent": agent_role,
                    }
                )

        # Pattern 9: Test Files
        test_patterns = [
            (
                r"```python\s*\n(.*?import pytest.*?)```",
                f"tests/test_{agent_role}.py",
            ),
            (
                r"```python\s*\n(.*?def test_.*?)```",
                f"tests/test_{agent_role}.py",
            ),
            (r"```python\s*\n(.*?TestClient.*?)```", "tests/test_api.py"),
        ]

        for pattern, default_filename in test_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(f"DEBUG: Test pattern match - {default_filename}")
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "python",
                        "agent": agent_role,
                    }
                )

        # Pattern 10: Documentation Files
        doc_patterns = [
            (r"```markdown\s*\n(.*?)```", "README.md"),
            (r"```md\s*\n(.*?)```", "README.md"),
            (r"# (.+)\n\n(.+)", "README.md"),  # Simple markdown content
        ]

        for pattern, default_filename in doc_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    code_content = match.group(1).strip()
                else:
                    code_content = match.group(
                        0
                    ).strip()  # Full match for simple markdown
                if len(code_content) > 50:  # Only create docs for substantial content
                    self.logger.debug(
                        f"DEBUG: Documentation pattern match - {default_filename}"
                    )
                    files.append(
                        {
                            "filename": default_filename,
                            "content": code_content,
                            "language": "markdown",
                            "agent": agent_role,
                        }
                    )

        # Pattern 11: Environment Files
        env_patterns = [
            (r"```env\s*\n(.*?)```", ".env"),
            (r"```\s*\n([A-Z_]+=.*?)```", ".env"),  # Environment variables
        ]

        for pattern, default_filename in env_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                code_content = match.group(1).strip()
                self.logger.debug(
                    f"DEBUG: Environment pattern match - {default_filename}"
                )
                files.append(
                    {
                        "filename": default_filename,
                        "content": code_content,
                        "language": "text",
                        "agent": agent_role,
                    }
                )

        # Pattern 12: COMPREHENSIVE FALLBACK - ANY REMAINING CODE BLOCKS
        # This ensures NO code block is ever ignored
        fallback_pattern = r"```([a-zA-Z]*)\s*\n(.*?)```"
        fallback_matches = re.finditer(
            fallback_pattern, content, re.DOTALL | re.IGNORECASE
        )

        existing_contents = {f["content"] for f in files}
        fallback_count = 0

        for match in fallback_matches:
            lang = match.group(1).strip().lower()
            code_content = match.group(2).strip()

            # Skip if this content was already captured by specific patterns
            if code_content in existing_contents or len(code_content) < 20:
                continue

            fallback_count += 1
            extension = self._get_extension_for_language(lang)
            filename = f"generated_{agent_role}_{fallback_count}.{extension}"

            self.logger.debug(f"DEBUG: Fallback pattern match - {filename}")
            files.append(
                {
                    "filename": filename,
                    "content": code_content,
                    "language": lang,
                    "agent": agent_role,
                }
            )
            existing_contents.add(code_content)

        # Pattern 13: Explicit file sections (keep existing)
        file_section_pattern = r"(?:FILE:|FILENAME:|File:|Filename:)\s*([^\n]+)\n(.*?)(?=(?:FILE:|FILENAME:|File:|Filename:|\Z))"
        matches = re.finditer(file_section_pattern, content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            filename = match.group(1).strip()
            file_content = match.group(2).strip()

            if filename and file_content:
                files.append(
                    {
                        "filename": self._sanitize_filename(filename),
                        "content": file_content,
                        "language": self._detect_language_from_extension(filename),
                        "agent": agent_role,
                    }
                )

        # Remove duplicates based on content similarity
        files = self._deduplicate_files(files)

        self.logger.debug(f"DEBUG: Total files found: {len(files)}")
        for i, file in enumerate(files):
            self.logger.debug(
                f"DEBUG: File {i+1}: {file['filename']} ({len(file['content'])} chars)"
            )

        return files

    def _extract_filename_from_hint(
        self, hint: str, language: str, agent_role: str
    ) -> str | None:
        """Extract filename from various hint formats"""
        if not hint:
            return self._generate_default_filename(language, agent_role)

        # Clean up the hint
        hint = hint.strip().strip("#").strip("//").strip("<!--").strip("-->").strip()

        # If it looks like a filename already
        if "." in hint and len(hint.split()) == 1:
            return self._sanitize_filename(hint)

        # If it's a description, generate filename
        if language:
            extension = self._get_extension_for_language(language)
            safe_hint = re.sub(r"[^\w\s-]", "", hint.lower())
            safe_hint = re.sub(r"\s+", "_", safe_hint)
            return f"{safe_hint}.{extension}"

        return self._generate_default_filename(language, agent_role)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = re.sub(r"\s+", "_", filename)
        filename = filename.strip("._")

        # Ensure it's not empty and has an extension
        if not filename:
            filename = "output.txt"
        elif "." not in filename:
            filename += ".txt"

        return filename

    def _detect_language_from_extension(self, filename: str) -> str:
        """Detect programming language from file extension"""
        extension = Path(filename).suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sql": "sql",
            ".sh": "bash",
            ".dockerfile": "dockerfile",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
        }

        return language_map.get(
            extension,
            ConfigManager().file_processing.language_defaults.get(
                "default_language", "python"
            ),
        )

    def _get_extension_for_language(self, language: str) -> str:
        """Get appropriate file extension for a language"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "yaml": "yml",
            "json": "json",
            "markdown": "md",
            "dockerfile": "dockerfile",
            "bash": "sh",
            "shell": "sh",
            "text": "txt",
            "txt": "txt",
        }
        return extensions.get(language.lower(), "txt")

    def _detect_language_from_extension(self, extension: str) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".txt": "text",
            ".sh": "shell",
            ".bash": "shell",
            ".dockerfile": "dockerfile",
            ".sql": "sql",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".php": "php",
            ".rb": "ruby",
        }
        return extension_map.get(extension.lower(), "text")

    async def _extract_files_from_structured_response(
        self, agent_result: Any, agent_role: str
    ) -> list[dict[str, Any]]:
        """
        Extract files from structured AgentResponse format.
        NO FALLBACKS - must succeed or fail completely.
        """
        self.logger.debug(f"🔒 Parsing structured response from {agent_role}")

        # Import the response model for validation
        from src.applications.oamat_sd.src.models.agent_response_models import (
            AgentResponse,
        )

        try:
            # Handle different response formats from LangGraph
            if isinstance(agent_result, dict):
                if "messages" in agent_result:
                    # Extract from LangGraph message format
                    content = self._extract_content_from_agent_output(agent_result)
                else:
                    # Direct dict response
                    content = agent_result
            elif isinstance(agent_result, str):
                # String response - try to parse as JSON
                import json

                content = json.loads(agent_result)
            else:
                # Assume it's already a structured object
                content = agent_result

            # Validate against AgentResponse schema
            if isinstance(content, str):
                import json

                parsed_content = json.loads(content)
            else:
                parsed_content = content

            # Validate the structure
            agent_response = AgentResponse(**parsed_content)

            # Extract files from the validated response
            files = []
            for generated_file in agent_response.deliverables.generated_files:
                file_info = {
                    "filename": generated_file.filename,
                    "content": generated_file.content,
                    "file_type": generated_file.file_type,
                    "description": generated_file.description,
                }
                files.append(file_info)

            self.logger.info(
                f"✅ {agent_role}: Extracted {len(files)} files from structured response"
            )

            # Log success status
            if agent_response.deliverables.success_status:
                self.logger.info(f"✅ {agent_role}: Reported successful completion")
            else:
                self.logger.warning(
                    f"⚠️ {agent_role}: Reported unsuccessful completion"
                )

            return files

        except Exception as e:
            self.logger.error(
                f"Failed to parse structured response from {agent_role}: {e}"
            )
            self.logger.debug(f"Raw agent result: {agent_result}")
            raise RuntimeError(
                f"Agent {agent_role} response does not conform to AgentResponse schema. "
                f"Validation error: {e}"
            )

    def _is_json_deliverables_format(self, content: str) -> bool:
        """
        Detect if the content is in JSON deliverables format.
        Expected format: '{"deliverables": [{"filename": "...", "content": "..."}]}'
        """
        try:
            data = json.loads(content.strip())
            if isinstance(data, dict) and "deliverables" in data:
                deliverables = data["deliverables"]
                if isinstance(deliverables, list) and len(deliverables) > 0:
                    # Check if first deliverable has required structure
                    first_item = deliverables[0]
                    if (
                        isinstance(first_item, dict)
                        and "filename" in first_item
                        and "content" in first_item
                    ):
                        self.logger.debug(
                            f"✅ JSON deliverables format detected with {len(deliverables)} files"
                        )
                        return True
            return False
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
            self.logger.debug(f"Not JSON deliverables format: {e}")
            return False

    async def _extract_files_from_json_deliverables(
        self, content: str
    ) -> list[dict[str, str]]:
        """
        Extract files directly from JSON deliverables format.
        Returns list of dicts with 'filename' and 'content' keys.
        """
        try:
            data = json.loads(content.strip())
            deliverables = data.get("deliverables", [])
            files = []

            self.logger.debug(
                f"🔍 Processing {len(deliverables)} deliverables from JSON format"
            )

            for idx, item in enumerate(deliverables):
                if isinstance(item, dict) and "filename" in item and "content" in item:
                    filename = item["filename"].strip()
                    file_content = item["content"]

                    # Skip empty files
                    if (
                        not filename
                        or not file_content
                        or len(file_content.strip()) == 0
                    ):
                        self.logger.warning(
                            f"Skipping empty deliverable {idx}: {filename}"
                        )
                        continue

                    files.append({"filename": filename, "content": file_content})

                    self.logger.debug(
                        f"✅ Extracted file: {filename} ({len(file_content)} chars)"
                    )
                else:
                    self.logger.warning(
                        f"Invalid deliverable structure at index {idx}: {item}"
                    )

            self.logger.info(
                f"🎯 Successfully extracted {len(files)} files from JSON deliverables"
            )
            return files

        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse JSON deliverables: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error extracting files from JSON deliverables: {e}")
            return []

    def _deduplicate_files(self, files: list[dict[str, str]]) -> list[dict[str, str]]:
        """Remove duplicate files based on content similarity"""
        unique_files = []
        seen_contents = set()

        for file in files:
            # Create a signature for the content (first 100 chars + length)
            content_signature = f"{file['content'][:100]}_{len(file['content'])}"

            if content_signature not in seen_contents:
                unique_files.append(file)
                seen_contents.add(content_signature)
            else:
                self.logger.debug(f"DEBUG: Skipping duplicate file: {file['filename']}")

        return unique_files

    def _generate_default_filename(self, language: str, agent_role: str) -> str:
        """Generate a default filename when one can't be determined"""
        if language:
            extension = self._get_extension_for_language(language)
            return f"{agent_role}_output.{extension}"
        else:
            return f"{agent_role}_output.txt"

    async def _create_project_file(
        self, project_path: Path, filename: str, content: str
    ):
        """Create a file in the project directory"""
        try:
            # Ensure the project directory exists
            project_path.mkdir(parents=True, exist_ok=True)

            # Create the full file path
            file_path = project_path / filename

            # Ensure parent directories exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Successfully created file: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to create file {filename}: {e}")
            raise

    def create_project_context(self, user_request: str) -> tuple[str, Path]:
        """Create project context and directory structure"""
        # Generate project name from user request
        project_name = re.sub(r"[^\w\s-]", "", user_request.lower())
        project_name = re.sub(r"\s+", "_", project_name)[:50]

        if not project_name:
            project_name = "smart_decomposition_project"

        # Create project directory in app root (not project root)
        app_root = Path(
            __file__
        ).parent.parent.parent  # Go up from operations -> src -> oamat_sd
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir_name = f"{project_name}_{timestamp}"
        project_path = app_root / "projects" / project_dir_name

        try:
            project_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"📁 Creating project directory: {project_path}")

            # Create basic project structure
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "docs").mkdir(exist_ok=True)

            self.logger.info(f"✅ Project context created: {project_path.absolute()}")
            self.logger.info(
                "📁 Project structure: src/, docs/, and logs/ (created when logging starts)"
            )

        except Exception as e:
            self.logger.error(f"❌ Error creating project directory: {e}")
            raise

        self.logger.info(f"🎯 Project initialized for request: {user_request[:100]}...")

        return project_dir_name, project_path
