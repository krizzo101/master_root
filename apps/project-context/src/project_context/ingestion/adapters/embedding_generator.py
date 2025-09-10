"""Semantic embedding generation for code analysis and search.

This module provides sophisticated embedding generation capabilities for code files,
supporting multiple embedding models and techniques for enhanced semantic search.
"""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class EmbeddingGenerator:
    """Advanced embedding generator with multiple model support."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize embedding generator with configuration."""
        self.config = config or {}
        self.embedding_cache: Dict[str, List[float]] = {}
        self.model_name = self.config.get("model_name", "sentence-transformers")
        self.cache_enabled = self.config.get("cache_embeddings", True)
        self.cache_file = self.config.get("cache_file", ".embedding_cache.json")
        self.max_text_length = self.config.get("max_text_length", 8192)

        # Load cache if enabled
        if self.cache_enabled:
            self._load_cache()

    def _load_cache(self) -> None:
        """Load embedding cache from disk."""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.embedding_cache = json.load(f)
                logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            self.embedding_cache = {}

    def _save_cache(self) -> None:
        """Save embedding cache to disk."""
        if not self.cache_enabled:
            return

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.embedding_cache, f, indent=2)
            logger.debug(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def _get_cache_key(self, text: str, context: str = "") -> str:
        """Generate cache key for text and context."""
        combined = f"{self.model_name}:{context}:{text}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def generate_embedding(
        self, text: str, context: str = "code", use_cache: bool = True
    ) -> Optional[List[float]]:
        """Generate embedding for text with optional context."""
        if not text or not text.strip():
            return None

        # Truncate text if too long
        if len(text) > self.max_text_length:
            text = text[: self.max_text_length]

        # Check cache first
        if use_cache and self.cache_enabled:
            cache_key = self._get_cache_key(text, context)
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]

        # Generate new embedding
        embedding = await self._generate_embedding_impl(text, context)

        # Cache the result
        if embedding and use_cache and self.cache_enabled:
            cache_key = self._get_cache_key(text, context)
            self.embedding_cache[cache_key] = embedding

            # Periodically save cache
            if len(self.embedding_cache) % 100 == 0:
                self._save_cache()

        return embedding

    async def _generate_embedding_impl(
        self, text: str, context: str = "code"
    ) -> Optional[List[float]]:
        """Implementation-specific embedding generation."""
        try:
            # Try different embedding approaches in order of preference
            embedding_methods = [
                self._generate_openai_embedding,
                self._generate_sentence_transformer_embedding,
                self._generate_basic_tfidf_embedding,
            ]

            for method in embedding_methods:
                try:
                    embedding = await method(text, context)
                    if embedding:
                        return embedding
                except Exception as e:
                    logger.debug(f"Embedding method {method.__name__} failed: {e}")
                    continue

            logger.warning("All embedding methods failed")
            return None

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def _generate_openai_embedding(
        self, text: str, context: str = "code"
    ) -> Optional[List[float]]:
        """Generate embedding using OpenAI API."""
        try:
            # Check if OpenAI API key is available
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None

            import openai

            # Set up client
            client = openai.AsyncOpenAI(api_key=api_key)

            # Choose model based on context
            model = (
                "text-embedding-3-small"
                if context == "code"
                else "text-embedding-3-small"
            )

            # Generate embedding
            response = await client.embeddings.create(
                model=model, input=text, encoding_format="float"
            )

            if response.data:
                return response.data[0].embedding

        except ImportError:
            logger.debug("OpenAI package not available")
        except Exception as e:
            logger.debug(f"OpenAI embedding failed: {e}")

        return None

    async def _generate_sentence_transformer_embedding(
        self, text: str, context: str = "code"
    ) -> Optional[List[float]]:
        """Generate embedding using sentence-transformers."""
        try:
            import torch
            from sentence_transformers import SentenceTransformer

            # Choose model based on context
            model_names = {
                "code": "microsoft/codebert-base",
                "text": "all-MiniLM-L6-v2",
                "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",
            }

            model_name = model_names.get(context, model_names["text"])

            # Load model (this should be cached by the library)
            model = SentenceTransformer(model_name)

            # Generate embedding
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, lambda: model.encode(text, convert_to_numpy=True)
            )

            return embedding.tolist()

        except ImportError:
            logger.debug("sentence-transformers package not available")
        except Exception as e:
            logger.debug(f"Sentence transformer embedding failed: {e}")

        return None

    async def _generate_basic_tfidf_embedding(
        self, text: str, context: str = "code"
    ) -> Optional[List[float]]:
        """Generate basic TF-IDF based embedding as fallback."""
        try:
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Create a simple vocabulary for code analysis
            code_vocabulary = [
                # Keywords
                "function",
                "class",
                "method",
                "variable",
                "constant",
                "import",
                "export",
                "async",
                "await",
                "return",
                "yield",
                "raise",
                "throw",
                "try",
                "catch",
                "if",
                "else",
                "elif",
                "for",
                "while",
                "do",
                "switch",
                "case",
                "break",
                "continue",
                "public",
                "private",
                "protected",
                "static",
                "final",
                "abstract",
                # Common patterns
                "initialize",
                "constructor",
                "destructor",
                "getter",
                "setter",
                "property",
                "decorator",
                "annotation",
                "interface",
                "implementation",
                "inheritance",
                "polymorphism",
                "encapsulation",
                "abstraction",
                "callback",
                "promise",
                "closure",
                "scope",
                "namespace",
                "module",
                "package",
                "library",
                # Data types
                "string",
                "number",
                "integer",
                "float",
                "boolean",
                "array",
                "list",
                "dict",
                "map",
                "set",
                "tuple",
                "object",
                "null",
                "undefined",
                "void",
                # Common operations
                "create",
                "read",
                "update",
                "delete",
                "find",
                "search",
                "filter",
                "sort",
                "map",
                "reduce",
                "transform",
                "validate",
                "parse",
                "format",
                "serialize",
                "deserialize",
                "encode",
                "decode",
                "compress",
                "decompress",
            ]

            # Use a simple approach: create TF-IDF for single document
            vectorizer = TfidfVectorizer(
                vocabulary=code_vocabulary,
                lowercase=True,
                stop_words="english" if context != "code" else None,
                max_features=512,  # Fixed size embedding
            )

            # Fit and transform (this creates a sparse matrix)
            tfidf_matrix = vectorizer.fit_transform([text])

            # Convert to dense array and pad/truncate to fixed size
            dense_embedding = tfidf_matrix.toarray()[0]

            # Pad or truncate to 384 dimensions (common embedding size)
            target_size = 384
            if len(dense_embedding) < target_size:
                # Pad with zeros
                padding = [0.0] * (target_size - len(dense_embedding))
                dense_embedding = np.concatenate([dense_embedding, padding])
            else:
                # Truncate
                dense_embedding = dense_embedding[:target_size]

            return dense_embedding.tolist()

        except ImportError:
            logger.debug("scikit-learn not available for TF-IDF embedding")
        except Exception as e:
            logger.debug(f"TF-IDF embedding failed: {e}")

        return None

    async def generate_code_embedding(
        self, code_content: str, symbols: Dict[str, Any] = None, file_path: str = ""
    ) -> Optional[List[float]]:
        """Generate specialized embedding for code content."""
        # Create enriched text for embedding
        enriched_text = self._create_enriched_code_text(
            code_content, symbols, file_path
        )

        return await self.generate_embedding(enriched_text, context="code")

    def _create_enriched_code_text(
        self, code_content: str, symbols: Dict[str, Any] = None, file_path: str = ""
    ) -> str:
        """Create enriched text representation of code for embedding."""
        parts = []

        # Add file context
        if file_path:
            file_name = Path(file_path).stem
            file_ext = Path(file_path).suffix
            parts.append(f"File: {file_name}{file_ext}")

        # Add language information
        if symbols and symbols.get("language"):
            parts.append(f"Language: {symbols['language']}")

        # Add function signatures
        if symbols and symbols.get("functions"):
            func_names = [
                f["name"] for f in symbols["functions"][:10]
            ]  # Limit to first 10
            if func_names:
                parts.append(f"Functions: {', '.join(func_names)}")

        # Add class names
        if symbols and symbols.get("classes"):
            class_names = [
                c["name"] for c in symbols["classes"][:5]
            ]  # Limit to first 5
            if class_names:
                parts.append(f"Classes: {', '.join(class_names)}")

        # Add import information
        if symbols and symbols.get("imports"):
            import_modules = []
            for imp in symbols["imports"][:10]:  # Limit to first 10
                if isinstance(imp, dict):
                    module = imp.get("module") or imp.get("package", "")
                else:
                    module = str(imp)
                if module:
                    import_modules.append(module)

            if import_modules:
                parts.append(f"Imports: {', '.join(import_modules)}")

        # Add complexity information
        if symbols and symbols.get("complexity_metrics"):
            complexity = symbols["complexity_metrics"]
            if complexity.get("cyclomatic_complexity", 0) > 5:
                parts.append("High complexity code")
            if complexity.get("function_count", 0) > 10:
                parts.append("Many functions")

        # Add architectural patterns
        if symbols and symbols.get("architectural_patterns"):
            patterns = [
                p.get("pattern", "") for p in symbols["architectural_patterns"][:3]
            ]
            patterns = [p for p in patterns if p]
            if patterns:
                parts.append(f"Patterns: {', '.join(patterns)}")

        # Add cleaned code content (truncated)
        cleaned_code = self._clean_code_for_embedding(code_content)
        parts.append(cleaned_code)

        return " | ".join(parts)

    def _clean_code_for_embedding(self, code_content: str) -> str:
        """Clean and prepare code content for embedding."""
        lines = code_content.splitlines()

        # Remove empty lines and comments
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("//"):
                # Remove string literals to focus on structure
                line = self._remove_string_literals(line)
                if line.strip():
                    cleaned_lines.append(line)

        # Join and truncate
        cleaned_code = " ".join(cleaned_lines)

        # Truncate to reasonable length for embedding
        max_code_length = self.max_text_length - 500  # Leave room for metadata
        if len(cleaned_code) > max_code_length:
            cleaned_code = cleaned_code[:max_code_length]

        return cleaned_code

    def _remove_string_literals(self, line: str) -> str:
        """Remove string literals from code line."""
        import re

        # Remove string literals (simplified approach)
        line = re.sub(r'"[^"]*"', '""', line)  # Double quotes
        line = re.sub(r"'[^']*'", "''", line)  # Single quotes
        line = re.sub(r"`[^`]*`", "``", line)  # Backticks

        return line

    async def generate_batch_embeddings(
        self, texts: List[str], context: str = "code"
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batch."""
        embeddings = []

        for text in texts:
            embedding = await self.generate_embedding(text, context)
            embeddings.append(embedding)

        return embeddings

    async def generate_summary_embedding(
        self,
        title: str = "",
        summary: str = "",
        content: str = "",
        metadata: Dict[str, Any] = None,
    ) -> Optional[List[float]]:
        """Generate embedding for item summary combining multiple fields."""
        parts = []

        if title:
            parts.append(f"Title: {title}")

        if summary:
            parts.append(f"Summary: {summary}")

        if metadata:
            # Add relevant metadata
            if metadata.get("language"):
                parts.append(f"Language: {metadata['language']}")

            if metadata.get("entity_type"):
                parts.append(f"Type: {metadata['entity_type']}")

            if metadata.get("tags"):
                tags = metadata["tags"][:5]  # Limit tags
                parts.append(f"Tags: {', '.join(tags)}")

        # Add truncated content
        if content:
            max_content_len = self.max_text_length - len(" | ".join(parts)) - 100
            if len(content) > max_content_len:
                content = content[:max_content_len]
            parts.append(content)

        combined_text = " | ".join(parts)
        return await self.generate_embedding(combined_text, context="text")

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0

        try:
            import numpy as np

            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0

    def find_similar_embeddings(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Tuple[str, List[float]]],
        top_k: int = 10,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """Find most similar embeddings to query."""
        similarities = []

        for identifier, candidate_embedding in candidate_embeddings:
            similarity = self.calculate_similarity(query_embedding, candidate_embedding)
            if similarity >= threshold:
                similarities.append((identifier, similarity))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    async def cleanup(self) -> None:
        """Cleanup resources and save cache."""
        if self.cache_enabled:
            self._save_cache()
        logger.info("Embedding generator cleanup completed")


class CodeEmbeddingGenerator(EmbeddingGenerator):
    """Specialized embedding generator for code analysis."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize code-specific embedding generator."""
        default_config = {
            "model_name": "code-embeddings",
            "cache_embeddings": True,
            "cache_file": ".code_embedding_cache.json",
            "max_text_length": 16384,  # Longer for code
            "include_ast_features": True,
            "include_complexity_metrics": True,
            "include_dependency_info": True,
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)
        self.ast_feature_extractor = (
            ASTFeatureExtractor() if config.get("include_ast_features") else None
        )

    async def generate_function_embedding(
        self, function_info: Dict[str, Any], context_code: str = ""
    ) -> Optional[List[float]]:
        """Generate embedding specifically for a function."""
        # Create function-specific text
        parts = [
            f"Function: {function_info.get('name', 'unknown')}",
            f"Signature: {function_info.get('signature', '')}",
        ]

        if function_info.get("docstring"):
            parts.append(f"Documentation: {function_info['docstring']}")

        if function_info.get("parameters"):
            param_names = [p.get("name", "") for p in function_info["parameters"]]
            parts.append(f"Parameters: {', '.join(param_names)}")

        if function_info.get("calls"):
            calls = function_info["calls"][:5]  # Limit to first 5 calls
            parts.append(f"Calls: {', '.join(calls)}")

        if function_info.get("complexity_score", 0) > 5:
            parts.append(
                f"Complex function (complexity: {function_info['complexity_score']})"
            )

        # Add some context code if available
        if context_code:
            context_snippet = context_code[:500]  # Small snippet
            parts.append(f"Context: {context_snippet}")

        function_text = " | ".join(parts)
        return await self.generate_embedding(function_text, context="code")

    async def generate_class_embedding(
        self, class_info: Dict[str, Any], context_code: str = ""
    ) -> Optional[List[float]]:
        """Generate embedding specifically for a class."""
        parts = [
            f"Class: {class_info.get('name', 'unknown')}",
        ]

        if class_info.get("docstring"):
            parts.append(f"Documentation: {class_info['docstring']}")

        if class_info.get("base_classes"):
            bases = class_info["base_classes"][:3]  # Limit to first 3
            parts.append(f"Inherits from: {', '.join(bases)}")

        if class_info.get("methods"):
            method_names = [m.get("name", "") for m in class_info["methods"][:10]]
            parts.append(f"Methods: {', '.join(method_names)}")

        if class_info.get("properties"):
            prop_names = [p.get("name", "") for p in class_info["properties"][:5]]
            parts.append(f"Properties: {', '.join(prop_names)}")

        # Add architectural pattern hints
        class_name = class_info.get("name", "").lower()
        if any(
            pattern in class_name
            for pattern in ["factory", "builder", "singleton", "observer", "strategy"]
        ):
            parts.append(f"Design pattern class")

        class_text = " | ".join(parts)
        return await self.generate_embedding(class_text, context="code")


class ASTFeatureExtractor:
    """Extract features from AST for enhanced embeddings."""

    def __init__(self):
        """Initialize AST feature extractor."""
        self.feature_cache = {}

    def extract_features(self, code: str, language: str) -> Dict[str, Any]:
        """Extract AST-based features from code."""
        if language == "python":
            return self._extract_python_ast_features(code)
        else:
            # Fallback to basic features
            return self._extract_basic_features(code)

    def _extract_python_ast_features(self, code: str) -> Dict[str, Any]:
        """Extract Python AST features."""
        try:
            import ast

            tree = ast.parse(code)
            features = {
                "node_types": [],
                "depth": 0,
                "complexity_indicators": [],
                "import_patterns": [],
                "class_patterns": [],
                "function_patterns": [],
            }

            # Walk AST and extract features
            for node in ast.walk(tree):
                node_type = type(node).__name__
                features["node_types"].append(node_type)

                # Extract specific patterns
                if isinstance(node, ast.Import):
                    features["import_patterns"].append("direct_import")
                elif isinstance(node, ast.ImportFrom):
                    features["import_patterns"].append("from_import")
                elif isinstance(node, ast.ClassDef):
                    features["class_patterns"].append("class_definition")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    features["function_patterns"].append("function_definition")
                elif isinstance(node, (ast.If, ast.For, ast.While)):
                    features["complexity_indicators"].append(node_type.lower())

            # Calculate AST depth (simplified)
            features["depth"] = self._calculate_ast_depth(tree)

            return features

        except Exception as e:
            logger.debug(f"Failed to extract Python AST features: {e}")
            return self._extract_basic_features(code)

    def _extract_basic_features(self, code: str) -> Dict[str, Any]:
        """Extract basic code features without AST."""
        import re

        features = {
            "keywords": [],
            "operators": [],
            "patterns": [],
            "structure_indicators": [],
        }

        # Common programming keywords
        keywords = [
            "function",
            "class",
            "if",
            "else",
            "for",
            "while",
            "return",
            "import",
            "export",
            "try",
            "catch",
            "throw",
            "async",
            "await",
        ]

        for keyword in keywords:
            if re.search(rf"\b{keyword}\b", code, re.IGNORECASE):
                features["keywords"].append(keyword)

        # Common operators
        operators = ["+", "-", "*", "/", "=", "==", "!=", "<", ">", "&&", "||"]
        for op in operators:
            if op in code:
                features["operators"].append(op)

        # Structure patterns
        if "{" in code and "}" in code:
            features["structure_indicators"].append("block_structure")
        if "(" in code and ")" in code:
            features["structure_indicators"].append("function_calls")
        if "[" in code and "]" in code:
            features["structure_indicators"].append("array_access")

        return features

    def _calculate_ast_depth(self, node, current_depth=0) -> int:
        """Calculate maximum depth of AST tree."""
        max_depth = current_depth

        for child in getattr(node, "body", []) or []:
            child_depth = self._calculate_ast_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)

        return max_depth
