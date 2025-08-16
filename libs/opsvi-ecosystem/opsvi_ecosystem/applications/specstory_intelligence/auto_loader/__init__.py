"""
SpecStory Auto-Loader Module
Provides automatic file monitoring and processing for SpecStory conversation files
"""

from .database_storage import SimplifiedSpecStoryStorage
from .server import SpecStoryAutoLoaderServer

__version__ = "1.0.0"
__all__ = ["SpecStoryAutoLoaderServer", "SimplifiedSpecStoryStorage"]
