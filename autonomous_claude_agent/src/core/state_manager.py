"""
State Manager for persistent state and checkpointing
"""

import json
import sqlite3
import pickle
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import aiofiles
import gzip

from src.utils.logger import get_logger

logger = get_logger(__name__)

class StateManager:
    """Manages agent state persistence and recovery"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.db_path = Path(f"data/state_{agent_id}.db")
        self.checkpoint_dir = Path(f"data/checkpoints/{agent_id}")
        
        # Create directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_db()
        
        # State cache
        self.state_cache = {}
        self.last_checkpoint = None
        
    def _initialize_db(self):
        """Initialize SQLite database for state persistence"""
        
        with sqlite3.connect(self.db_path) as conn:
            # State table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    state_data TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    compressed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Events table for audit trail
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    iteration INTEGER,
                    success BOOLEAN
                )
            ''')
            
            # Metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL
                )
            ''')
            
            # Create indices
            conn.execute('CREATE INDEX IF NOT EXISTS idx_checkpoint_id ON state(checkpoint_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_iteration ON state(iteration)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)')
            
            conn.commit()
    
    async def save_checkpoint(self, state: Dict[str, Any]) -> str:
        """Create checkpoint with verification"""
        
        try:
            # Generate checkpoint ID
            timestamp = datetime.now().isoformat()
            iteration = state.get('iteration', 0)
            checkpoint_id = f"{timestamp}_{iteration}_{self.agent_id[:8]}"
            
            # Prepare state data
            state_data = {
                'checkpoint_id': checkpoint_id,
                'timestamp': timestamp,
                'agent_id': self.agent_id,
                'state': state
            }
            
            # Calculate checksum
            state_bytes = pickle.dumps(state_data)
            checksum = hashlib.sha256(state_bytes).hexdigest()
            
            # Compress if large
            compressed = False
            if len(state_bytes) > 1024 * 1024:  # 1MB
                state_bytes = gzip.compress(state_bytes)
                compressed = True
            
            # Save to file
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl{'z' if compressed else ''}"
            async with aiofiles.open(checkpoint_path, 'wb') as f:
                await f.write(state_bytes)
            
            # Save metadata to database
            async with self._get_db_connection() as conn:
                await conn.execute(
                    '''INSERT INTO state 
                       (checkpoint_id, timestamp, iteration, state_data, checksum, compressed) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (checkpoint_id, timestamp, iteration, 
                     json.dumps({'file': str(checkpoint_path), 'size': len(state_bytes)}),
                     checksum, compressed)
                )
                await conn.commit()
            
            # Log event
            await self.log_event('checkpoint_saved', {
                'checkpoint_id': checkpoint_id,
                'size_bytes': len(state_bytes),
                'compressed': compressed
            }, iteration, True)
            
            self.last_checkpoint = checkpoint_id
            logger.info(f"Checkpoint saved: {checkpoint_id} (size: {len(state_bytes)} bytes)")
            
            # Clean old checkpoints
            await self._cleanup_old_checkpoints()
            
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            await self.log_event('checkpoint_failed', {'error': str(e)}, 
                               state.get('iteration', 0), False)
            raise
    
    async def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Load checkpoint with validation"""
        
        try:
            # Get checkpoint metadata from database
            async with self._get_db_connection() as conn:
                cursor = await conn.execute(
                    'SELECT * FROM state WHERE checkpoint_id = ?',
                    (checkpoint_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    raise ValueError(f"Checkpoint not found: {checkpoint_id}")
                
                metadata = dict(row)
            
            # Load checkpoint file
            file_info = json.loads(metadata['state_data'])
            checkpoint_path = Path(file_info['file'])
            
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
            
            # Read and decompress if needed
            async with aiofiles.open(checkpoint_path, 'rb') as f:
                state_bytes = await f.read()
            
            if metadata['compressed']:
                state_bytes = gzip.decompress(state_bytes)
            
            # Verify checksum
            checksum = hashlib.sha256(state_bytes).hexdigest()
            if checksum != metadata['checksum']:
                raise ValueError(f"Checkpoint corrupted: checksum mismatch")
            
            # Unpickle state
            state_data = pickle.loads(state_bytes)
            
            logger.info(f"Checkpoint loaded: {checkpoint_id}")
            await self.log_event('checkpoint_loaded', {'checkpoint_id': checkpoint_id},
                               state_data['state'].get('iteration', 0), True)
            
            return state_data['state']
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            await self.log_event('checkpoint_load_failed', 
                               {'checkpoint_id': checkpoint_id, 'error': str(e)},
                               0, False)
            raise
    
    async def list_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List available checkpoints"""
        
        async with self._get_db_connection() as conn:
            cursor = await conn.execute(
                '''SELECT checkpoint_id, timestamp, iteration 
                   FROM state 
                   ORDER BY iteration DESC 
                   LIMIT ?''',
                (limit,)
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    'checkpoint_id': row[0],
                    'timestamp': row[1],
                    'iteration': row[2]
                }
                for row in rows
            ]
    
    async def log_event(self, event_type: str, event_data: Dict[str, Any],
                        iteration: Optional[int] = None, success: bool = True):
        """Log an event to the audit trail"""
        
        try:
            async with self._get_db_connection() as conn:
                await conn.execute(
                    '''INSERT INTO events 
                       (timestamp, event_type, event_data, iteration, success) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (datetime.now().isoformat(), event_type, 
                     json.dumps(event_data), iteration, success)
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    async def log_metric(self, metric_name: str, metric_value: float, iteration: int):
        """Log a metric value"""
        
        try:
            async with self._get_db_connection() as conn:
                await conn.execute(
                    '''INSERT INTO metrics 
                       (timestamp, iteration, metric_name, metric_value) 
                       VALUES (?, ?, ?, ?)''',
                    (datetime.now().isoformat(), iteration, metric_name, metric_value)
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Failed to log metric: {e}")
    
    async def get_metrics(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical metrics"""
        
        async with self._get_db_connection() as conn:
            cursor = await conn.execute(
                '''SELECT timestamp, iteration, metric_value 
                   FROM metrics 
                   WHERE metric_name = ? 
                   ORDER BY iteration DESC 
                   LIMIT ?''',
                (metric_name, limit)
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    'timestamp': row[0],
                    'iteration': row[1],
                    'value': row[2]
                }
                for row in rows
            ]
    
    async def get_events(self, event_type: Optional[str] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical events"""
        
        async with self._get_db_connection() as conn:
            if event_type:
                cursor = await conn.execute(
                    '''SELECT timestamp, event_type, event_data, iteration, success 
                       FROM events 
                       WHERE event_type = ? 
                       ORDER BY id DESC 
                       LIMIT ?''',
                    (event_type, limit)
                )
            else:
                cursor = await conn.execute(
                    '''SELECT timestamp, event_type, event_data, iteration, success 
                       FROM events 
                       ORDER BY id DESC 
                       LIMIT ?''',
                    (limit,)
                )
            
            rows = await cursor.fetchall()
            
            return [
                {
                    'timestamp': row[0],
                    'event_type': row[1],
                    'event_data': json.loads(row[2]),
                    'iteration': row[3],
                    'success': row[4]
                }
                for row in rows
            ]
    
    async def _cleanup_old_checkpoints(self, keep_count: int = 10):
        """Clean up old checkpoints, keeping the most recent ones"""
        
        try:
            # Get all checkpoints
            async with self._get_db_connection() as conn:
                cursor = await conn.execute(
                    'SELECT checkpoint_id, state_data FROM state ORDER BY iteration DESC'
                )
                rows = await cursor.fetchall()
            
            # Keep the most recent ones
            if len(rows) > keep_count:
                to_delete = rows[keep_count:]
                
                for checkpoint_id, state_data in to_delete:
                    # Delete file
                    file_info = json.loads(state_data)
                    checkpoint_path = Path(file_info['file'])
                    if checkpoint_path.exists():
                        checkpoint_path.unlink()
                    
                    # Delete from database
                    async with self._get_db_connection() as conn:
                        await conn.execute(
                            'DELETE FROM state WHERE checkpoint_id = ?',
                            (checkpoint_id,)
                        )
                        await conn.commit()
                    
                logger.info(f"Cleaned up {len(to_delete)} old checkpoints")
                
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
    
    async def _get_db_connection(self):
        """Get async database connection"""
        # In production, would use aiosqlite
        # For now, using synchronous sqlite3 in executor
        return sqlite3.connect(self.db_path, isolation_level=None)
    
    async def export_state(self) -> Dict[str, Any]:
        """Export complete state for backup"""
        
        state = {
            'agent_id': self.agent_id,
            'checkpoints': await self.list_checkpoints(limit=100),
            'events': await self.get_events(limit=1000),
            'metrics': {}
        }
        
        # Export all metrics
        async with self._get_db_connection() as conn:
            cursor = await conn.execute(
                'SELECT DISTINCT metric_name FROM metrics'
            )
            metric_names = await cursor.fetchall()
            
            for (metric_name,) in metric_names:
                state['metrics'][metric_name] = await self.get_metrics(metric_name)
        
        return state
    
    async def import_state(self, state: Dict[str, Any]):
        """Import state from backup"""
        
        # Import events
        for event in state.get('events', []):
            await self.log_event(
                event['event_type'],
                event['event_data'],
                event.get('iteration'),
                event.get('success', True)
            )
        
        # Import metrics
        for metric_name, values in state.get('metrics', {}).items():
            for value in values:
                await self.log_metric(
                    metric_name,
                    value['value'],
                    value['iteration']
                )
        
        logger.info("State imported successfully")