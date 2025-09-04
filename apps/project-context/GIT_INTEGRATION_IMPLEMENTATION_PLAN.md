# Git History Integration Implementation Plan

## Executive Summary

Based on comprehensive research of Git history analysis patterns and the existing unified context system architecture, this plan provides concrete implementation steps to extend the temporal knowledge graph with Git history correlation. The implementation leverages pygit2 for performance, extends the existing TimescaleDB schema, and integrates seamlessly with the current adapter pattern.

## 1. Implementation Phases

### Phase 1: Foundation Enhancement (Weeks 1-2)
**Goal**: Upgrade existing git_adapter.py and database schema for enhanced performance

#### Week 1: Library Migration and Schema Updates

**Day 1-2: pygit2 Integration**
```bash
# Install pygit2 dependencies
apt-get update
apt-get install -y libgit2-dev python3-dev
pip install pygit2==1.13.3

# Update git_adapter.py imports
```

**Enhanced git_adapter.py Implementation**:
```python
# src/project_context/ingestion/adapters/git_adapter_enhanced.py
import pygit2
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator, Dict, Any, Optional
from datetime import datetime, timezone

class EnhancedGitAdapter(GitAdapter):
    """Enhanced Git adapter using pygit2 for better performance"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.repo = None
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.author_cache = {}
        self.commit_cache = LRUCache(maxsize=10000)

    async def initialize(self) -> None:
        """Initialize with pygit2 repository"""
        self.logger.info("Initializing enhanced git adapter with pygit2")

        # Initialize repository in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.repo = await loop.run_in_executor(
            None,
            self._init_pygit2_repo
        )

        # Validate repository
        if not self.repo:
            raise ValueError(f"Failed to initialize git repository at {self._repo_path}")

        # Cache repository metadata
        self.repo_metadata = await self._collect_repository_metadata()

        self.logger.info(
            "Enhanced git adapter initialized successfully",
            repo_path=self._repo_path,
            total_commits=len(list(self.repo.walk(self.repo.head.target))),
            branches=len(list(self.repo.branches))
        )

    def _init_pygit2_repo(self) -> Optional[pygit2.Repository]:
        """Initialize pygit2 repository in thread"""
        try:
            return pygit2.Repository(self._repo_path)
        except Exception as e:
            self.logger.error(f"Failed to initialize pygit2 repository: {e}")
            return None

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch git data using optimized pygit2 operations"""

        count = 0
        batch_size = min(self.config.batch_size, 100)

        # Fetch commits in batches using thread pool
        async for commit_batch in self._fetch_commits_batched(since, until, batch_size):
            for commit in commit_batch:
                if limit and count >= limit:
                    return

                yield commit
                count += 1

                # Yield control periodically
                if count % 50 == 0:
                    await asyncio.sleep(0.001)

    async def _fetch_commits_batched(
        self,
        since: Optional[datetime],
        until: Optional[datetime],
        batch_size: int
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Fetch commits in optimized batches"""

        def _fetch_commit_range(start_idx: int, batch_size: int) -> List[Dict[str, Any]]:
            commits = []
            walker = self.repo.walk(self.repo.head.target)

            # Skip to start position
            for _ in range(start_idx):
                try:
                    next(walker)
                except StopIteration:
                    return commits

            # Collect batch
            for _ in range(batch_size):
                try:
                    commit = next(walker)

                    # Apply time filters
                    commit_time = datetime.fromtimestamp(commit.commit_time, timezone.utc)
                    if since and commit_time < since:
                        break
                    if until and commit_time > until:
                        continue

                    commit_data = self._extract_commit_data(commit)
                    commits.append(commit_data)

                except StopIteration:
                    break

            return commits

        # Fetch commits in parallel batches
        start_idx = 0
        loop = asyncio.get_event_loop()

        while True:
            batch = await loop.run_in_executor(
                self.thread_pool,
                _fetch_commit_range,
                start_idx,
                batch_size
            )

            if not batch:
                break

            yield batch
            start_idx += batch_size

    def _extract_commit_data(self, commit: pygit2.Commit) -> Dict[str, Any]:
        """Extract commit data optimized for correlation"""

        # Get file changes efficiently
        changed_files = []
        if commit.parents:
            parent = commit.parents[0]
            diff = self.repo.diff(parent.tree, commit.tree)

            for delta in diff.deltas:
                changed_files.append({
                    'type': self._map_git_delta_to_type(delta.status),
                    'file': delta.new_file.path or delta.old_file.path,
                    'old_path': delta.old_file.path if delta.status == pygit2.GIT_DELTA_RENAMED else None
                })
        else:
            # Initial commit - all files are added
            for entry in commit.tree:
                changed_files.append({
                    'type': 'A',
                    'file': entry.name
                })

        # Build comprehensive commit data
        commit_data = {
            'type': 'commit',
            'hash': str(commit.id),
            'short_hash': str(commit.id)[:8],
            'author': commit.author.name,
            'author_email': commit.author.email,
            'author_date': datetime.fromtimestamp(commit.author.time, timezone.utc).isoformat(),
            'committer': commit.committer.name,
            'committer_email': commit.committer.email,
            'commit_date': datetime.fromtimestamp(commit.commit_time, timezone.utc).isoformat(),
            'subject': commit.message.split('\n')[0] if commit.message else '',
            'body': '\n'.join(commit.message.split('\n')[1:]).strip() if commit.message else '',
            'parent_commits': [str(p.id) for p in commit.parents],
            'changed_files': changed_files,
            'files_changed_count': len(changed_files),
            'is_merge': len(commit.parents) > 1,
            'tree_id': str(commit.tree.id)
        }

        return commit_data
```

**Day 3-4: Database Schema Enhancement**
```sql
-- migrations/001_git_enhanced_schema.sql
-- Enhanced Git storage schema

-- Authors table for identity resolution
CREATE TABLE IF NOT EXISTS git_authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    normalized_email VARCHAR(255),
    first_commit_timestamp TIMESTAMPTZ,
    last_commit_timestamp TIMESTAMPTZ,
    total_commits INTEGER DEFAULT 0,
    repositories TEXT[], -- Array of repository paths
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_git_author_email UNIQUE(email)
);

-- Repository registry
CREATE TABLE IF NOT EXISTS git_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path TEXT NOT NULL UNIQUE,
    name VARCHAR(255),
    origin_url TEXT,
    default_branch VARCHAR(255) DEFAULT 'main',
    last_scan_timestamp TIMESTAMPTZ,
    last_commit_sha VARCHAR(64),
    total_commits INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Repository metadata
    language_distribution JSONB DEFAULT '{}',
    primary_language VARCHAR(100),
    repository_size_mb INTEGER DEFAULT 0
);

-- Enhanced commit storage (extends context_items)
CREATE TABLE IF NOT EXISTS git_commit_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_item_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES git_repositories(id),
    author_id UUID REFERENCES git_authors(id),
    committer_id UUID REFERENCES git_authors(id),

    -- Enhanced commit data
    commit_sha VARCHAR(64) NOT NULL,
    short_sha VARCHAR(12) NOT NULL,
    tree_sha VARCHAR(64),
    parent_shas TEXT[], -- Array of parent commit SHAs

    -- Change statistics
    files_added INTEGER DEFAULT 0,
    files_modified INTEGER DEFAULT 0,
    files_deleted INTEGER DEFAULT 0,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,

    -- Commit classification
    commit_type VARCHAR(50), -- 'feature', 'bugfix', 'refactor', 'docs', 'test'
    is_merge_commit BOOLEAN DEFAULT FALSE,
    merge_base_distance INTEGER DEFAULT 0,

    -- Analysis results
    complexity_score FLOAT,
    impact_score FLOAT, -- 0.0 to 1.0
    risk_score FLOAT, -- 0.0 to 1.0

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_repo_commit UNIQUE(repository_id, commit_sha)
);

-- File change tracking
CREATE TABLE IF NOT EXISTS git_file_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_detail_id UUID NOT NULL REFERENCES git_commit_details(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    old_path TEXT, -- For renames
    change_type VARCHAR(10) NOT NULL, -- 'A', 'M', 'D', 'R', 'C'

    -- File metadata
    file_size_bytes INTEGER,
    language VARCHAR(50),
    file_category VARCHAR(50), -- 'source', 'test', 'config', 'docs'

    -- Change metrics
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optimized indexes
CREATE INDEX IF NOT EXISTS idx_git_commit_details_repo_timestamp
    ON git_commit_details(repository_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_git_commit_details_author
    ON git_commit_details(author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_git_commit_details_sha
    ON git_commit_details(commit_sha);
CREATE INDEX IF NOT EXISTS idx_git_file_changes_path
    ON git_file_changes(file_path, change_type);
```

**Day 5: Integration Testing**
```python
# tests/test_enhanced_git_adapter.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.project_context.ingestion.adapters.git_adapter_enhanced import EnhancedGitAdapter

@pytest.fixture
async def enhanced_git_adapter():
    config = AdapterConfig(
        adapter_id="git_enhanced",
        source_type="git",
        batch_mode=BatchMode.STREAM,
        batch_size=100
    )
    adapter = EnhancedGitAdapter(config)
    await adapter.initialize()
    return adapter

async def test_commit_fetching_performance(enhanced_git_adapter):
    """Test that pygit2 implementation is faster than subprocess"""
    import time

    start_time = time.time()
    commits = []
    async for commit in enhanced_git_adapter.fetch_items(limit=1000):
        commits.append(commit)

    duration = time.time() - start_time

    # Should process 1000 commits in under 10 seconds
    assert duration < 10.0
    assert len(commits) <= 1000
    assert all('hash' in commit for commit in commits)

async def test_commit_data_quality(enhanced_git_adapter):
    """Test data extraction quality"""
    commits = []
    async for commit in enhanced_git_adapter.fetch_items(limit=10):
        commits.append(commit)

    for commit in commits:
        # Verify required fields
        assert 'hash' in commit
        assert 'author' in commit
        assert 'commit_date' in commit
        assert 'changed_files' in commit

        # Verify data types
        assert isinstance(commit['changed_files'], list)
        assert isinstance(commit['parent_commits'], list)
        assert commit['files_changed_count'] == len(commit['changed_files'])
```

#### Week 2: Repository Management and Author Resolution

**Day 1-2: Repository Registry Implementation**
```python
# src/project_context/ingestion/git_repository_manager.py
class GitRepositoryManager:
    """Manages Git repository registration and metadata"""

    def __init__(self, database: IngestionDatabase):
        self.database = database
        self.author_resolver = GitAuthorResolver()

    async def register_repository(self, repo_path: str, config: Dict) -> UUID:
        """Register repository in the system"""

        # Check if already registered
        existing_repo = await self._get_repository_by_path(repo_path)
        if existing_repo:
            return existing_repo['id']

        # Collect repository metadata
        repo_metadata = await self._analyze_repository(repo_path)

        # Insert repository record
        repo_id = await self.database.execute_query("""
            INSERT INTO git_repositories (
                path, name, origin_url, default_branch,
                language_distribution, primary_language, repository_size_mb
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """,
        repo_metadata['path'],
        repo_metadata['name'],
        repo_metadata['origin_url'],
        repo_metadata['default_branch'],
        json.dumps(repo_metadata['languages']),
        repo_metadata['primary_language'],
        repo_metadata['size_mb']
        )

        return repo_id

    async def _analyze_repository(self, repo_path: str) -> Dict:
        """Analyze repository for metadata collection"""

        repo = pygit2.Repository(repo_path)

        # Basic repository info
        origin_url = None
        try:
            origin_remote = repo.remotes['origin']
            origin_url = origin_remote.url
        except KeyError:
            pass

        # Language analysis
        languages = await self._analyze_repository_languages(repo_path)

        # Size calculation
        size_mb = await self._calculate_repository_size(repo_path)

        return {
            'path': repo_path,
            'name': os.path.basename(repo_path),
            'origin_url': origin_url,
            'default_branch': repo.head.shorthand,
            'languages': languages,
            'primary_language': max(languages.items(), key=lambda x: x[1])[0] if languages else None,
            'size_mb': size_mb
        }

class GitAuthorResolver:
    """Resolves Git author identities and handles aliases"""

    def __init__(self, database: IngestionDatabase):
        self.database = database
        self.author_cache = {}

    async def resolve_author(self, name: str, email: str) -> UUID:
        """Resolve author identity, creating if necessary"""

        # Normalize email
        normalized_email = email.lower().strip()

        # Check cache first
        cache_key = f"{name}:{normalized_email}"
        if cache_key in self.author_cache:
            return self.author_cache[cache_key]

        # Check database
        existing_author = await self._find_existing_author(normalized_email, name)
        if existing_author:
            author_id = existing_author['id']
            self.author_cache[cache_key] = author_id
            return author_id

        # Create new author
        author_id = await self._create_new_author(name, email, normalized_email)
        self.author_cache[cache_key] = author_id
        return author_id

    async def _find_existing_author(self, normalized_email: str, name: str) -> Optional[Dict]:
        """Find existing author by email or name patterns"""

        # Direct email match
        result = await self.database.fetch_one("""
            SELECT * FROM git_authors WHERE normalized_email = $1
        """, normalized_email)

        if result:
            return result

        # Name-based fuzzy matching for same email domain
        email_domain = normalized_email.split('@')[1] if '@' in normalized_email else None
        if email_domain:
            similar_authors = await self.database.fetch_all("""
                SELECT * FROM git_authors
                WHERE normalized_email LIKE $1
                AND similarity(name, $2) > 0.7
            """, f"%{email_domain}", name)

            if similar_authors:
                return similar_authors[0]  # Return most similar

        return None

    async def _create_new_author(self, name: str, email: str, normalized_email: str) -> UUID:
        """Create new author record"""

        return await self.database.execute_query("""
            INSERT INTO git_authors (name, email, normalized_email)
            VALUES ($1, $2, $3)
            RETURNING id
        """, name, email, normalized_email)
```

**Day 3-4: Enhanced Data Transformation**
```python
# Enhanced transform_item method for git_adapter_enhanced.py
async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
    """Transform raw git item with enhanced correlation data"""

    if raw_item["type"] != "commit":
        return await super().transform_item(raw_item)

    # Create base context item
    item = self.transformer.create_base_context_item(
        source_type="git",
        source_id=raw_item["hash"],
        raw_data=raw_item
    )

    # Enhanced commit transformation
    item.title = raw_item.get("subject", f"Commit {raw_item['short_hash']}")
    item.content = await self._build_enhanced_commit_content(raw_item)
    item.actor_id = raw_item.get("author", "unknown")
    item.actor_type = "human"

    # Parse timestamp
    commit_date_str = raw_item.get("commit_date", "")
    if commit_date_str:
        item.timestamp = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
    else:
        item.timestamp = datetime.utcnow()

    # Enhanced metrics for correlation
    enhanced_metrics = {
        # Basic Git data
        "commit_sha": raw_item["hash"],
        "short_sha": raw_item["short_hash"],
        "author": raw_item.get("author", ""),
        "author_email": raw_item.get("author_email", ""),
        "parent_commits": raw_item.get("parent_commits", []),
        "is_merge": raw_item.get("is_merge", False),

        # File changes
        "changed_files": [f["file"] for f in raw_item.get("changed_files", [])],
        "files_added": len([f for f in raw_item.get("changed_files", []) if f["type"] == "A"]),
        "files_modified": len([f for f in raw_item.get("changed_files", []) if f["type"] == "M"]),
        "files_deleted": len([f for f in raw_item.get("changed_files", []) if f["type"] == "D"]),
        "total_files_changed": raw_item.get("files_changed_count", 0),

        # Commit classification
        "commit_type": await self._classify_commit(raw_item),
        "impact_score": await self._calculate_impact_score(raw_item),
        "risk_score": await self._calculate_risk_score(raw_item),

        # Language analysis
        "languages_affected": await self._analyze_affected_languages(raw_item),
        "file_categories": await self._categorize_changed_files(raw_item),

        # Correlation hints
        "potential_error_fix": await self._detect_error_fix_pattern(raw_item),
        "potential_feature": await self._detect_feature_pattern(raw_item),
        "refactoring_indicator": await self._detect_refactoring_pattern(raw_item)
    }

    item.metrics = enhanced_metrics
    item.entity_type = "commit"

    # Enhanced tagging
    tags = await self._generate_enhanced_tags(raw_item, enhanced_metrics)
    item.tags = tags

    # Apply transformations
    item = await self.transformer.transform_item(item)

    return item

async def _classify_commit(self, commit_data: Dict) -> str:
    """Classify commit type based on message and changes"""

    subject = commit_data.get("subject", "").lower()
    changed_files = commit_data.get("changed_files", [])

    # Test commits
    if any("test" in f["file"].lower() for f in changed_files):
        return "test"

    # Documentation commits
    if any(f["file"].lower().endswith(('.md', '.txt', '.rst')) for f in changed_files):
        return "docs"

    # Bug fix indicators
    if any(keyword in subject for keyword in ["fix", "bug", "issue", "patch", "hotfix"]):
        return "bugfix"

    # Feature indicators
    if any(keyword in subject for keyword in ["feat", "add", "new", "implement"]):
        return "feature"

    # Refactoring indicators
    if any(keyword in subject for keyword in ["refactor", "cleanup", "restructure", "optimize"]):
        return "refactor"

    # Configuration changes
    if any(f["file"].lower().endswith(('.json', '.yml', '.yaml', '.toml', '.ini')) for f in changed_files):
        return "config"

    return "other"

async def _calculate_impact_score(self, commit_data: Dict) -> float:
    """Calculate impact score based on files and lines changed"""

    files_changed = commit_data.get("files_changed_count", 0)
    changed_files = commit_data.get("changed_files", [])

    # Base score from file count (normalized to 0-1)
    file_score = min(1.0, files_changed / 20.0)

    # Boost score for critical files
    critical_file_boost = 0.0
    for file_change in changed_files:
        file_path = file_change["file"].lower()
        if any(pattern in file_path for pattern in [
            "main.", "index.", "app.", "server.", "config", "setup"
        ]):
            critical_file_boost += 0.2

    # Boost score for certain file types
    important_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'}
    extension_boost = sum(0.1 for f in changed_files
                         if any(f["file"].endswith(ext) for ext in important_extensions))

    total_score = min(1.0, file_score + critical_file_boost + extension_boost)
    return round(total_score, 3)
```

**Day 5: Integration and Testing**
```python
# Integration test for complete pipeline
async def test_enhanced_git_pipeline():
    """Test complete enhanced git pipeline"""

    # Initialize components
    config = AdapterConfig(
        adapter_id="git_enhanced",
        source_type="git",
        batch_size=50
    )

    adapter = EnhancedGitAdapter(config)
    await adapter.initialize()

    repo_manager = GitRepositoryManager(database)
    author_resolver = GitAuthorResolver(database)

    # Register repository
    repo_id = await repo_manager.register_repository(".", {})

    # Process commits
    processed_count = 0
    async for raw_commit in adapter.fetch_items(limit=100):
        context_item = await adapter.transform_item(raw_commit)

        # Store enhanced commit details
        commit_detail_id = await store_git_commit_details(
            context_item, repo_id, raw_commit, author_resolver
        )

        processed_count += 1

    assert processed_count > 0
    print(f"Successfully processed {processed_count} commits")
```

### Phase 2: Real-time Integration (Weeks 3-4)

#### Week 3: Event-Driven Updates

**Day 1-2: Git Hook Integration**
```python
# src/project_context/ingestion/git_hooks.py
class GitHookManager:
    """Manages Git hooks for real-time updates"""

    def __init__(self, ingestion_service: IngestionService):
        self.ingestion = ingestion_service
        self.hook_processors = {
            'post-commit': self._process_post_commit,
            'post-receive': self._process_post_receive,
            'post-merge': self._process_post_merge
        }

    async def setup_repository_hooks(self, repo_path: str) -> None:
        """Set up Git hooks for a repository"""

        hooks_dir = Path(repo_path) / '.git' / 'hooks'
        hooks_dir.mkdir(exist_ok=True)

        # Create hook scripts
        for hook_name in self.hook_processors.keys():
            await self._create_hook_script(hooks_dir / hook_name, hook_name)

    async def _create_hook_script(self, hook_path: Path, hook_name: str):
        """Create Git hook script"""

        script_content = f'''#!/bin/bash
# Unified Context System Git Hook
REPO_PATH="$(git rev-parse --show-toplevel)"
COMMIT_SHA="$(git rev-parse HEAD)"

# Send notification to ingestion service
curl -X POST \\
  -H "Content-Type: application/json" \\
  -d '{{"repository_path": "'"$REPO_PATH"'", "hook_type": "{hook_name}", "commit_sha": "'"$COMMIT_SHA"'", "timestamp": "$(date -Iseconds)"}}' \\
  http://localhost:8000/api/git-hooks/process \\
  2>/dev/null || true
'''

        hook_path.write_text(script_content)
        hook_path.chmod(0o755)

    async def process_hook_event(self, event_data: Dict) -> None:
        """Process incoming Git hook event"""

        hook_type = event_data.get('hook_type')
        processor = self.hook_processors.get(hook_type)

        if processor:
            await processor(event_data)
        else:
            logger.warning(f"No processor for hook type: {hook_type}")

    async def _process_post_commit(self, event_data: Dict) -> None:
        """Process post-commit hook"""

        repo_path = event_data['repository_path']
        commit_sha = event_data['commit_sha']

        # Process the single new commit
        await self.ingestion.process_incremental_commit(repo_path, commit_sha)

        # Trigger relationship detection
        await self.ingestion.trigger_relationship_detection(repo_path, commit_sha)
```

**Day 3-4: Incremental Processing**
```python
# src/project_context/ingestion/incremental_processor.py
class IncrementalGitProcessor:
    """Handles incremental Git processing for real-time updates"""

    def __init__(self, database: IngestionDatabase, git_adapter: EnhancedGitAdapter):
        self.database = database
        self.git_adapter = git_adapter
        self.correlation_engine = GitCorrelationEngine(database)

    async def process_incremental_commit(self, repo_path: str, commit_sha: str) -> None:
        """Process a single commit incrementally"""

        # Get repository info
        repo_info = await self._get_repository_info(repo_path)
        if not repo_info:
            logger.error(f"Repository not registered: {repo_path}")
            return

        # Check if commit already processed
        if await self._is_commit_processed(repo_info['id'], commit_sha):
            logger.info(f"Commit already processed: {commit_sha}")
            return

        # Extract commit data
        commit_data = await self._extract_single_commit(repo_path, commit_sha)
        if not commit_data:
            return

        # Transform to context item
        context_item = await self.git_adapter.transform_item(commit_data)

        # Store in database
        await self._store_commit_incremental(context_item, repo_info, commit_data)

        # Trigger correlation analysis
        await self.correlation_engine.analyze_commit_correlations(context_item)

        logger.info(f"Processed incremental commit: {commit_sha[:8]}")

    async def _extract_single_commit(self, repo_path: str, commit_sha: str) -> Optional[Dict]:
        """Extract data for a single commit"""

        try:
            repo = pygit2.Repository(repo_path)
            commit = repo[commit_sha]

            # Use same extraction logic as batch processing
            commit_data = self.git_adapter._extract_commit_data(commit)
            return commit_data

        except Exception as e:
            logger.error(f"Failed to extract commit {commit_sha}: {e}")
            return None

    async def catch_up_missed_commits(self, repo_path: str) -> int:
        """Catch up any commits that were missed"""

        repo_info = await self._get_repository_info(repo_path)
        if not repo_info:
            return 0

        # Get last processed commit
        last_processed = repo_info.get('last_commit_sha')
        if not last_processed:
            # Full processing needed
            return await self._trigger_full_processing(repo_path)

        # Find commits since last processed
        missed_commits = await self._find_commits_since(repo_path, last_processed)

        processed_count = 0
        for commit_sha in missed_commits:
            await self.process_incremental_commit(repo_path, commit_sha)
            processed_count += 1

        logger.info(f"Caught up {processed_count} missed commits for {repo_path}")
        return processed_count
```

**Day 5: Webhook Integration**
```python
# src/project_context/server/git_webhook_handler.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

class GitHookEvent(BaseModel):
    repository_path: str
    hook_type: str
    commit_sha: str
    timestamp: str

router = APIRouter(prefix="/api/git-hooks")

@router.post("/process")
async def process_git_hook(
    event: GitHookEvent,
    background_tasks: BackgroundTasks
):
    """Handle Git hook events"""

    # Add to background processing queue
    background_tasks.add_task(
        process_git_hook_background,
        event.dict()
    )

    return {"status": "accepted", "message": "Git hook event queued for processing"}

async def process_git_hook_background(event_data: Dict[str, Any]):
    """Background processing of Git hook events"""

    try:
        hook_manager = GitHookManager(ingestion_service)
        await hook_manager.process_hook_event(event_data)

    except Exception as e:
        logger.error(f"Failed to process Git hook event: {e}")
```

#### Week 4: Correlation Engine Implementation

**Day 1-3: Advanced Correlation Algorithms**
```python
# src/project_context/analysis/git_correlation_engine.py
class GitCorrelationEngine:
    """Advanced correlation engine for Git history integration"""

    def __init__(self, database: IngestionDatabase):
        self.database = database
        self.correlators = [
            ErrorCommitCorrelator(),
            ChatCommitCorrelator(),
            FileActivityCorrelator(),
            AuthorPatternCorrelator()
        ]

    async def analyze_commit_correlations(self, commit: ContextItem) -> List[ContextRelationship]:
        """Analyze all possible correlations for a commit"""

        all_relationships = []

        # Run all correlators in parallel
        correlation_tasks = [
            correlator.find_correlations(commit)
            for correlator in self.correlators
        ]

        results = await asyncio.gather(*correlation_tasks, return_exceptions=True)

        for correlator, result in zip(self.correlators, results):
            if isinstance(result, Exception):
                logger.error(f"Correlator {correlator.__class__.__name__} failed: {result}")
                continue

            all_relationships.extend(result)

        # Store relationships
        for relationship in all_relationships:
            await self._store_relationship(relationship)

        logger.info(f"Found {len(all_relationships)} correlations for commit {commit.source_id[:8]}")
        return all_relationships

class ErrorCommitCorrelator:
    """Correlate commits with errors that might be caused by them"""

    async def find_correlations(self, commit: ContextItem) -> List[ContextRelationship]:
        """Find errors potentially caused by this commit"""

        correlations = []

        # Look for errors after this commit
        time_window_start = commit.timestamp
        time_window_end = time_window_start + timedelta(hours=24)

        # Query recent errors
        errors = await self.database.query_context_items(
            source_type="error",
            timestamp_range=(time_window_start, time_window_end),
            file_path=commit.file_path,  # Same file context
            limit=50
        )

        for error in errors:
            correlation_score = await self._calculate_error_correlation(commit, error)

            if correlation_score >= 0.4:  # Significant correlation
                correlations.append(ContextRelationship(
                    source_id=error.id,
                    target_id=commit.id,
                    relationship_type="error_potentially_caused_by_commit",
                    confidence=correlation_score,
                    metadata={
                        "time_delta_hours": (error.timestamp - commit.timestamp).total_seconds() / 3600,
                        "file_overlap": self._calculate_file_overlap(commit, error),
                        "correlation_factors": await self._get_correlation_factors(commit, error)
                    },
                    created_by="error_commit_correlator"
                ))

        return correlations

    async def _calculate_error_correlation(self, commit: ContextItem, error: ContextItem) -> float:
        """Calculate correlation score between commit and error"""

        factors = {
            'temporal': 0.0,      # How close in time
            'spatial': 0.0,       # File/location overlap
            'semantic': 0.0,      # Content similarity
            'pattern': 0.0        # Known error patterns
        }

        # Temporal factor (closer in time = higher correlation)
        time_delta_hours = (error.timestamp - commit.timestamp).total_seconds() / 3600
        if 0 <= time_delta_hours <= 2:
            factors['temporal'] = 1.0 - (time_delta_hours / 2.0)
        elif time_delta_hours <= 24:
            factors['temporal'] = 0.5 - ((time_delta_hours - 2) / 44.0)  # Decay to 0.05 at 24h

        # Spatial factor (file overlap)
        commit_files = set(commit.metrics.get('changed_files', []))
        error_file = {error.file_path} if error.file_path else set()

        if error_file & commit_files:  # Direct file match
            factors['spatial'] = 1.0
        elif error.file_path:
            # Check for related files (same directory, similar names)
            factors['spatial'] = await self._calculate_file_relatedness(commit_files, error.file_path)

        # Semantic factor (commit message vs error content similarity)
        if commit.content and error.content:
            factors['semantic'] = await self._calculate_semantic_similarity(
                commit.content, error.content[:500]
            )

        # Pattern factor (known error-causing patterns)
        factors['pattern'] = await self._detect_error_patterns(commit, error)

        # Weighted combination
        weights = {'temporal': 0.4, 'spatial': 0.3, 'semantic': 0.2, 'pattern': 0.1}
        total_score = sum(factors[f] * weights[f] for f in factors)

        return min(1.0, max(0.0, total_score))

class ChatCommitCorrelator:
    """Correlate commits with chat conversations"""

    async def find_correlations(self, commit: ContextItem) -> List[ContextRelationship]:
        """Find chat conversations related to this commit"""

        correlations = []

        # Look for conversations around commit time (wider window)
        time_window = timedelta(hours=48)  # Look 2 days before and after
        conversations = await self.database.query_context_items(
            source_type="chat",
            timestamp_range=(
                commit.timestamp - time_window,
                commit.timestamp + timedelta(hours=2)  # Shorter after window
            ),
            limit=100
        )

        for conversation in conversations:
            correlation_score = await self._calculate_chat_correlation(commit, conversation)

            if correlation_score >= 0.5:
                correlations.append(ContextRelationship(
                    source_id=commit.id,
                    target_id=conversation.id,
                    relationship_type="commit_discussed_in_chat",
                    confidence=correlation_score,
                    metadata={
                        "correlation_type": "semantic_and_temporal",
                        "time_delta_hours": abs((conversation.timestamp - commit.timestamp).total_seconds() / 3600)
                    },
                    created_by="chat_commit_correlator"
                ))

        return correlations

    async def _calculate_chat_correlation(self, commit: ContextItem, chat: ContextItem) -> float:
        """Calculate correlation between commit and chat message"""

        # File mention correlation
        file_mention_score = 0.0
        commit_files = commit.metrics.get('changed_files', [])
        chat_content = (chat.content or "").lower()

        for file_path in commit_files:
            if os.path.basename(file_path).lower() in chat_content:
                file_mention_score += 0.3  # Base score per file mention

        file_mention_score = min(1.0, file_mention_score)

        # Semantic similarity
        semantic_score = 0.0
        if commit.title and chat.content:
            commit_text = f"{commit.title} {commit.content or ''}"
            semantic_score = await self._calculate_semantic_similarity(commit_text, chat.content)

        # Issue/PR reference correlation
        reference_score = await self._detect_issue_references(commit, chat)

        # Temporal proximity
        time_delta_hours = abs((chat.timestamp - commit.timestamp).total_seconds() / 3600)
        temporal_score = max(0, 1.0 - (time_delta_hours / 48.0))  # Decay over 48 hours

        # Combined score
        total_score = (
            file_mention_score * 0.4 +
            semantic_score * 0.3 +
            reference_score * 0.2 +
            temporal_score * 0.1
        )

        return min(1.0, total_score)
```

**Day 4-5: Performance Testing and Optimization**
```python
# tests/test_correlation_performance.py
async def test_correlation_performance():
    """Test correlation engine performance"""

    correlation_engine = GitCorrelationEngine(database)

    # Create test commit
    test_commit = ContextItem(
        id=uuid4(),
        source_type="git",
        source_id="test_commit_sha",
        title="Fix authentication bug",
        content="Fixed issue with JWT token validation",
        timestamp=datetime.utcnow(),
        metrics={
            'changed_files': ['auth/jwt_validator.py', 'tests/test_auth.py'],
            'commit_type': 'bugfix'
        }
    )

    # Benchmark correlation analysis
    start_time = time.time()
    correlations = await correlation_engine.analyze_commit_correlations(test_commit)
    duration = time.time() - start_time

    # Should complete in under 5 seconds
    assert duration < 5.0
    assert isinstance(correlations, list)

    print(f"Found {len(correlations)} correlations in {duration:.2f}s")

# Performance optimization
async def optimize_correlation_queries():
    """Optimize database queries for correlation analysis"""

    # Add specialized indexes for correlation queries
    await database.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_timestamp_source
        ON context_items (timestamp DESC, source_type)
        WHERE source_type IN ('error', 'chat');

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_file_timestamp
        ON context_items (file_path, timestamp DESC)
        WHERE file_path IS NOT NULL;

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_content_trigram
        ON context_items USING GIN (content gin_trgm_ops)
        WHERE content IS NOT NULL;
    """)
```

### Phase 3: Analytics and Monitoring (Weeks 5-6)

#### Week 5: Analytics Implementation

**Day 1-2: Repository Analytics Dashboard**
```python
# src/project_context/analytics/git_analytics.py
class GitAnalyticsDashboard:
    """Comprehensive Git analytics dashboard"""

    def __init__(self, database: IngestionDatabase):
        self.database = database

    async def generate_repository_health_report(self, repo_id: UUID) -> Dict:
        """Generate comprehensive repository health report"""

        # Parallel analytics queries
        analytics_tasks = [
            self._get_commit_velocity_trends(repo_id),
            self._get_author_activity_patterns(repo_id),
            self._get_hotspot_analysis(repo_id),
            self._get_quality_metrics(repo_id),
            self._get_collaboration_metrics(repo_id)
        ]

        results = await asyncio.gather(*analytics_tasks)

        return {
            "repository_id": str(repo_id),
            "generated_at": datetime.utcnow().isoformat(),
            "commit_velocity": results[0],
            "author_activity": results[1],
            "hotspot_analysis": results[2],
            "quality_metrics": results[3],
            "collaboration_metrics": results[4],
            "overall_health_score": await self._calculate_health_score(results)
        }

    async def _get_commit_velocity_trends(self, repo_id: UUID) -> Dict:
        """Analyze commit velocity trends"""

        query = """
        WITH daily_commits AS (
            SELECT
                DATE_TRUNC('day', ci.timestamp) as date,
                COUNT(*) as commit_count,
                COUNT(DISTINCT gcd.author_id) as unique_authors,
                AVG(gcd.files_modified + gcd.files_added + gcd.files_deleted) as avg_files_per_commit
            FROM context_items ci
            JOIN git_commit_details gcd ON ci.id = gcd.context_item_id
            WHERE gcd.repository_id = $1
                AND ci.timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY DATE_TRUNC('day', ci.timestamp)
            ORDER BY date DESC
        ),
        velocity_analysis AS (
            SELECT
                *,
                AVG(commit_count) OVER (
                    ORDER BY date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as rolling_7day_avg,
                LAG(commit_count, 7) OVER (ORDER BY date) as commits_week_ago
            FROM daily_commits
        )
        SELECT
            date,
            commit_count,
            unique_authors,
            avg_files_per_commit,
            rolling_7day_avg,
            CASE
                WHEN commits_week_ago IS NOT NULL AND commits_week_ago > 0
                THEN ((commit_count - commits_week_ago)::float / commits_week_ago) * 100
                ELSE NULL
            END as week_over_week_change
        FROM velocity_analysis
        ORDER BY date DESC
        LIMIT 30
        """

        results = await self.database.fetch_all(query, repo_id)

        return {
            "daily_trends": results,
            "avg_commits_per_day": sum(r['commit_count'] for r in results) / len(results) if results else 0,
            "trend_direction": await self._calculate_trend_direction(results)
        }

    async def _get_hotspot_analysis(self, repo_id: UUID) -> Dict:
        """Analyze file hotspots and change patterns"""

        query = """
        WITH file_activity AS (
            SELECT
                gfc.file_path,
                COUNT(*) as change_frequency,
                COUNT(DISTINCT gcd.author_id) as unique_authors,
                COUNT(DISTINCT DATE_TRUNC('week', ci.timestamp)) as active_weeks,
                AVG(gfc.lines_added + gfc.lines_removed) as avg_churn_per_change,
                MAX(ci.timestamp) as last_changed,

                -- Calculate languages
                gfc.language,
                gfc.file_category,

                -- Risk indicators
                CASE WHEN COUNT(*) > 20 THEN 1 ELSE 0 END as high_frequency_risk,
                CASE WHEN COUNT(DISTINCT gcd.author_id) = 1 THEN 1 ELSE 0 END as single_author_risk,
                CASE WHEN AVG(gfc.lines_added + gfc.lines_removed) > 100 THEN 1 ELSE 0 END as high_churn_risk
            FROM git_file_changes gfc
            JOIN git_commit_details gcd ON gfc.commit_detail_id = gcd.id
            JOIN context_items ci ON gcd.context_item_id = ci.id
            WHERE gcd.repository_id = $1
                AND ci.timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY gfc.file_path, gfc.language, gfc.file_category
        ),
        hotspot_ranking AS (
            SELECT
                *,
                (change_frequency::float / 90) *
                (1 + high_frequency_risk + single_author_risk + high_churn_risk) as hotspot_score,

                ROW_NUMBER() OVER (ORDER BY change_frequency DESC, avg_churn_per_change DESC) as hotspot_rank
            FROM file_activity
        )
        SELECT * FROM hotspot_ranking
        WHERE hotspot_rank <= 20
        ORDER BY hotspot_score DESC
        """

        hotspots = await self.database.fetch_all(query, repo_id)

        return {
            "top_hotspots": hotspots,
            "hotspot_summary": {
                "total_hotspots": len([h for h in hotspots if h['hotspot_score'] > 2.0]),
                "high_risk_files": len([h for h in hotspots if h['high_frequency_risk'] or h['high_churn_risk']]),
                "single_author_files": len([h for h in hotspots if h['single_author_risk']])
            }
        }
```

**Day 3-4: Developer Productivity Analytics**
```python
# src/project_context/analytics/developer_analytics.py
class DeveloperProductivityAnalyzer:
    """Analyze developer productivity patterns"""

    async def analyze_developer_patterns(self, repo_id: UUID, days: int = 30) -> Dict:
        """Comprehensive developer productivity analysis"""

        query = """
        WITH developer_activity AS (
            SELECT
                ga.name as developer_name,
                ga.email as developer_email,
                COUNT(*) as total_commits,
                COUNT(DISTINCT DATE_TRUNC('day', ci.timestamp)) as active_days,
                AVG(gcd.files_added + gcd.files_modified + gcd.files_deleted) as avg_files_per_commit,
                SUM(gfc.lines_added) as total_lines_added,
                SUM(gfc.lines_removed) as total_lines_removed,

                -- Commit type distribution
                COUNT(*) FILTER (WHERE gcd.commit_type = 'feature') as feature_commits,
                COUNT(*) FILTER (WHERE gcd.commit_type = 'bugfix') as bugfix_commits,
                COUNT(*) FILTER (WHERE gcd.commit_type = 'refactor') as refactor_commits,
                COUNT(*) FILTER (WHERE gcd.commit_type = 'test') as test_commits,

                -- Quality indicators
                AVG(gcd.impact_score) as avg_impact_score,
                AVG(gcd.risk_score) as avg_risk_score,

                -- Collaboration indicators
                COUNT(DISTINCT gfc.file_path) as unique_files_touched,

                -- Time patterns
                MIN(ci.timestamp) as first_commit_in_period,
                MAX(ci.timestamp) as last_commit_in_period

            FROM git_authors ga
            JOIN git_commit_details gcd ON ga.id = gcd.author_id
            JOIN context_items ci ON gcd.context_item_id = ci.id
            JOIN git_file_changes gfc ON gcd.id = gfc.commit_detail_id
            WHERE gcd.repository_id = $1
                AND ci.timestamp >= NOW() - INTERVAL '1 day' * $2
            GROUP BY ga.id, ga.name, ga.email
        ),
        productivity_metrics AS (
            SELECT
                *,
                -- Productivity score calculation
                LEAST(1.0, (
                    (total_commits::float / $2) * 0.3 +  -- Commit frequency
                    (avg_impact_score * 0.25) +          -- Impact quality
                    ((1.0 - avg_risk_score) * 0.2) +     -- Code quality (inverse risk)
                    (active_days::float / $2 * 0.15) +   -- Consistency
                    ((feature_commits + bugfix_commits)::float / total_commits * 0.1) -- Value-add commits
                )) as productivity_score,

                -- Collaboration score
                LEAST(1.0, unique_files_touched::float / 50.0) as breadth_score,

                -- Velocity calculation
                CASE
                    WHEN active_days > 0
                    THEN total_commits::float / active_days
                    ELSE 0
                END as commits_per_active_day

            FROM developer_activity
        )
        SELECT * FROM productivity_metrics
        ORDER BY productivity_score DESC, total_commits DESC
        """

        developers = await self.database.fetch_all(query, repo_id, days)

        # Additional analysis
        collaboration_matrix = await self._analyze_developer_collaboration(repo_id, days)
        knowledge_distribution = await self._analyze_knowledge_distribution(repo_id, days)

        return {
            "developer_metrics": developers,
            "collaboration_matrix": collaboration_matrix,
            "knowledge_distribution": knowledge_distribution,
            "team_summary": {
                "total_developers": len(developers),
                "avg_productivity_score": sum(d['productivity_score'] for d in developers) / len(developers) if developers else 0,
                "top_performers": [d for d in developers if d['productivity_score'] > 0.7][:5]
            }
        }

    async def _analyze_developer_collaboration(self, repo_id: UUID, days: int) -> Dict:
        """Analyze how developers collaborate on files"""

        query = """
        WITH file_authors AS (
            SELECT
                gfc.file_path,
                ga.name as author_name,
                COUNT(*) as changes_by_author,
                MAX(ci.timestamp) as last_change
            FROM git_file_changes gfc
            JOIN git_commit_details gcd ON gfc.commit_detail_id = gcd.id
            JOIN git_authors ga ON gcd.author_id = ga.id
            JOIN context_items ci ON gcd.context_item_id = ci.id
            WHERE gcd.repository_id = $1
                AND ci.timestamp >= NOW() - INTERVAL '1 day' * $2
            GROUP BY gfc.file_path, ga.name
        ),
        collaboration_pairs AS (
            SELECT
                fa1.author_name as author1,
                fa2.author_name as author2,
                COUNT(DISTINCT fa1.file_path) as shared_files,
                AVG(GREATEST(fa1.changes_by_author, fa2.changes_by_author)) as avg_changes_per_shared_file
            FROM file_authors fa1
            JOIN file_authors fa2 ON fa1.file_path = fa2.file_path
                AND fa1.author_name < fa2.author_name  -- Avoid duplicates
            GROUP BY fa1.author_name, fa2.author_name
            HAVING COUNT(DISTINCT fa1.file_path) >= 2  -- At least 2 shared files
        )
        SELECT * FROM collaboration_pairs
        ORDER BY shared_files DESC, avg_changes_per_shared_file DESC
        LIMIT 50
        """

        pairs = await self.database.fetch_all(query, repo_id, days)

        return {
            "collaboration_pairs": pairs,
            "collaboration_strength": sum(p['shared_files'] for p in pairs) / len(pairs) if pairs else 0
        }
```

**Day 5: Real-time Monitoring**
```python
# src/project_context/monitoring/git_monitoring.py
class GitIntegrationMonitor:
    """Real-time monitoring for Git integration health"""

    def __init__(self, database: IngestionDatabase, metrics_collector: MetricsCollector):
        self.database = database
        self.metrics = metrics_collector

    async def collect_realtime_metrics(self):
        """Collect real-time metrics for monitoring"""

        # Processing performance metrics
        processing_metrics = await self._collect_processing_metrics()
        for metric_name, value in processing_metrics.items():
            await self.metrics.gauge(f"git.{metric_name}", value)

        # Correlation effectiveness metrics
        correlation_metrics = await self._collect_correlation_metrics()
        for metric_name, value in correlation_metrics.items():
            await self.metrics.gauge(f"git.correlation.{metric_name}", value)

        # Repository health metrics
        repo_metrics = await self._collect_repository_health_metrics()
        for metric_name, value in repo_metrics.items():
            await self.metrics.gauge(f"git.repository.{metric_name}", value)

    async def _collect_processing_metrics(self) -> Dict[str, float]:
        """Collect Git processing performance metrics"""

        # Commits processed in last hour
        commits_last_hour = await self.database.fetch_one("""
            SELECT COUNT(*) as count
            FROM context_items ci
            JOIN git_commit_details gcd ON ci.id = gcd.context_item_id
            WHERE ci.ingested_at >= NOW() - INTERVAL '1 hour'
        """)

        # Processing lag (difference between commit time and ingestion time)
        avg_processing_lag = await self.database.fetch_one("""
            SELECT AVG(EXTRACT(EPOCH FROM (ci.ingested_at - ci.timestamp))) as avg_lag_seconds
            FROM context_items ci
            JOIN git_commit_details gcd ON ci.id = gcd.context_item_id
            WHERE ci.ingested_at >= NOW() - INTERVAL '1 hour'
        """)

        # Error rate
        processing_errors = await self.database.fetch_one("""
            SELECT COUNT(*) as error_count
            FROM context_items
            WHERE source_type = 'error'
                AND content ILIKE '%git%'
                AND timestamp >= NOW() - INTERVAL '1 hour'
        """)

        return {
            "commits_per_hour": commits_last_hour["count"] if commits_last_hour else 0,
            "avg_processing_lag_seconds": avg_processing_lag["avg_lag_seconds"] if avg_processing_lag else 0,
            "processing_error_rate": processing_errors["error_count"] if processing_errors else 0
        }

    async def generate_health_alert(self, threshold_breaches: Dict) -> Optional[str]:
        """Generate health alert if thresholds are breached"""

        alerts = []

        if threshold_breaches.get("processing_lag_seconds", 0) > 3600:  # 1 hour lag
            alerts.append("HIGH PROCESSING LAG: Git commits are being processed with >1 hour delay")

        if threshold_breaches.get("correlation_accuracy", 1.0) < 0.5:  # <50% accuracy
            alerts.append("LOW CORRELATION ACCURACY: Git correlation engine accuracy below 50%")

        if threshold_breaches.get("commits_per_hour", 0) == 0:  # No processing
            alerts.append("NO GIT PROCESSING: No Git commits processed in the last hour")

        if alerts:
            return "GIT INTEGRATION HEALTH ALERT:\n" + "\n".join(f"- {alert}" for alert in alerts)

        return None
```

#### Week 6: Testing and Optimization

**Day 1-2: Comprehensive Testing Suite**
```python
# tests/test_git_integration_comprehensive.py
import pytest
import asyncio
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path

class TestGitIntegrationComprehensive:
    """Comprehensive test suite for Git integration"""

    @pytest.fixture
    async def test_repository(self):
        """Create temporary test repository"""

        temp_dir = Path(tempfile.mkdtemp())
        repo_path = temp_dir / "test_repo"

        # Initialize test repo with pygit2
        repo = pygit2.init_repository(str(repo_path))

        # Create initial commit
        signature = pygit2.Signature("Test Author", "test@example.com")
        tree = repo.TreeBuilder().write()

        # Add test file
        test_file = repo_path / "test_file.py"
        test_file.write_text("print('hello world')")

        repo.index.add("test_file.py")
        repo.index.write()
        tree = repo.index.write_tree()

        initial_commit = repo.create_commit(
            "HEAD", signature, signature, "Initial commit", tree, []
        )

        yield repo_path

        # Cleanup
        shutil.rmtree(temp_dir)

    async def test_end_to_end_processing(self, test_repository):
        """Test complete end-to-end Git processing"""

        # Initialize components
        config = AdapterConfig(
            adapter_id="git_test",
            source_type="git",
            batch_size=10
        )

        adapter = EnhancedGitAdapter(config)
        adapter._repo_path = str(test_repository)
        await adapter.initialize()

        # Process commits
        commits = []
        async for commit in adapter.fetch_items(limit=10):
            commits.append(commit)

        # Verify results
        assert len(commits) >= 1  # At least initial commit

        for commit in commits:
            # Verify data quality
            assert 'hash' in commit
            assert 'author' in commit
            assert 'commit_date' in commit
            assert 'changed_files' in commit
            assert isinstance(commit['changed_files'], list)

            # Transform to context item
            context_item = await adapter.transform_item(commit)

            # Verify transformation
            assert context_item.source_type == "git"
            assert context_item.entity_type == "commit"
            assert context_item.metrics is not None
            assert 'commit_sha' in context_item.metrics

    async def test_incremental_processing(self, test_repository):
        """Test incremental commit processing"""

        # Add more commits to repository
        repo = pygit2.Repository(str(test_repository))
        signature = pygit2.Signature("Test Author 2", "test2@example.com")

        # Add second commit
        test_file2 = test_repository / "test_file2.py"
        test_file2.write_text("print('second file')")

        repo.index.add("test_file2.py")
        repo.index.write()
        tree = repo.index.write_tree()

        parent_commit = repo.head.target
        second_commit = repo.create_commit(
            "HEAD", signature, signature, "Add second file", tree, [parent_commit]
        )

        # Test incremental processor
        processor = IncrementalGitProcessor(database, enhanced_git_adapter)
        await processor.process_incremental_commit(str(test_repository), str(second_commit))

        # Verify commit was processed
        processed_commit = await database.fetch_one("""
            SELECT * FROM git_commit_details WHERE commit_sha = $1
        """, str(second_commit))

        assert processed_commit is not None
        assert processed_commit['commit_sha'] == str(second_commit)

    async def test_correlation_accuracy(self):
        """Test correlation engine accuracy"""

        # Create test data
        test_commit = ContextItem(
            id=uuid4(),
            source_type="git",
            source_id="test_sha_123",
            title="Fix authentication bug in login.py",
            content="Fixed JWT token validation issue",
            timestamp=datetime.utcnow(),
            file_path="auth/login.py",
            metrics={
                'changed_files': ['auth/login.py', 'tests/test_auth.py'],
                'commit_type': 'bugfix',
                'impact_score': 0.8
            }
        )

        # Create related error
        test_error = ContextItem(
            id=uuid4(),
            source_type="error",
            source_id="error_123",
            title="Authentication Error",
            content="JWT token validation failed at line 45",
            timestamp=test_commit.timestamp + timedelta(minutes=30),
            file_path="auth/login.py",
            line_start=45
        )

        # Store test data
        await self._store_test_items([test_commit, test_error])

        # Run correlation
        correlator = ErrorCommitCorrelator()
        correlations = await correlator.find_correlations(test_commit)

        # Verify correlation found
        assert len(correlations) > 0

        error_correlations = [c for c in correlations if c.source_id == test_error.id]
        assert len(error_correlations) > 0

        # Verify correlation quality
        correlation = error_correlations[0]
        assert correlation.confidence >= 0.7  # Should be high confidence
        assert correlation.relationship_type == "error_potentially_caused_by_commit"

    async def test_performance_benchmarks(self, test_repository):
        """Test performance meets benchmarks"""

        # Create larger test repository
        await self._create_large_test_repo(test_repository, commits=1000)

        # Benchmark commit processing
        start_time = time.time()

        config = AdapterConfig(adapter_id="perf_test", source_type="git", batch_size=100)
        adapter = EnhancedGitAdapter(config)
        adapter._repo_path = str(test_repository)
        await adapter.initialize()

        commit_count = 0
        async for commit in adapter.fetch_items(limit=1000):
            commit_count += 1

        duration = time.time() - start_time

        # Performance assertions
        assert duration < 30.0  # Should process 1000 commits in under 30 seconds
        assert commit_count == 1000

        commits_per_second = commit_count / duration
        assert commits_per_second > 30  # At least 30 commits per second

        print(f"Performance: {commits_per_second:.2f} commits/second")

    async def _create_large_test_repo(self, repo_path: Path, commits: int):
        """Create test repository with many commits"""

        repo = pygit2.Repository(str(repo_path))
        signature = pygit2.Signature("Test Author", "test@example.com")

        for i in range(commits - 1):  # -1 because we already have initial commit
            # Create or modify a file
            test_file = repo_path / f"file_{i % 10}.py"
            test_file.write_text(f"# File content for commit {i}\nprint('commit {i}')")

            repo.index.add(f"file_{i % 10}.py")
            repo.index.write()
            tree = repo.index.write_tree()

            parent_commit = repo.head.target
            repo.create_commit(
                "HEAD", signature, signature, f"Commit {i}", tree, [parent_commit]
            )
```

**Day 3-4: Performance Optimization**
```python
# src/project_context/optimization/git_optimization.py
class GitPerformanceOptimizer:
    """Optimize Git integration performance"""

    def __init__(self, database: IngestionDatabase):
        self.database = database

    async def optimize_database_performance(self):
        """Apply database optimizations for Git data"""

        optimizations = [
            # Partition large tables by time
            """
            ALTER TABLE git_commit_details
            SET (timescaledb.compress, timescaledb.compress_segmentby = 'repository_id');
            """,

            # Update table statistics
            """
            ANALYZE git_commit_details;
            ANALYZE git_file_changes;
            ANALYZE git_authors;
            ANALYZE context_relationships;
            """,

            # Create covering indexes for common queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_git_commit_details_covering
            ON git_commit_details (repository_id, created_at DESC)
            INCLUDE (author_id, commit_sha, commit_type, impact_score);
            """,

            # Optimize relationship queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_rel_git_optimized
            ON context_relationships (target_id, relationship_type, confidence DESC)
            WHERE created_by LIKE '%git%';
            """
        ]

        for optimization in optimizations:
            try:
                await self.database.execute(optimization)
                logger.info(f"Applied optimization: {optimization[:50]}...")
            except Exception as e:
                logger.error(f"Failed to apply optimization: {e}")

    async def setup_connection_pooling(self):
        """Optimize database connection pooling for Git operations"""

        # Configure connection pool for heavy Git operations
        pool_config = {
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300.0,
            'command_timeout': 60.0
        }

        return await asyncpg.create_pool(
            database_url,
            **pool_config
        )

    async def implement_caching_strategy(self):
        """Implement multi-level caching for Git data"""

        # Redis configuration for Git data caching
        redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 1,  # Dedicated database for Git cache
            'decode_responses': True,
            'max_connections': 100
        }

        redis_client = redis.Redis(**redis_config)

        # Cache commonly accessed data
        cache_strategies = {
            'repository_metadata': {'ttl': 3600, 'namespace': 'git:repo:meta'},
            'commit_details': {'ttl': 86400, 'namespace': 'git:commit:detail'},
            'file_history': {'ttl': 1800, 'namespace': 'git:file:history'},
            'correlation_results': {'ttl': 7200, 'namespace': 'git:correlations'}
        }

        return GitDataCache(redis_client, cache_strategies)

class GitDataCache:
    """Intelligent caching for Git data"""

    def __init__(self, redis_client, cache_strategies):
        self.redis = redis_client
        self.strategies = cache_strategies

    async def get_or_compute(self, cache_type: str, key: str, compute_func: callable):
        """Get from cache or compute and cache result"""

        strategy = self.strategies.get(cache_type)
        if not strategy:
            return await compute_func()

        cache_key = f"{strategy['namespace']}:{key}"

        # Try cache first
        cached_result = await self.redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        # Compute and cache
        result = await compute_func()
        await self.redis.setex(
            cache_key,
            strategy['ttl'],
            json.dumps(result, default=str)
        )

        return result

    async def invalidate_cache(self, cache_type: str, pattern: str = "*"):
        """Invalidate cached data"""

        strategy = self.strategies.get(cache_type)
        if not strategy:
            return

        search_pattern = f"{strategy['namespace']}:{pattern}"
        keys = await self.redis.keys(search_pattern)

        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries for {cache_type}")
```

**Day 5: Deployment Preparation**
```bash
#!/bin/bash
# deploy_git_integration.sh - Complete deployment script

set -e

echo "🚀 Deploying Git History Integration System"

# Check prerequisites
echo "📋 Checking prerequisites..."
python3 -c "import pygit2; print('✅ pygit2 available')" || {
    echo "❌ pygit2 not available. Installing..."
    apt-get update
    apt-get install -y libgit2-dev python3-dev
    pip install pygit2==1.13.3
}

# Database setup
echo "🗄️  Setting up database schema..."
psql $DATABASE_URL -f migrations/001_git_enhanced_schema.sql
psql $DATABASE_URL -f migrations/002_git_indexes.sql
psql $DATABASE_URL -f migrations/003_git_functions.sql

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements_git.txt

# Configure Redis for caching
echo "💾 Configuring Redis caching..."
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Run migration for existing data
echo "🔄 Migrating existing Git data..."
python scripts/migrate_existing_git_data.py

# Setup Git hooks for active repositories
echo "🪝 Setting up Git hooks..."
python scripts/setup_git_hooks.py

# Run comprehensive tests
echo "🧪 Running integration tests..."
python -m pytest tests/test_git_integration_comprehensive.py -v

# Start monitoring
echo "📊 Starting monitoring services..."
systemctl restart unified-context-git-monitor

# Verify deployment
echo "✅ Verifying deployment..."
python scripts/verify_git_integration.py

echo "🎉 Git History Integration deployed successfully!"
echo "📈 Dashboard available at: http://localhost:8000/git-analytics"
echo "📋 Monitor health at: http://localhost:8000/health/git"
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Execute mandatory startup sequence", "status": "completed", "activeForm": "Executing mandatory startup sequence"}, {"content": "Research Git analysis libraries comparison", "status": "completed", "activeForm": "Researching Git analysis libraries comparison"}, {"content": "Analyze commit parsing strategies", "status": "completed", "activeForm": "Analyzing commit parsing strategies"}, {"content": "Study integration architecture patterns", "status": "completed", "activeForm": "Studying integration architecture patterns"}, {"content": "Design optimal data structures", "status": "completed", "activeForm": "Designing optimal data structures"}, {"content": "Create implementation recommendations", "status": "completed", "activeForm": "Creating implementation recommendations"}]
