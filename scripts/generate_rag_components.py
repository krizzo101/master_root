#!/usr/bin/env python3
"""
Code generator for OPSVI-RAG components.

Generates multiple files from templates to speed up development.
"""

from pathlib import Path


class RAGComponentGenerator:
    """Generates RAG components from templates."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.templates = self._load_templates()

    def _load_templates(self) -> dict[str, str]:
        """Load template strings."""
        return {
            "processor_base": '''"""
{module_name} processor for opsvi-rag.

{description}
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from opsvi_foundation import get_logger
from pydantic import Field

from .base import (
    BaseProcessor,
    ProcessingMetadata,
    ProcessingResult,
    ProcessingStatus,
    ProcessorConfig,
    ProcessorError,
    ProcessorType,
)


class {class_name}Config(ProcessorConfig):
    """Configuration for {module_name} processor."""
    
    processor_type: ProcessorType = Field(default=ProcessorType.{processor_type}, description="Processor type")
    # Add specific configuration options here


class {class_name}(BaseProcessor):
    """{module_name} document processor."""
    
    def __init__(self, config: {class_name}Config):
        """Initialize {module_name} processor."""
        super().__init__(config)
        self.config = config
        self.logger = get_logger(__name__)
    
    def can_process(self, file_path: Path) -> bool:
        """Check if file can be processed."""
        return file_path.suffix.lower() in {file_extensions}
    
    def process(self, file_path: Path) -> ProcessingResult:
        """Process {module_name} file."""
        start_time = time.time()
        
        try:
            # TODO: Implement {module_name} processing logic
            content = ""
            metadata = {{}}
            
            # Create processing metadata
            processing_metadata = ProcessingMetadata(
                file_size=file_path.stat().st_size,
                processing_time=time.time() - start_time,
                text_length=len(content),
                block_count=0,
                link_count=0,
                image_count=0,
                metadata_count=len(metadata),
            )
            
            return ProcessingResult(
                content=content,
                metadata=metadata,
                processing_metadata=processing_metadata,
                status=ProcessingStatus.SUCCESS,
                error_message=None,
            )
            
        except Exception as e:
            self.logger.error(f"Error processing {module_name} file {{file_path}}: {{e}}")
            return ProcessingResult(
                content="",
                metadata={{}},
                processing_metadata=ProcessingMetadata(
                    file_size=file_path.stat().st_size if file_path.exists() else 0,
                    processing_time=time.time() - start_time,
                    text_length=0,
                    block_count=0,
                    link_count=0,
                    image_count=0,
                    metadata_count=0,
                ),
                status=ProcessingStatus.ERROR,
                error_message=str(e),
            )
''',
            "chunking_base": '''"""
{module_name} chunking for opsvi-rag.

{description}
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class ChunkingError(ComponentError):
    """Raised when chunking fails."""
    pass


@dataclass
class Chunk:
    """Represents a text chunk."""
    content: str
    start_index: int
    end_index: int
    metadata: dict


class {class_name}Config(BaseModel):
    """Configuration for {module_name} chunking."""
    
    chunk_size: int = Field(default=1000, description="Target chunk size in characters")
    overlap_size: int = Field(default=200, description="Overlap between chunks")
    # Add specific configuration options here


class {class_name}(BaseComponent):
    """{module_name} chunking strategy."""
    
    def __init__(self, config: {class_name}Config):
        """Initialize {module_name} chunker."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)
    
    def chunk(self, text: str) -> List[Chunk]:
        """Chunk the given text."""
        # TODO: Implement {module_name} chunking logic
        chunks = []
        # Add chunking implementation here
        return chunks
''',
            "search_base": '''"""
{module_name} search for opsvi-rag.

{description}
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class SearchError(ComponentError):
    """Raised when search fails."""
    pass


@dataclass
class SearchResult:
    """Represents a search result."""
    content: str
    score: float
    metadata: Dict[str, Any]


class {class_name}Config(BaseModel):
    """Configuration for {module_name} search."""
    
    max_results: int = Field(default=10, description="Maximum number of results")
    # Add specific configuration options here


class {class_name}(BaseComponent):
    """{module_name} search implementation."""
    
    def __init__(self, config: {class_name}Config):
        """Initialize {module_name} search."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)
    
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Search for content matching the query."""
        # TODO: Implement {module_name} search logic
        results = []
        # Add search implementation here
        return results
''',
            "storage_base": '''"""
{module_name} storage for opsvi-rag.

{description}
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class StorageError(ComponentError):
    """Raised when storage operations fail."""
    pass


class {class_name}Config(BaseModel):
    """Configuration for {module_name} storage."""
    
    # Add specific configuration options here


class {class_name}(BaseComponent):
    """{module_name} storage implementation."""
    
    def __init__(self, config: {class_name}Config):
        """Initialize {module_name} storage."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)
    
    def store(self, key: str, data: Any) -> bool:
        """Store data with the given key."""
        # TODO: Implement {module_name} storage logic
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data with the given key."""
        # TODO: Implement {module_name} retrieval logic
        return None
    
    def delete(self, key: str) -> bool:
        """Delete data with the given key."""
        # TODO: Implement {module_name} deletion logic
        return True
''',
        }

    def generate_processor(
        self,
        module_name: str,
        class_name: str,
        processor_type: str,
        file_extensions: list[str],
        description: str,
    ) -> str:
        """Generate a processor file."""
        template = self.templates["processor_base"]
        return template.format(
            module_name=module_name,
            class_name=class_name,
            processor_type=processor_type.upper(),
            file_extensions=file_extensions,
            description=description,
        )

    def generate_chunking(
        self, module_name: str, class_name: str, description: str
    ) -> str:
        """Generate a chunking file."""
        template = self.templates["chunking_base"]
        return template.format(
            module_name=module_name, class_name=class_name, description=description
        )

    def generate_search(
        self, module_name: str, class_name: str, description: str
    ) -> str:
        """Generate a search file."""
        template = self.templates["search_base"]
        return template.format(
            module_name=module_name, class_name=class_name, description=description
        )

    def generate_storage(
        self, module_name: str, class_name: str, description: str
    ) -> str:
        """Generate a storage file."""
        template = self.templates["storage_base"]
        return template.format(
            module_name=module_name, class_name=class_name, description=description
        )

    def write_file(self, file_path: Path, content: str):
        """Write content to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Generated: {file_path}")

    def generate_all_processors(self):
        """Generate all processor files."""
        processors = [
            (
                "docx",
                "DocxProcessor",
                "DOCX",
                [".docx", ".doc"],
                "Handles Word documents",
            ),
            ("csv", "CSVProcessor", "CSV", [".csv"], "Handles CSV files"),
            ("json", "JSONProcessor", "JSON", [".json"], "Handles JSON files"),
            ("web", "WebProcessor", "WEB", [".html", ".htm"], "Handles web scraping"),
            (
                "email",
                "EmailProcessor",
                "EMAIL",
                [".eml", ".msg"],
                "Handles email files",
            ),
        ]

        for (
            module_name,
            class_name,
            processor_type,
            extensions,
            description,
        ) in processors:
            content = self.generate_processor(
                module_name, class_name, processor_type, extensions, description
            )
            file_path = self.base_path / "processors" / f"{module_name}.py"
            self.write_file(file_path, content)

    def generate_all_chunking(self):
        """Generate all chunking files."""
        chunking_modules = [
            ("semantic", "SemanticChunker", "Semantic text chunking"),
            ("overlapping", "OverlappingChunker", "Overlapping text chunking"),
            ("hierarchical", "HierarchicalChunker", "Hierarchical text chunking"),
            ("adaptive", "AdaptiveChunker", "Adaptive text chunking"),
        ]

        for module_name, class_name, description in chunking_modules:
            content = self.generate_chunking(module_name, class_name, description)
            file_path = self.base_path / "chunking" / f"{module_name}.py"
            self.write_file(file_path, content)

    def generate_all_search(self):
        """Generate all search files."""
        search_modules = [
            ("semantic", "SemanticSearch", "Semantic search implementation"),
            ("keyword", "KeywordSearch", "Keyword-based search"),
            ("faceted", "FacetedSearch", "Faceted search implementation"),
            ("vector", "VectorSearch", "Vector-based search"),
        ]

        for module_name, class_name, description in search_modules:
            content = self.generate_search(module_name, class_name, description)
            file_path = self.base_path / "search" / f"{module_name}.py"
            self.write_file(file_path, content)

    def generate_all_storage(self):
        """Generate all storage files."""
        storage_modules = [
            ("memory", "MemoryStorage", "In-memory storage implementation"),
            ("file", "FileStorage", "File-based storage implementation"),
            ("database", "DatabaseStorage", "Database storage implementation"),
        ]

        for module_name, class_name, description in storage_modules:
            content = self.generate_storage(module_name, class_name, description)
            file_path = self.base_path / "storage" / f"{module_name}.py"
            self.write_file(file_path, content)


def main():
    """Generate all RAG components."""
    base_path = Path("libs/opsvi-rag/opsvi_rag")
    generator = RAGComponentGenerator(base_path)

    print("Generating RAG components...")

    # Generate all processors
    print("\nGenerating processors...")
    generator.generate_all_processors()

    # Generate all chunking
    print("\nGenerating chunking modules...")
    generator.generate_all_chunking()

    # Generate all search
    print("\nGenerating search modules...")
    generator.generate_all_search()

    # Generate all storage
    print("\nGenerating storage modules...")
    generator.generate_all_storage()

    print("\nGeneration complete!")


if __name__ == "__main__":
    main()
