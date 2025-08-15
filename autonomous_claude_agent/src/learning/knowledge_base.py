"""
Knowledge Base - Stores and retrieves learned knowledge
"""

import asyncio
import json
import sqlite3
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
from collections import defaultdict
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from src.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge that can be stored"""
    FACT = "fact"                    # Factual information
    PROCEDURE = "procedure"          # How to do something
    CONCEPT = "concept"              # Conceptual understanding
    SOLUTION = "solution"            # Problem solutions
    REFERENCE = "reference"          # External references
    HEURISTIC = "heuristic"         # Rules of thumb
    CONSTRAINT = "constraint"       # Limitations and constraints
    OPTIMIZATION = "optimization"   # Performance optimizations


@dataclass
class KnowledgeEntry:
    """Represents a piece of knowledge"""
    id: str
    type: KnowledgeType
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    confidence: float = 1.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['type'] = self.type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        # Don't serialize embeddings directly
        if 'embeddings' in data:
            del data['embeddings']
        return data


class KnowledgeBase:
    """Manages the agent's knowledge base"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / '.autonomous_claude' / 'knowledge.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.cache: Dict[str, KnowledgeEntry] = {}
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.type_index: Dict[KnowledgeType, Set[str]] = defaultdict(set)
        
        # Embedding model for semantic search
        if SentenceTransformer is not None:
            try:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                self.has_embeddings = True
            except:
                logger.warning("Sentence transformer model loading failed, semantic search disabled")
                self.encoder = None
                self.has_embeddings = False
        else:
            logger.warning("Sentence transformer not available, semantic search disabled")
            self.encoder = None
            self.has_embeddings = False
        
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        
        self._lock = asyncio.Lock()
        self._init_database()
        self._load_knowledge()
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata TEXT,
                    embeddings BLOB
                )
            ''')
            
            # Create indices for faster queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON knowledge(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON knowledge(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_usage ON knowledge(usage_count DESC)')
            
            conn.commit()
    
    def _load_knowledge(self):
        """Load knowledge from database into cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM knowledge WHERE expires_at IS NULL OR expires_at > ?',
                                 (datetime.now().isoformat(),))
            
            for row in cursor:
                try:
                    entry = self._row_to_entry(row)
                    self.cache[entry.id] = entry
                    self._update_indices(entry)
                    
                    # Load embeddings if available
                    if row['embeddings']:
                        self.embeddings_cache[entry.id] = pickle.loads(row['embeddings'])
                        
                except Exception as e:
                    logger.error(f"Failed to load knowledge entry: {e}")
        
        logger.info(f"Loaded {len(self.cache)} knowledge entries")
    
    def _row_to_entry(self, row: sqlite3.Row) -> KnowledgeEntry:
        """Convert database row to KnowledgeEntry"""
        return KnowledgeEntry(
            id=row['id'],
            type=KnowledgeType(row['type']),
            title=row['title'],
            content=row['content'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            source=row['source'],
            confidence=row['confidence'],
            usage_count=row['usage_count'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _update_indices(self, entry: KnowledgeEntry):
        """Update search indices for an entry"""
        # Update tag index
        for tag in entry.tags:
            self.tag_index[tag].add(entry.id)
        
        # Update type index
        self.type_index[entry.type].add(entry.id)
    
    async def add_knowledge(self, entry: KnowledgeEntry) -> bool:
        """Add new knowledge to the base"""
        async with self._lock:
            try:
                # Generate ID if not provided
                if not entry.id:
                    content_hash = hashlib.md5(entry.content.encode()).hexdigest()[:8]
                    entry.id = f"{entry.type.value}_{content_hash}"
                
                # Check for duplicates
                if entry.id in self.cache:
                    # Update existing entry
                    existing = self.cache[entry.id]
                    existing.content = entry.content
                    existing.updated_at = datetime.now()
                    existing.usage_count += 1
                    existing.confidence = max(existing.confidence, entry.confidence)
                    entry = existing
                else:
                    # Add new entry
                    self.cache[entry.id] = entry
                    self._update_indices(entry)
                
                # Generate embeddings if available
                if self.has_embeddings and self.encoder:
                    text = f"{entry.title} {entry.content}"
                    embeddings = self.encoder.encode(text)
                    self.embeddings_cache[entry.id] = embeddings
                    entry.embeddings = embeddings
                
                # Save to database
                self._save_entry(entry)
                
                logger.info(f"Added knowledge: {entry.id} ({entry.type.value})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to add knowledge: {e}")
                return False
    
    def _save_entry(self, entry: KnowledgeEntry):
        """Save entry to database"""
        with sqlite3.connect(self.db_path) as conn:
            embeddings_blob = None
            if entry.id in self.embeddings_cache:
                embeddings_blob = pickle.dumps(self.embeddings_cache[entry.id])
            
            conn.execute('''
                INSERT OR REPLACE INTO knowledge 
                (id, type, title, content, tags, source, confidence, usage_count, 
                 created_at, updated_at, expires_at, metadata, embeddings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id,
                entry.type.value,
                entry.title,
                entry.content,
                json.dumps(entry.tags),
                entry.source,
                entry.confidence,
                entry.usage_count,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
                entry.expires_at.isoformat() if entry.expires_at else None,
                json.dumps(entry.metadata),
                embeddings_blob
            ))
            conn.commit()
    
    async def search(self, query: str, limit: int = 10, 
                    knowledge_type: Optional[KnowledgeType] = None) -> List[KnowledgeEntry]:
        """Search for knowledge entries"""
        
        results = []
        
        # Filter by type if specified
        if knowledge_type:
            candidate_ids = self.type_index.get(knowledge_type, set())
            candidates = [self.cache[id] for id in candidate_ids if id in self.cache]
        else:
            candidates = list(self.cache.values())
        
        # Semantic search if embeddings available
        if self.has_embeddings and self.encoder and candidates:
            query_embedding = self.encoder.encode(query)
            
            scores = []
            for entry in candidates:
                if entry.id in self.embeddings_cache:
                    entry_embedding = self.embeddings_cache[entry.id]
                    # Cosine similarity
                    similarity = np.dot(query_embedding, entry_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(entry_embedding)
                    )
                    scores.append((entry, similarity))
                else:
                    # Fallback to keyword matching
                    score = self._keyword_score(query, entry)
                    scores.append((entry, score))
            
            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)
            results = [entry for entry, _ in scores[:limit]]
            
        else:
            # Fallback to keyword search
            scored = []
            for entry in candidates:
                score = self._keyword_score(query, entry)
                if score > 0:
                    scored.append((entry, score))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            results = [entry for entry, _ in scored[:limit]]
        
        # Update usage counts
        for entry in results:
            entry.usage_count += 1
            self._save_entry(entry)
        
        return results
    
    def _keyword_score(self, query: str, entry: KnowledgeEntry) -> float:
        """Calculate keyword relevance score"""
        score = 0.0
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Title match
        title_lower = entry.title.lower()
        if query_lower in title_lower:
            score += 10.0
        for word in query_words:
            if word in title_lower:
                score += 2.0
        
        # Content match
        content_lower = entry.content.lower()
        if query_lower in content_lower:
            score += 5.0
        for word in query_words:
            if word in content_lower:
                score += 1.0
        
        # Tag match
        for tag in entry.tags:
            if tag.lower() in query_lower:
                score += 3.0
        
        # Weight by confidence and usage
        score *= entry.confidence
        score += np.log1p(entry.usage_count) * 0.5
        
        return score
    
    async def get_by_tags(self, tags: List[str], match_all: bool = False) -> List[KnowledgeEntry]:
        """Get knowledge entries by tags"""
        
        if match_all:
            # Get entries that have all tags
            entry_ids = None
            for tag in tags:
                tag_entries = self.tag_index.get(tag, set())
                if entry_ids is None:
                    entry_ids = tag_entries.copy()
                else:
                    entry_ids &= tag_entries
            
            if entry_ids:
                return [self.cache[id] for id in entry_ids if id in self.cache]
        else:
            # Get entries that have any tag
            entry_ids = set()
            for tag in tags:
                entry_ids.update(self.tag_index.get(tag, set()))
            
            if entry_ids:
                return [self.cache[id] for id in entry_ids if id in self.cache]
        
        return []
    
    async def get_by_type(self, knowledge_type: KnowledgeType) -> List[KnowledgeEntry]:
        """Get all knowledge entries of a specific type"""
        entry_ids = self.type_index.get(knowledge_type, set())
        return [self.cache[id] for id in entry_ids if id in self.cache]
    
    async def update_knowledge(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing knowledge entry"""
        async with self._lock:
            if entry_id not in self.cache:
                return False
            
            entry = self.cache[entry_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            entry.updated_at = datetime.now()
            
            # Re-generate embeddings if content changed
            if 'content' in updates or 'title' in updates:
                if self.has_embeddings and self.encoder:
                    text = f"{entry.title} {entry.content}"
                    embeddings = self.encoder.encode(text)
                    self.embeddings_cache[entry.id] = embeddings
            
            # Update indices if tags changed
            if 'tags' in updates:
                # Remove old tag associations
                for tag in entry.tags:
                    self.tag_index[tag].discard(entry_id)
                # Add new ones
                for tag in updates['tags']:
                    self.tag_index[tag].add(entry_id)
            
            self._save_entry(entry)
            return True
    
    async def remove_knowledge(self, entry_id: str) -> bool:
        """Remove a knowledge entry"""
        async with self._lock:
            if entry_id not in self.cache:
                return False
            
            entry = self.cache[entry_id]
            
            # Remove from indices
            for tag in entry.tags:
                self.tag_index[tag].discard(entry_id)
            self.type_index[entry.type].discard(entry_id)
            
            # Remove from cache
            del self.cache[entry_id]
            if entry_id in self.embeddings_cache:
                del self.embeddings_cache[entry_id]
            
            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM knowledge WHERE id = ?', (entry_id,))
                conn.commit()
            
            logger.info(f"Removed knowledge: {entry_id}")
            return True
    
    async def cleanup_expired(self) -> int:
        """Remove expired knowledge entries"""
        async with self._lock:
            expired = []
            now = datetime.now()
            
            for entry_id, entry in self.cache.items():
                if entry.expires_at and entry.expires_at < now:
                    expired.append(entry_id)
            
            for entry_id in expired:
                await self.remove_knowledge(entry_id)
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired knowledge entries")
            
            return len(expired)
    
    async def get_related(self, entry_id: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Get related knowledge entries"""
        
        if entry_id not in self.cache:
            return []
        
        entry = self.cache[entry_id]
        
        # Use semantic similarity if available
        if self.has_embeddings and entry_id in self.embeddings_cache:
            query_embedding = self.embeddings_cache[entry_id]
            
            scores = []
            for other_id, other_entry in self.cache.items():
                if other_id != entry_id and other_id in self.embeddings_cache:
                    other_embedding = self.embeddings_cache[other_id]
                    similarity = np.dot(query_embedding, other_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(other_embedding)
                    )
                    scores.append((other_entry, similarity))
            
            scores.sort(key=lambda x: x[1], reverse=True)
            return [entry for entry, _ in scores[:limit]]
        
        # Fallback to tag-based similarity
        related = []
        for tag in entry.tags:
            tag_entries = await self.get_by_tags([tag])
            for other_entry in tag_entries:
                if other_entry.id != entry_id:
                    related.append(other_entry)
        
        # Deduplicate and return
        seen = set()
        unique = []
        for entry in related:
            if entry.id not in seen:
                seen.add(entry.id)
                unique.append(entry)
        
        return unique[:limit]
    
    async def merge_knowledge(self, entry_id1: str, entry_id2: str) -> Optional[str]:
        """Merge two knowledge entries"""
        async with self._lock:
            if entry_id1 not in self.cache or entry_id2 not in self.cache:
                return None
            
            entry1 = self.cache[entry_id1]
            entry2 = self.cache[entry_id2]
            
            # Create merged entry
            merged = KnowledgeEntry(
                id=f"merged_{entry_id1}_{entry_id2}",
                type=entry1.type,  # Use first entry's type
                title=f"{entry1.title} + {entry2.title}",
                content=f"{entry1.content}\n\n---\n\n{entry2.content}",
                tags=list(set(entry1.tags + entry2.tags)),
                source=f"{entry1.source}, {entry2.source}" if entry1.source and entry2.source else None,
                confidence=max(entry1.confidence, entry2.confidence),
                usage_count=entry1.usage_count + entry2.usage_count,
                metadata={**entry1.metadata, **entry2.metadata}
            )
            
            # Add merged entry
            await self.add_knowledge(merged)
            
            # Remove original entries
            await self.remove_knowledge(entry_id1)
            await self.remove_knowledge(entry_id2)
            
            return merged.id
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        
        total = len(self.cache)
        by_type = {
            ktype.value: len(self.type_index[ktype])
            for ktype in KnowledgeType
        }
        
        # Most used entries
        most_used = sorted(
            self.cache.values(),
            key=lambda e: e.usage_count,
            reverse=True
        )[:5]
        
        # Tag statistics
        tag_counts = {
            tag: len(entries)
            for tag, entries in self.tag_index.items()
        }
        
        return {
            'total_entries': total,
            'by_type': by_type,
            'total_tags': len(self.tag_index),
            'top_tags': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'most_used': [
                {
                    'id': e.id,
                    'title': e.title,
                    'type': e.type.value,
                    'usage_count': e.usage_count
                }
                for e in most_used
            ],
            'has_embeddings': self.has_embeddings,
            'embeddings_count': len(self.embeddings_cache)
        }
    
    async def export_knowledge(self, output_file: Path, 
                              knowledge_type: Optional[KnowledgeType] = None):
        """Export knowledge to JSON file"""
        
        if knowledge_type:
            entries = await self.get_by_type(knowledge_type)
        else:
            entries = list(self.cache.values())
        
        data = [entry.to_dict() for entry in entries]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(data)} knowledge entries to {output_file}")
    
    async def import_knowledge(self, input_file: Path) -> int:
        """Import knowledge from JSON file"""
        
        with open(input_file) as f:
            data = json.load(f)
        
        imported = 0
        for item in data:
            try:
                entry = KnowledgeEntry(
                    id=item.get('id', ''),
                    type=KnowledgeType(item['type']),
                    title=item['title'],
                    content=item['content'],
                    tags=item.get('tags', []),
                    source=item.get('source'),
                    confidence=item.get('confidence', 1.0),
                    usage_count=item.get('usage_count', 0),
                    metadata=item.get('metadata', {})
                )
                
                if await self.add_knowledge(entry):
                    imported += 1
                    
            except Exception as e:
                logger.error(f"Failed to import entry: {e}")
        
        logger.info(f"Imported {imported} knowledge entries from {input_file}")
        return imported