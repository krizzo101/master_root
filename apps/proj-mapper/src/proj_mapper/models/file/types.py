"""File type definitions for Project Mapper.

This module contains the FileType enumeration.
"""

from enum import Enum


class FileType(Enum):
    """Enumeration of supported file types."""
    
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUBY = "ruby"
    PHP = "php"
    RUST = "rust"
    HTML = "html"
    CSS = "css"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    SQL = "sql"
    TEXT = "text"
    BINARY = "binary"
    OTHER = "other"
    UNKNOWN = "unknown"
    RESTRUCTUREDTEXT = "restructuredtext"
    
    @property
    def value(self):
        """Get the enum value.
        
        This property is explicitly defined to ensure that string values
        that are passed instead of enum instances can be handled uniformly.
        """
        return self._value_
    
    @classmethod
    def from_extension(cls, extension: str) -> "FileType":
        """Determine file type from file extension.
        
        Args:
            extension: The file extension (without dot)
            
        Returns:
            The determined file type
        """
        # Strip the leading dot if present
        if extension.startswith("."):
            extension = extension[1:]
        
        extension = extension.lower()
        
        # Map of extensions to file types
        extension_map = {
            "py": cls.PYTHON,
            "js": cls.JAVASCRIPT,
            "jsx": cls.JAVASCRIPT,
            "ts": cls.TYPESCRIPT,
            "tsx": cls.TYPESCRIPT,
            "java": cls.JAVA,
            "cs": cls.CSHARP,
            "cpp": cls.CPP, "cc": cls.CPP, "cxx": cls.CPP, "hpp": cls.CPP, "hxx": cls.CPP, "h": cls.CPP,
            "c": cls.C,
            "go": cls.GO,
            "rb": cls.RUBY,
            "php": cls.PHP,
            "rs": cls.RUST,
            "html": cls.HTML, "htm": cls.HTML,
            "css": cls.CSS, "scss": cls.CSS, "sass": cls.CSS,
            "md": cls.MARKDOWN, "markdown": cls.MARKDOWN,
            "json": cls.JSON,
            "yaml": cls.YAML, "yml": cls.YAML,
            "xml": cls.XML,
            "sql": cls.SQL,
            "txt": cls.TEXT,
            "bin": cls.BINARY,
        }
        
        return extension_map.get(extension, cls.UNKNOWN) 