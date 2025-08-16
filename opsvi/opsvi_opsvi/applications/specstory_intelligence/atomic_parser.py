"""
Atomic SpecStory Parser
Implements complete atomic decomposition per SPECSTORY_FORMAT_SCHEMA.md
Breaks down SpecStory files into 15 atomic component types with full relationships
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Tuple
import uuid


# Reference: docs/applications/agent_intelligence_pipeline.md (authoritative schema)
class ComponentType(Enum):
    SESSION_HEADER = "session_header"
    CONVERSATION_TURN = "conversation_turn"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CODE_BLOCK = "code_block"
    FILE_REFERENCE = "file_reference"
    ERROR_MESSAGE = "error_message"
    EXPLICIT_REASONING_BLOCK = "explicit_reasoning_block"
    PROVENANCE_COMMENT = "provenance_comment"
    FILE_METADATA = "file_metadata"
    # New granular turn types
    USER_TURN = "user_turn"
    ASSISTANT_TURN = "assistant_turn"
    QUESTION = "question"
    ANSWER = "answer"
    # All other types are deprecated and removed for minimal atomic schema


class RelationshipType(Enum):
    """Relationship types per schema"""

    # Temporal
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    SIMULTANEOUS = "simultaneous"

    # Containment
    CONTAINS = "contains"
    PART_OF = "part_of"
    NESTED_IN = "nested_in"

    # Causal
    TRIGGERS = "triggers"
    CAUSES = "causes"
    RESULTS_IN = "results_in"

    # Reference
    REFERENCES = "references"
    MENTIONS = "mentions"
    DEPENDS_ON = "depends_on"

    # Semantic
    ANSWERS = "answers"
    EXPLAINS = "explains"
    SOLVES = "solves"


@dataclass
class ComponentBoundaries:
    """Exact positioning information for reconstruction"""

    start_line: int
    end_line: int
    start_char: int
    end_char: int
    absolute_char_start: int
    absolute_char_end: int


@dataclass
class AtomicComponent:
    """Universal atomic component structure"""

    component_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_type: ComponentType = None

    # Positioning
    boundaries: ComponentBoundaries = None
    turn_sequence: Optional[int] = None
    component_sequence: int = 0
    nesting_level: int = 0

    # Content
    raw_content: str = ""
    processed_content: Dict = field(default_factory=dict)
    formatting: Dict = field(default_factory=dict)

    # Metadata
    session_id: str = ""
    session_title: str = ""
    session_timestamp: Optional[datetime] = None
    extraction_confidence: float = 1.0
    validation_errors: List[str] = field(default_factory=list)

    # Analysis
    analysis: Dict = field(default_factory=dict)

    # Graph metadata
    graph_metadata: Dict = field(default_factory=dict)

    # Reconstruction
    reconstruction: Dict = field(default_factory=dict)

    def to_arango_document(self) -> Dict:
        """Convert to ArangoDB document format"""
        return {
            "_key": self.component_id,
            "component_type": self.component_type.value,
            "positioning": {
                "file_path": getattr(self, "file_path", ""),
                "line_start": self.boundaries.start_line if self.boundaries else 0,
                "line_end": self.boundaries.end_line if self.boundaries else 0,
                "char_start": self.boundaries.start_char if self.boundaries else 0,
                "char_end": self.boundaries.end_char if self.boundaries else 0,
                "turn_sequence": self.turn_sequence,
                "component_sequence": self.component_sequence,
                "nesting_level": self.nesting_level,
            },
            "content": {
                "raw_content": self.raw_content,
                "processed_content": self.processed_content,
                "formatting": self.formatting,
            },
            "metadata": {
                "session_id": self.session_id,
                "session_title": self.session_title,
                "session_timestamp": (
                    self.session_timestamp.isoformat()
                    if self.session_timestamp
                    else None
                ),
                "extraction_confidence": self.extraction_confidence,
                "validation_errors": self.validation_errors,
                "processing_timestamp": datetime.utcnow().isoformat(),
            },
            "analysis": self.analysis,
            "graph_data": self.graph_metadata,
            "reconstruction": self.reconstruction,
        }


@dataclass
class AtomicRelationship:
    """Relationship between atomic components"""

    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    relationship_type: RelationshipType = None
    source_component_id: str = ""
    target_component_id: str = ""

    # Temporal data
    sequence_distance: int = 0
    time_distance: float = 0.0
    temporal_order: int = 0

    # Semantic data
    relevance_score: float = 1.0
    confidence: float = 1.0
    relationship_strength: float = 1.0

    # Context
    context: Dict = field(default_factory=dict)

    def to_arango_edge(self) -> Dict:
        """Convert to ArangoDB edge format"""
        return {
            "_key": self.relationship_id,
            "_from": f"specstory_components/{self.source_component_id}",
            "_to": f"specstory_components/{self.target_component_id}",
            "relationship_type": self.relationship_type.value,
            "temporal_data": {
                "sequence_distance": self.sequence_distance,
                "time_distance": self.time_distance,
                "temporal_order": self.temporal_order,
            },
            "semantic_data": {
                "relevance_score": self.relevance_score,
                "confidence": self.confidence,
                "relationship_strength": self.relationship_strength,
            },
            "context": self.context,
            "metadata": {
                "extraction_method": "automated",
                "validation_status": "validated",
                "created_timestamp": datetime.utcnow().isoformat(),
            },
        }


logger = logging.getLogger("atomic_parser")
logger.setLevel(logging.DEBUG)  # Enable debug logging by default
# Ensure debug logs are shown in the terminal
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class AtomicAnalysis:
    @staticmethod
    def analyze_turn_content(patterns, lines: List[str]) -> Dict:
        content = "\n".join(lines)
        return {
            "contains_tools": "<function_calls>" in content
            or "<function_results>" in content,
            "contains_code": "```" in content,
            "contains_thinking": "<think>" in content,
            "contains_urls": bool(patterns["http_url"].search(content))
            if "http_url" in patterns
            else False,
            "complexity_score": len(content.split()) / 100.0,
        }

    @staticmethod
    def classify_output_type(content: str) -> str:
        content_lower = content.lower()
        if "contents of" in content_lower and "lines" in content_lower:
            return "file_content"
        elif "directory" in content_lower or "contents of directory" in content_lower:
            return "directory_listing"
        elif any(cmd in content_lower for cmd in ["command output", "exit code", "$"]):
            return "command_output"
        elif any(
            error in content_lower
            for error in ["error", "exception", "traceback", "failed"]
        ):
            return "error"
        elif any(
            format_type in content_lower
            for format_type in ["json", "xml", "yaml", "csv"]
        ):
            return "structured_data"
        else:
            return "text_data"

    @staticmethod
    def analyze_code_block(language: str, content: str) -> Dict:
        lines = content.split("\n")
        return {
            "syntax_valid": True,
            "contains_imports": any(
                "import " in line or "from " in line for line in lines
            ),
            "contains_functions": any(
                "def " in line or "function" in line for line in lines
            ),
            "contains_comments": any(
                line.strip().startswith("#") or line.strip().startswith("//")
                for line in lines
            ),
            "executable": language in ["python", "bash", "javascript"],
            "complexity_score": len(lines) / 10.0,
            "line_count": len(lines),
        }


class AtomicSpecStoryParser:
    """Complete atomic decomposition parser"""

    def __init__(self):
        self.components: List[AtomicComponent] = []
        self.relationships: List[AtomicRelationship] = []
        self.current_session_id = ""
        self.current_turn_sequence = 0
        self.current_component_sequence = 0

        # Compiled regex patterns for performance
        self._compile_patterns()
        logger.debug("AtomicSpecStoryParser initialized.")

    def _compile_patterns(self):
        """Pre-compile all regex patterns (extended for catalog types)"""
        self.patterns = {
            # Minimal atomic parser patterns
            "header_comment": re.compile(r"^<!-- Generated by.*?-->", re.IGNORECASE),
            "provenance_comment": re.compile(
                r"^<!--.*?generated.*?by.*?-->", re.IGNORECASE
            ),
            "title_line": re.compile(r"^# (.+?) \\((.+?)\\)"),
            "turn_separator": re.compile(r"^---"),
            "tool_call": re.compile(r'<function_calls>|<invoke name="[^"]+">'),
            "tool_result": re.compile(r"<function_results>|<result>"),
            "code_block": re.compile(r"^```(\w*)$"),
            "file_reference": re.compile(r"`([^`]+\.[a-zA-Z]+)`"),
            "error_message": re.compile(r"(Error:|ERROR:|Failed:|Exception:)(.*)"),
            "explicit_reasoning_block": re.compile(
                r"\*\*(?:Action/Reasoning/Output|Plan & Reasoning|Next Steps):\*\*",
                re.IGNORECASE,
            ),
            # Added missing patterns for tool results and file entries
            "function_results_end": re.compile(r"</function_results>|</result>"),
            "result_block": re.compile(
                r"<result name=\"([^\"]+)\">(.*?)</result>", re.DOTALL
            ),
            "file_entry": re.compile(r"([\w\-.\/]+\.[a-zA-Z0-9]+)"),
            # Add missing patterns
            "code_block_start": re.compile(r"^```(\w*)"),
            "code_block_end": re.compile(r"^```$"),
            "speaker_marker": re.compile(r"^_\*\*(User|Assistant)\*\*_"),
            # NEW: Provenance and metadata
            "provenance_comment": re.compile(
                r"^<!--.*?generated.*?by.*?-->", re.IGNORECASE
            ),
            "file_metadata": re.compile(r"^# (.+?) \\((.+?)\\)"),
            # Block markers and collapsible/expandable blocks
            "details_block_start": re.compile(r"^<details>(.*)$", re.IGNORECASE),
            "summary_block": re.compile(r"^<summary>(.*?)</summary>$", re.IGNORECASE),
            "details_block_end": re.compile(r"^</details>$", re.IGNORECASE),
            "think_block_start": re.compile(r"^<think>(.*)$", re.IGNORECASE),
            "think_block_end": re.compile(r"^</think>$", re.IGNORECASE),
            # Directory listings and markdown tables
            "directory_listing": re.compile(
                r"^\s*([\w\-.\/]+)\s+(dir|directory|file|\d+ bytes|\d+)$", re.IGNORECASE
            ),
            "markdown_table": re.compile(r"^\|(.+)\|$"),
            # Summary/conclusion blocks
            "summary_block": re.compile(
                r"\*\*(Summary|Conclusion):\*\*", re.IGNORECASE
            ),
            # Intent/conceptual tags
            "intent_tag": re.compile(r"\[intent:([\w\-]+)\]", re.IGNORECASE),
            "focus_tag": re.compile(r"\[focus:([\w\-]+)\]", re.IGNORECASE),
            "action_tag": re.compile(r"\[action:([\w\-]+)\]", re.IGNORECASE),
            "reflection_tag": re.compile(r"\[reflection:([\w\-]+)\]", re.IGNORECASE),
        }

    def _get_pattern_dispatch_table(self):
        """Return a dispatch table mapping pattern names to handler methods."""
        return [
            ("header_comment", self._parse_session_header),
            ("turn_separator", self._parse_conversation_turn),
            ("tool_call", self._parse_tool_calls),
            ("tool_result", self._parse_tool_results),
            ("code_block", self._parse_code_block),
            ("file_reference", self._parse_file_references),
            ("error_message", self._extract_error_message),
            ("explicit_reasoning_block", self._parse_explicit_reasoning),
        ]

    async def parse_file(
        self, filepath: str
    ) -> Tuple[List[AtomicComponent], List[AtomicRelationship]]:
        logger.debug(f"Parsing file: {filepath}")
        self.components = []
        self.relationships = []
        self.current_component_sequence = 0
        self.current_turn_sequence = 0

        # Read file content
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"Read {len(content)} characters from {filepath}")

        lines = content.split("\n")
        logger.debug(f"File split into {len(lines)} lines")

        # --- Provenance/Generation Comment Extraction ---
        if lines and self.patterns["provenance_comment"].match(lines[0]):
            logger.debug("Found provenance comment in first line.")
            provenance_component = AtomicComponent(
                component_type=ComponentType.PROVENANCE_COMMENT,
                boundaries=ComponentBoundaries(
                    0, 0, 0, len(lines[0]), 0, len(lines[0])
                ),
                raw_content=lines[0],
                processed_content={"provenance": lines[0]},
                analysis={"type": "provenance_comment"},
            )
            self._add_component_metadata(provenance_component)
            self.components.append(provenance_component)

        # --- File Metadata Extraction (from header/title) ---
        if len(lines) > 1 and self.patterns["file_metadata"].match(lines[1]):
            meta_match = self.patterns["file_metadata"].match(lines[1])
            session_title = meta_match.group(1)
            timestamp_str = meta_match.group(2)
            try:
                session_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%MZ")
            except ValueError:
                session_timestamp = datetime.utcnow()
            file_metadata_component = AtomicComponent(
                component_type=ComponentType.FILE_METADATA,
                boundaries=ComponentBoundaries(
                    1, 1, 0, len(lines[1]), len(lines[0]), len(lines[0]) + len(lines[1])
                ),
                raw_content=lines[1],
                processed_content={
                    "session_title": session_title,
                    "timestamp": timestamp_str,
                    "filename": str(filepath),
                },
                analysis={"type": "file_metadata"},
            )
            self._add_component_metadata(file_metadata_component)
            self.components.append(file_metadata_component)

        # Continue with session header and rest of parsing as before
        session_header = self._parse_session_header(lines[:3])
        if session_header:
            self.current_session_id = session_header.component_id
            self.components.append(session_header)

        # Parse document line by line using dispatch table
        current_line = 0
        absolute_char_pos = 0
        dispatch_table = self._get_pattern_dispatch_table()

        while current_line < len(lines):
            line = lines[current_line]
            line_start_char = absolute_char_pos
            absolute_char_pos += len(line) + 1  # +1 for newline

            matched = False
            for pattern_name, handler in dispatch_table:
                pattern = self.patterns.get(pattern_name)
                if pattern and pattern.search(line):
                    if handler == self._parse_session_header:
                        session_header = handler(lines[:3])
                        if session_header:
                            self.components.append(session_header)
                            current_line += 1
                            matched = True
                            break
                    elif handler == self._parse_conversation_turn:
                        turn_component, lines_consumed = handler(
                            lines, current_line, line_start_char
                        )
                        if turn_component:
                            self.components.append(turn_component)
                            current_line += lines_consumed
                            matched = True
                            break
                    elif handler == self._parse_tool_calls:
                        tool_components, lines_consumed = handler(
                            lines, current_line, line_start_char
                        )
                        self.components.extend(tool_components)
                        current_line += lines_consumed
                        matched = True
                        break
                    elif handler == self._parse_tool_results:
                        result_components, lines_consumed = handler(
                            lines, current_line, line_start_char
                        )
                        self.components.extend(result_components)
                        current_line += lines_consumed
                        matched = True
                        break
                    elif handler == self._parse_code_block:
                        code_component, lines_consumed = handler(
                            lines, current_line, line_start_char
                        )
                        if code_component:
                            self.components.append(code_component)
                            current_line += lines_consumed
                            matched = True
                            break
                    elif handler == self._parse_file_references:
                        file_refs = handler(line, current_line, line_start_char)
                        self.components.extend(file_refs)
                        current_line += 1
                        matched = True
                        break
                    elif handler == self._extract_error_message:
                        error_component = handler(line, current_line, line_start_char)
                        if error_component:
                            self.components.append(error_component)
                            current_line += 1
                            matched = True
                            break
                    elif handler == self._parse_explicit_reasoning:
                        reasoning_component, lines_consumed = handler(
                            lines, current_line, line_start_char
                        )
                        if reasoning_component:
                            self.components.append(reasoning_component)
                            current_line += lines_consumed
                            matched = True
                            break
            if not matched:
                current_line += 1

        # Generate relationships
        self._generate_relationships()

        logger.debug(
            f"Parsed {len(self.components)} components and {len(self.relationships)} relationships from {filepath}"
        )
        logger.debug(f"Component types: {[c.component_type for c in self.components]}")
        logger.debug(
            f"Returning components type: {type(self.components)}; relationships type: {type(self.relationships)}"
        )
        return self.components, self.relationships

    def _parse_session_header(
        self, header_lines: List[str]
    ) -> Optional[AtomicComponent]:
        """Parse session header component"""
        if len(header_lines) < 2:
            return None

        # Validate header comment
        if not self.patterns["header_comment"].match(header_lines[0]):
            return None

        # Parse title line
        title_match = self.patterns["title_line"].match(header_lines[1])
        if not title_match:
            return None

        session_title = title_match.group(1)
        timestamp_str = title_match.group(2)

        try:
            session_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%MZ")
        except ValueError:
            session_timestamp = datetime.utcnow()

        component = AtomicComponent(
            component_type=ComponentType.SESSION_HEADER,
            boundaries=ComponentBoundaries(
                0,
                1,
                0,
                len(header_lines[1]),
                0,
                len(header_lines[0]) + len(header_lines[1]) + 2,
            ),
            raw_content="\n".join(header_lines[:2]),
            session_title=session_title,
            session_timestamp=session_timestamp,
            processed_content={
                "generator": "SpecStory",
                "session_title": session_title,
                "timestamp": timestamp_str,
                "derived_date": timestamp_str.split(" ")[0],
                "derived_time": timestamp_str.split(" ")[1].replace("Z", ""),
            },
            analysis={
                "word_count": len(session_title.split()),
                "character_count": len(session_title),
                "complexity_score": 0.1,
            },
            graph_metadata={
                "node_type": "session_header",
                "temporal_order": 0,
                "relationships": ["contains_turns", "has_metadata"],
            },
        )

        self._add_component_metadata(component)
        return component

    def _parse_conversation_turn(
        self, lines: List[str], start_line: int, start_char: int
    ) -> Tuple[Optional[AtomicComponent], int]:
        """Parse complete conversation turn and emit granular turn types"""
        speaker_match = self.patterns["speaker_marker"].match(lines[start_line])
        if not speaker_match:
            return None, 0

        speaker = speaker_match.group(1)
        self.current_turn_sequence += 1

        # Find turn end (next speaker marker or document end)
        end_line = start_line + 1
        turn_content_lines = []

        while end_line < len(lines):
            line = lines[end_line]
            if self.patterns["speaker_marker"].match(line) or self.patterns[
                "turn_separator"
            ].match(line):
                break
            turn_content_lines.append(line)
            end_line += 1

        # Calculate boundaries
        raw_content = "\n".join([lines[start_line]] + turn_content_lines)
        end_char = start_char + len(raw_content)

        # Analyze turn content
        content_analysis = self._analyze_turn_content(turn_content_lines)

        # Extract intent/conceptual tags from turn content
        tags = []
        for tag_type in ["intent_tag", "focus_tag", "action_tag", "reflection_tag"]:
            for i, line in enumerate(turn_content_lines):
                match = self.patterns[tag_type].search(line)
                if match:
                    tags.append(
                        {
                            "type": tag_type,
                            "value": match.group(1),
                            "line": i + start_line + 1,
                        }
                    )

        # Determine granular turn type
        turn_type = None
        if speaker.lower() == "user":
            turn_type = ComponentType.USER_TURN
        elif speaker.lower() == "assistant":
            turn_type = ComponentType.ASSISTANT_TURN
        else:
            turn_type = ComponentType.CONVERSATION_TURN

        # Detect question/answer
        content_raw = "\n".join(turn_content_lines).strip()
        is_question = content_raw.endswith("?") or any(
            content_raw.lower().startswith(qw)
            for qw in ["how ", "why ", "what ", "when ", "where ", "who ", "which "]
        )
        is_answer = not is_question and len(content_raw) > 0

        # Emit CONVERSATION_TURN (backward compatibility)
        component = AtomicComponent(
            component_type=ComponentType.CONVERSATION_TURN,
            boundaries=ComponentBoundaries(
                start_line, end_line - 1, start_char, end_char, start_char, end_char
            ),
            turn_sequence=self.current_turn_sequence,
            raw_content=raw_content,
            processed_content={
                "speaker": speaker,
                "turn_sequence": self.current_turn_sequence,
                "content_raw": content_raw,
                "tags": tags,
            },
            analysis={
                "word_count": len(" ".join(turn_content_lines).split()),
                "character_count": len(raw_content),
                "line_count": len(turn_content_lines),
                **content_analysis,
            },
            graph_metadata={
                "node_type": "conversation_turn",
                "relationships": ["follows_turn", "contains_content", "has_speaker"],
            },
        )
        self._add_component_metadata(component)
        self.components.append(component)

        # Emit granular turn type (user_turn/assistant_turn)
        granular_component = AtomicComponent(
            component_type=turn_type,
            boundaries=ComponentBoundaries(
                start_line, end_line - 1, start_char, end_char, start_char, end_char
            ),
            turn_sequence=self.current_turn_sequence,
            raw_content=raw_content,
            processed_content={
                "speaker": speaker,
                "turn_sequence": self.current_turn_sequence,
                "content_raw": content_raw,
                "tags": tags,
            },
            analysis={
                "word_count": len(" ".join(turn_content_lines).split()),
                "character_count": len(raw_content),
                "line_count": len(turn_content_lines),
                **content_analysis,
            },
            graph_metadata={
                "node_type": turn_type.value,
                "relationships": ["follows_turn", "contains_content", "has_speaker"],
            },
        )
        self._add_component_metadata(granular_component)
        self.components.append(granular_component)

        # Emit question/answer nodes if detected
        if is_question:
            question_component = AtomicComponent(
                component_type=ComponentType.QUESTION,
                boundaries=ComponentBoundaries(
                    start_line, end_line - 1, start_char, end_char, start_char, end_char
                ),
                turn_sequence=self.current_turn_sequence,
                raw_content=raw_content,
                processed_content={
                    "speaker": speaker,
                    "turn_sequence": self.current_turn_sequence,
                    "content_raw": content_raw,
                    "tags": tags,
                },
                analysis={
                    "word_count": len(" ".join(turn_content_lines).split()),
                    "character_count": len(raw_content),
                    "line_count": len(turn_content_lines),
                    **content_analysis,
                },
                graph_metadata={
                    "node_type": "question",
                    "relationships": ["asks"],
                },
            )
            self._add_component_metadata(question_component)
            self.components.append(question_component)
        elif is_answer:
            answer_component = AtomicComponent(
                component_type=ComponentType.ANSWER,
                boundaries=ComponentBoundaries(
                    start_line, end_line - 1, start_char, end_char, start_char, end_char
                ),
                turn_sequence=self.current_turn_sequence,
                raw_content=raw_content,
                processed_content={
                    "speaker": speaker,
                    "turn_sequence": self.current_turn_sequence,
                    "content_raw": content_raw,
                    "tags": tags,
                },
                analysis={
                    "word_count": len(" ".join(turn_content_lines).split()),
                    "character_count": len(raw_content),
                    "line_count": len(turn_content_lines),
                    **content_analysis,
                },
                graph_metadata={
                    "node_type": "answer",
                    "relationships": ["answers"],
                },
            )
            self._add_component_metadata(answer_component)
            self.components.append(answer_component)

        # Parse nested content within the conversation turn
        nested_components = self._parse_nested_content(
            turn_content_lines, start_line + 1, start_char
        )
        self.components.extend(nested_components)

        # Create containment relationships for nested components
        for nested_comp in nested_components:
            contains_rel = AtomicRelationship(
                relationship_type=RelationshipType.CONTAINS,
                source_component_id=component.component_id,
                target_component_id=nested_comp.component_id,
                confidence=1.0,
                context={"nested_in": "conversation_turn"},
            )
            self.relationships.append(contains_rel)

        return component, end_line - start_line

    def _parse_block(
        self,
        lines,
        start_line,
        start_char,
        block_type,
        start_pattern,
        end_pattern,
        component_type,
        processed_content_key=None,
    ):
        """Generic block parser for code, details, think, summary, etc."""
        if not start_pattern.match(lines[start_line]):
            return None, 1
        block_lines = [lines[start_line]]
        end_line = start_line + 1
        while end_line < len(lines):
            block_lines.append(lines[end_line])
            if end_pattern.match(lines[end_line]):
                break
            end_line += 1
        raw_content = "\n".join(block_lines)
        component = AtomicComponent(
            component_type=component_type,
            boundaries=ComponentBoundaries(
                start_line,
                end_line,
                start_char,
                start_char + len(raw_content),
                start_char,
                start_char + len(raw_content),
            ),
            raw_content=raw_content,
            processed_content={
                "block_type": block_type,
                processed_content_key or "content": raw_content,
            },
            analysis={"lines": len(block_lines)},
        )
        self._add_component_metadata(component)
        return component, end_line - start_line + 1

    def _parse_nested_content(
        self, lines: List[str], start_line_offset: int, start_char_offset: int
    ) -> List[AtomicComponent]:
        """Parse nested content within conversation turns (extended for block markers)"""
        nested_components = []
        current_line = 0
        absolute_char_pos = start_char_offset
        while current_line < len(lines):
            line = lines[current_line]
            line_start_char = absolute_char_pos
            absolute_char_pos += len(line) + 1  # +1 for newline

            # Generic block parsing
            for block_type, (start_pat, end_pat, comp_type, key) in [
                (
                    "details",
                    (
                        self.patterns["details_block_start"],
                        self.patterns["details_block_end"],
                        ComponentType.EXPLICIT_REASONING_BLOCK,
                        None,
                    ),
                ),
                (
                    "think",
                    (
                        self.patterns["think_block_start"],
                        self.patterns["think_block_end"],
                        ComponentType.EXPLICIT_REASONING_BLOCK,
                        None,
                    ),
                ),
                (
                    "code",
                    (
                        self.patterns["code_block_start"],
                        self.patterns["code_block_end"],
                        ComponentType.CODE_BLOCK,
                        "content",
                    ),
                ),
            ]:
                if start_pat.match(line):
                    component, lines_consumed = self._parse_block(
                        lines,
                        current_line,
                        line_start_char,
                        block_type,
                        start_pat,
                        end_pat,
                        comp_type,
                        key,
                    )
                    if component:
                        nested_components.append(component)
                        current_line += lines_consumed
                        break
            else:
                # Parse other types as before
                if self.patterns["tool_call"].search(line):
                    tool_components, lines_consumed = self._parse_tool_calls(
                        lines, current_line, line_start_char
                    )
                    nested_components.extend(tool_components)
                    current_line += lines_consumed
                    continue
                elif self.patterns["tool_result"].search(line):
                    result_components, lines_consumed = self._parse_tool_results(
                        lines, current_line, line_start_char
                    )
                    nested_components.extend(result_components)
                    current_line += lines_consumed
                    continue
                elif self.patterns["file_reference"].search(line):
                    file_refs = self._parse_file_references(
                        line, current_line + start_line_offset, line_start_char
                    )
                    nested_components.extend(file_refs)
                    current_line += 1
                    continue
                elif self.patterns["error_message"].search(line):
                    error_component = self._extract_error_message(
                        line, current_line + start_line_offset, line_start_char
                    )
                    if error_component:
                        nested_components.append(error_component)
                        current_line += 1
                        continue
                elif self.patterns["explicit_reasoning_block"].search(line):
                    (
                        reasoning_component,
                        lines_consumed,
                    ) = self._parse_explicit_reasoning(
                        lines, current_line, line_start_char
                    )
                    if reasoning_component:
                        nested_components.append(reasoning_component)
                        current_line += lines_consumed
                        continue
                current_line += 1
        return nested_components

    def _parse_explicit_reasoning(self, lines, current_line, line_start_char):
        """Parse explicit reasoning block, including nested <details> and <think> blocks"""
        for block_type, (start_pat, end_pat, comp_type, key) in [
            (
                "details",
                (
                    self.patterns["details_block_start"],
                    self.patterns["details_block_end"],
                    ComponentType.EXPLICIT_REASONING_BLOCK,
                    None,
                ),
            ),
            (
                "think",
                (
                    self.patterns["think_block_start"],
                    self.patterns["think_block_end"],
                    ComponentType.EXPLICIT_REASONING_BLOCK,
                    None,
                ),
            ),
        ]:
            if start_pat.match(lines[current_line]):
                component, lines_consumed = self._parse_block(
                    lines,
                    current_line,
                    line_start_char,
                    block_type,
                    start_pat,
                    end_pat,
                    comp_type,
                    key,
                )
                return component, lines_consumed
        # Fallback: not a block, skip
        return None, 1

    def _parse_file_references(
        self, line: str, line_number: int, start_char: int
    ) -> List[AtomicComponent]:
        """Parse file references from a line"""
        refs = []
        for match in self.patterns["file_reference"].finditer(line):
            filepath = match.group(1)

            component = AtomicComponent(
                component_type=ComponentType.FILE_REFERENCE,
                boundaries=ComponentBoundaries(
                    line_number,
                    line_number,
                    start_char + match.start(),
                    start_char + match.end(),
                    start_char + match.start(),
                    start_char + match.end(),
                ),
                raw_content=match.group(0),
                processed_content={
                    "filepath": filepath,
                    "reference_type": "inline",
                    "context": "conversation",
                },
                analysis={
                    "file_extension": (
                        filepath.split(".")[-1] if "." in filepath else ""
                    ),
                    "file_type": self._classify_file_type(filepath),
                    "relative_path": not filepath.startswith("/"),
                    "character_count": len(filepath),
                },
            )
            self._add_component_metadata(component)
            refs.append(component)

        return refs

    def _parse_tool_calls(self, lines, start_line, start_char):
        """Parse tool function calls into atomic components (minimal schema)"""
        components = []
        current_line = start_line
        while current_line < len(lines):
            line = lines[current_line]
            invoke_match = re.search(r'<invoke name="([^"]+)">', line)
            if invoke_match:
                tool_name = invoke_match.group(1)
                component = AtomicComponent(
                    component_type=ComponentType.TOOL_CALL,
                    raw_content=line.strip(),
                    processed_content={"tool_name": tool_name},
                    analysis={},
                )
                self._add_component_metadata(component)
                components.append(component)
            if re.search(r"</invoke>", line):
                break
            current_line += 1
        return components, current_line - start_line + 1

    def _parse_tool_results(
        self, lines: List[str], start_line: int, start_char: int
    ) -> Tuple[List[AtomicComponent], int]:
        """Parse tool function results into atomic components"""
        components = []
        current_line = start_line + 1  # Skip opening tag
        result_sequence = 0

        while current_line < len(lines):
            line = lines[current_line]

            if self.patterns["function_results_end"].search(line):
                break

            # Look for result blocks using multi-line pattern matching
            remaining_lines = lines[current_line:]
            remaining_content = "\n".join(remaining_lines)

            # Find result block pattern
            result_match = self.patterns["result_block"].search(remaining_content)
            if result_match:
                tool_name = result_match.group(1)
                output_content = result_match.group(2)

                # Calculate boundaries for the result block
                result_start = current_line
                result_content = result_match.group(0)
                result_lines = result_content.count("\n")
                result_end = current_line + result_lines

                # Determine output type and success
                output_type = self._classify_output_type(output_content)
                success_indicator = not any(
                    error_word in output_content.lower()
                    for error_word in ["error", "failed", "exception", "traceback"]
                )

                # Create tool result component
                component = AtomicComponent(
                    component_type=ComponentType.TOOL_RESULT,
                    boundaries=ComponentBoundaries(
                        result_start,
                        result_end,
                        start_char,
                        start_char + len(result_content),
                        start_char,
                        start_char + len(result_content),
                    ),
                    raw_content=result_content,
                    processed_content={
                        "tool_name": tool_name,
                        "output_content": output_content,
                        "success_indicator": success_indicator,
                        "error_message": (
                            ""
                            if success_indicator
                            else self._extract_error_message(output_content)
                        ),
                        "result_sequence": result_sequence,
                    },
                    analysis={
                        "output_type": output_type,
                        "content_size": len(output_content),
                        "line_count": output_content.count("\n") + 1,
                        "contains_code": "```" in output_content,
                        "contains_data": any(
                            marker in output_content.lower()
                            for marker in ["json", "xml", "csv", "yaml"]
                        ),
                        "word_count": len(output_content.split()),
                        "character_count": len(output_content),
                    },
                    graph_metadata={
                        "node_type": "tool_result",
                        "relationships": [
                            "result_of_call",
                            "contains_content",
                            "triggers_action",
                        ],
                    },
                )

                self._add_component_metadata(component)
                components.append(component)

                # Parse nested content within tool results
                if output_type == "file_content" and "```" in output_content:
                    # Extract code blocks from tool results
                    self._parse_nested_code_blocks(component, output_content)
                elif output_type == "directory_listing":
                    # Extract file references from directory listings
                    self._parse_directory_entries(component, output_content)

                current_line += result_lines + 1
                result_sequence += 1
            else:
                current_line += 1

        return components, current_line - start_line

    def _classify_output_type(self, content: str) -> str:
        """Classify the type of tool output"""
        return AtomicAnalysis.classify_output_type(content)

    def _extract_error_message(self, line, current_line=None, line_start_char=None):
        """Extract error message from a line and return as AtomicComponent"""
        # Accepts extra args for compatibility, but only uses line
        if isinstance(line, str):
            for error_word in ["error:", "exception:", "failed:"]:
                if error_word in line.lower():
                    # Build an AtomicComponent for the error message
                    return AtomicComponent(
                        component_type=ComponentType.ERROR_MESSAGE,
                        raw_content=line.strip(),
                        processed_content={"error_message": line.strip()},
                        analysis={"contains_error": True},
                    )
        # If not a recognized error, return None
        return None

    def _parse_nested_code_blocks(
        self, parent_component: AtomicComponent, content: str
    ):
        """Parse code blocks found within tool results"""
        code_pattern = re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL)
        for match in code_pattern.finditer(content):
            language = match.group(1) or ""
            code_content = match.group(2)

            code_component = AtomicComponent(
                component_type=ComponentType.CODE_BLOCK,
                raw_content=match.group(0),
                processed_content={
                    "language": language,
                    "content": code_content,
                    "line_count": code_content.count("\n") + 1,
                    "character_count": len(code_content),
                    "parent_tool_result": parent_component.component_id,
                },
                analysis=self._analyze_code_block(language, code_content),
            )

            self._add_component_metadata(code_component)
            self.components.append(code_component)

            # Create relationship: code block is part of tool result
            relationship = AtomicRelationship(
                relationship_type=RelationshipType.PART_OF,
                source_component_id=code_component.component_id,
                target_component_id=parent_component.component_id,
                confidence=1.0,
                context={"extraction_context": "nested_in_tool_result"},
            )
            self.relationships.append(relationship)

    def _parse_directory_entries(self, parent_component: AtomicComponent, content: str):
        """Parse file and directory entries from directory listings"""
        # Parse file entries
        for file_match in self.patterns["file_entry"].finditer(content):
            filename = file_match.group(1)

            file_component = AtomicComponent(
                component_type=ComponentType.FILE_REFERENCE,
                raw_content=file_match.group(0),
                processed_content={
                    "filepath": filename,
                    "reference_type": "list",
                    "context": "directory_listing",
                    "parent_tool_result": parent_component.component_id,
                },
                analysis={
                    "file_extension": (
                        filename.split(".")[-1] if "." in filename else ""
                    ),
                    "file_type": self._classify_file_type(filename),
                    "relative_path": not filename.startswith("/"),
                    "character_count": len(filename),
                },
            )

            self._add_component_metadata(file_component)
            self.components.append(file_component)

            # Create relationship: file reference is part of tool result
            relationship = AtomicRelationship(
                relationship_type=RelationshipType.PART_OF,
                source_component_id=file_component.component_id,
                target_component_id=parent_component.component_id,
                confidence=1.0,
                context={"extraction_context": "directory_listing"},
            )
            self.relationships.append(relationship)

    def _classify_file_type(self, filename: str) -> str:
        """Classify file type based on extension"""
        if "." not in filename:
            return "no_extension"

        ext = filename.split(".")[-1].lower()

        if ext in ["py", "js", "ts", "java", "cpp", "c", "go", "rs"]:
            return "source_code"
        elif ext in ["json", "yaml", "yml", "toml", "ini", "cfg"]:
            return "configuration"
        elif ext in ["md", "txt", "rst", "doc"]:
            return "documentation"
        elif ext in ["sql", "db", "sqlite"]:
            return "database"
        elif ext in ["jpg", "png", "gif", "svg"]:
            return "image"
        else:
            return "other"

    def _parse_code_block(self, lines, start_line, start_char):
        """Parse code block from lines[start_line:]"""
        if not self.patterns["code_block_start"].match(lines[start_line]):
            return None, 1
        language = self.patterns["code_block_start"].match(lines[start_line]).group(1)
        code_lines = []
        end_line = start_line + 1
        while end_line < len(lines):
            if self.patterns["code_block_end"].match(lines[end_line]):
                break
            code_lines.append(lines[end_line])
            end_line += 1
        # If no end found, treat as invalid
        if end_line == len(lines):
            return None, end_line - start_line
        raw_content = "\n".join([lines[start_line]] + code_lines + [lines[end_line]])
        component = AtomicComponent(
            component_type=ComponentType.CODE_BLOCK,
            raw_content=raw_content,
            processed_content={
                "language": language,
                "content": "\n".join(code_lines),
                "line_count": len(code_lines),
                "character_count": sum(len(l) for l in code_lines),
            },
        )
        self._add_component_metadata(component)
        return component, end_line - start_line + 1

    def _add_component_metadata(self, component: AtomicComponent):
        """Add common metadata to component"""
        component.session_id = self.current_session_id
        component.component_sequence = self.current_component_sequence
        self.current_component_sequence += 1

        # Add reconstruction metadata
        component.reconstruction = {
            "original_format": component.raw_content,
            "dependencies": [],
            "rendering_order": self.current_component_sequence,
        }

    def _generate_relationships(self):
        """Generate relationships between all components"""
        # Generate temporal relationships (follows/precedes)
        for i in range(len(self.components) - 1):
            current = self.components[i]
            next_comp = self.components[i + 1]

            follows_rel = AtomicRelationship(
                relationship_type=RelationshipType.FOLLOWS,
                source_component_id=next_comp.component_id,
                target_component_id=current.component_id,
                sequence_distance=1,
                temporal_order=i,
            )
            self.relationships.append(follows_rel)

            # Q&A: If current is User turn and next is Assistant, link as ANSWERS
            if (
                current.component_type == ComponentType.CONVERSATION_TURN
                and next_comp.component_type == ComponentType.CONVERSATION_TURN
            ):
                current_speaker = current.processed_content.get("speaker", "").lower()
                next_speaker = next_comp.processed_content.get("speaker", "").lower()
                if current_speaker == "user" and next_speaker == "assistant":
                    qa_rel = AtomicRelationship(
                        relationship_type=RelationshipType.ANSWERS,
                        source_component_id=next_comp.component_id,
                        target_component_id=current.component_id,
                        confidence=1.0,
                    )
                    self.relationships.append(qa_rel)

        # Generate containment relationships
        for component in self.components:
            if component.component_type == ComponentType.CONVERSATION_TURN:
                # Find components within this turn
                for other in self.components:
                    if (
                        other.turn_sequence == component.turn_sequence
                        and other.component_type != ComponentType.CONVERSATION_TURN
                    ):
                        contains_rel = AtomicRelationship(
                            relationship_type=RelationshipType.CONTAINS,
                            source_component_id=component.component_id,
                            target_component_id=other.component_id,
                            confidence=1.0,
                        )
                        self.relationships.append(contains_rel)

    # Helper methods for analysis
    def _analyze_turn_content(self, lines: List[str]) -> Dict:
        """Analyze conversation turn content"""
        return AtomicAnalysis.analyze_turn_content(self.patterns, lines)

    def _classify_output_type(self, content: str) -> str:
        """Classify the type of tool output"""
        return AtomicAnalysis.classify_output_type(content)

    def _analyze_code_block(self, language: str, content: str) -> Dict:
        """Analyze code block characteristics"""
        return AtomicAnalysis.analyze_code_block(language, content)

    def _classify_token_type(self, token: str) -> str:
        """Classify token type"""
        if token.isspace():
            return "whitespace"
        elif token.isdigit():
            return "number"
        elif token in [
            ".",
            ",",
            ":",
            ";",
            "!",
            "?",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
            '"',
            "'",
        ]:
            return "punctuation"
        elif token in ["+", "-", "*", "/", "=", "<", ">", "&", "|", "^", "%"]:
            return "operator"
        else:
            return "word"

    def _analyze_token(self, token: str, language: str) -> Dict:
        """Analyze token characteristics"""
        return {
            "is_keyword": self._is_programming_keyword(token, language),
            "is_identifier": (
                token.isidentifier() if hasattr(token, "isidentifier") else False
            ),
            "is_literal": token.startswith('"')
            or token.startswith("'")
            or token.isdigit(),
            "language_specific_type": self._get_language_specific_type(token, language),
        }

    def _classify_character(self, char: str) -> str:
        """Classify character category"""
        if char.isalpha():
            return "letter"
        elif char.isdigit():
            return "digit"
        elif char.isspace():
            return "whitespace"
        else:
            return "symbol"

    def _analyze_character(self, char: str) -> Dict:
        """Analyze character properties"""
        return {
            "is_alphanumeric": char.isalnum(),
            "is_uppercase": char.isupper(),
            "is_lowercase": char.islower(),
            "is_special_char": not char.isalnum() and not char.isspace(),
            "ascii_value": ord(char),
        }

    # Additional helper methods would continue here...
    def _extract_thinking_content(self, lines: List[str]) -> str:
        """Extract thinking content between summary and end tags"""
        content_lines = []
        in_content = False

        for line in lines:
            if "</summary>" in line:
                in_content = True
                # Add any content after </summary> on the same line
                after_summary = line.split("</summary>", 1)
                if len(after_summary) > 1 and after_summary[1].strip():
                    content_lines.append(after_summary[1])
                continue
            elif "</details></think>" in line:
                # Add any content before closing tags
                before_close = line.split("</details></think>", 1)[0]
                if before_close.strip():
                    content_lines.append(before_close)
                break
            elif in_content:
                content_lines.append(line)

        return "\n".join(content_lines).strip()

    def _estimate_execution_time(self, tool_name: str) -> float:
        """Estimate tool execution time in milliseconds"""
        time_estimates = {
            "read_file": 100,
            "write_file": 200,
            "codebase_search": 1000,
            "grep_search": 500,
            "run_terminal_cmd": 2000,
            "list_dir": 50,
        }
        return time_estimates.get(tool_name, 500)

    def _calculate_tool_complexity(
        self, tool_name: str, parameters: List[AtomicComponent]
    ) -> float:
        """Calculate tool call complexity score"""
        base_complexity = {
            "read_file": 0.2,
            "codebase_search": 0.8,
            "grep_search": 0.6,
            "run_terminal_cmd": 0.9,
            "edit_file": 0.7,
        }.get(tool_name, 0.5)

        # Adjust based on parameter complexity
        param_complexity = (
            sum(
                len(p.processed_content.get("parameter_value", "")) / 100.0
                for p in parameters
            )
            / len(parameters)
            if parameters
            else 0
        )

        return min(base_complexity + param_complexity, 1.0)

    def _is_programming_keyword(self, token: str, language: str) -> bool:
        """Check if token is a programming keyword"""
        keywords = {
            "python": [
                "def",
                "class",
                "if",
                "else",
                "elif",
                "for",
                "while",
                "try",
                "except",
                "import",
                "from",
                "return",
            ],
            "javascript": [
                "function",
                "var",
                "let",
                "const",
                "if",
                "else",
                "for",
                "while",
                "return",
                "class",
            ],
            "bash": [
                "if",
                "then",
                "else",
                "fi",
                "for",
                "while",
                "do",
                "done",
                "case",
                "esac",
            ],
        }
        return token in keywords.get(language, [])

    def _get_language_specific_type(self, token: str, language: str) -> str:
        """Get language-specific token type"""
        if self._is_programming_keyword(token, language):
            return "keyword"
        elif token.startswith("_") or token.isidentifier():
            return "identifier"
        elif token.isdigit():
            return "literal"
        else:
            return "unknown"

    def _safe_append(self, target_list, obj):
        """Append obj to target_list if obj is AtomicComponent."""
        if isinstance(obj, AtomicComponent):
            target_list.append(obj)
        else:
            logger.warning(
                f"Attempted to append non-AtomicComponent: {type(obj)} {obj}"
            )

    def _safe_extend(self, target_list, obj):
        """Extend target_list with obj if obj is a list of AtomicComponent."""
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, AtomicComponent):
                    target_list.append(item)
                else:
                    logger.warning(
                        f"Attempted to extend with non-AtomicComponent: {type(item)} {item}"
                    )
        elif isinstance(obj, AtomicComponent):
            target_list.append(obj)
        else:
            logger.warning(f"Attempted to extend with non-list: {type(obj)} {obj}")

    def _safe_relationship(self, rel_type, source, target, **kwargs):
        """Create relationship if both source and target are AtomicComponent."""
        if isinstance(source, AtomicComponent) and isinstance(target, AtomicComponent):
            try:
                rel = AtomicRelationship(
                    relationship_type=rel_type,
                    source_component_id=source.component_id,
                    target_component_id=target.component_id,
                    **kwargs,
                )
                self.relationships.append(rel)
            except Exception as e:
                logger.warning(f"Failed to create relationship: {e}")
        else:
            logger.warning(f"Invalid relationship: {type(source)}, {type(target)}")


# Example usage
async def main():
    """Test the atomic parser or run on a specified file"""
    parser = AtomicSpecStoryParser()

    # Accept filename from command line
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = ".specstory/history/2025-01-27_10-30Z-test-conversation.md"

    if Path(test_file).exists():
        components, relationships = await parser.parse_file(test_file)
        print(f"\n=== Atomic Parse Results for: {test_file} ===")
        print(
            f"📊 Parsed {len(components)} components and {len(relationships)} relationships"
        )
        print(f"🧩 Component types: {set(c.component_type.value for c in components)}")
        print(
            f"🔗 Relationship types: {set(r.relationship_type.value for r in relationships)}"
        )
    else:
        print(f"File not found: {test_file}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
