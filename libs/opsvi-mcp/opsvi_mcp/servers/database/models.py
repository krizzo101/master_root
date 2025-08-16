"""
Data models for Database Integration MCP Server
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum


class QueryType(str, Enum):
    """Types of database queries"""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    EXECUTE = "EXECUTE"
    TRANSACTION = "TRANSACTION"


class TransactionState(str, Enum):
    """Transaction states"""

    IDLE = "idle"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class MigrationStatus(str, Enum):
    """Migration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class QueryParameter:
    """Query parameter definition"""

    name: str
    value: Any
    type: Optional[str] = None
    index: Optional[int] = None


@dataclass
class QueryResult:
    """Database query result"""

    query_id: str
    query: str
    query_type: QueryType
    connection_name: str
    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    rows_affected: int = 0
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PreparedStatement:
    """Prepared statement definition"""

    statement_id: str
    name: str
    query: str
    parameters: List[QueryParameter] = field(default_factory=list)
    connection_name: str
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    execution_count: int = 0


@dataclass
class Transaction:
    """Database transaction"""

    transaction_id: str
    connection_name: str
    state: TransactionState = TransactionState.IDLE
    isolation_level: str = "READ_COMMITTED"
    read_only: bool = False
    deferrable: bool = False
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    queries: List[str] = field(default_factory=list)
    savepoints: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ConnectionPool:
    """Connection pool state"""

    pool_id: str
    connection_name: str
    min_size: int
    max_size: int
    current_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_connections_created: int = 0
    total_connections_closed: int = 0
    wait_queue_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None


@dataclass
class Migration:
    """Database migration"""

    migration_id: str
    version: str
    name: str
    description: Optional[str] = None
    up_script: str = ""
    down_script: str = ""
    checksum: Optional[str] = None
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class TableSchema:
    """Table schema information"""

    table_name: str
    schema_name: Optional[str] = None
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_key: Optional[List[str]] = None
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class QueryBuilder:
    """SQL query builder state"""

    builder_id: str
    query_type: QueryType
    table: Optional[str] = None
    schema: Optional[str] = None
    select_columns: List[str] = field(default_factory=list)
    where_conditions: List[str] = field(default_factory=list)
    join_clauses: List[str] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having_conditions: List[str] = field(default_factory=list)
    order_by: List[Dict[str, str]] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    values: Dict[str, Any] = field(default_factory=dict)
    returning: List[str] = field(default_factory=list)
    cte_expressions: List[str] = field(default_factory=list)

    def to_sql(self) -> str:
        """Convert builder state to SQL query"""
        parts = []

        # Handle CTEs
        if self.cte_expressions:
            parts.append(f"WITH {', '.join(self.cte_expressions)}")

        # Handle different query types
        if self.query_type == QueryType.SELECT:
            columns = ", ".join(self.select_columns) if self.select_columns else "*"
            parts.append(f"SELECT {columns}")
            if self.table:
                table_ref = f"{self.schema}.{self.table}" if self.schema else self.table
                parts.append(f"FROM {table_ref}")

        elif self.query_type == QueryType.INSERT:
            if self.table:
                table_ref = f"{self.schema}.{self.table}" if self.schema else self.table
                parts.append(f"INSERT INTO {table_ref}")
                if self.values:
                    columns = ", ".join(self.values.keys())
                    placeholders = ", ".join([f":{k}" for k in self.values.keys()])
                    parts.append(f"({columns}) VALUES ({placeholders})")

        elif self.query_type == QueryType.UPDATE:
            if self.table:
                table_ref = f"{self.schema}.{self.table}" if self.schema else self.table
                parts.append(f"UPDATE {table_ref}")
                if self.values:
                    set_clauses = [f"{k} = :{k}" for k in self.values.keys()]
                    parts.append(f"SET {', '.join(set_clauses)}")

        elif self.query_type == QueryType.DELETE:
            if self.table:
                table_ref = f"{self.schema}.{self.table}" if self.schema else self.table
                parts.append(f"DELETE FROM {table_ref}")

        # Add JOIN clauses
        if self.join_clauses:
            parts.extend(self.join_clauses)

        # Add WHERE conditions
        if self.where_conditions:
            parts.append(f"WHERE {' AND '.join(self.where_conditions)}")

        # Add GROUP BY
        if self.group_by:
            parts.append(f"GROUP BY {', '.join(self.group_by)}")

        # Add HAVING
        if self.having_conditions:
            parts.append(f"HAVING {' AND '.join(self.having_conditions)}")

        # Add ORDER BY
        if self.order_by:
            order_clauses = [
                f"{col['column']} {col.get('direction', 'ASC')}"
                for col in self.order_by
            ]
            parts.append(f"ORDER BY {', '.join(order_clauses)}")

        # Add LIMIT/OFFSET
        if self.limit is not None:
            parts.append(f"LIMIT {self.limit}")
        if self.offset is not None:
            parts.append(f"OFFSET {self.offset}")

        # Add RETURNING clause
        if self.returning:
            parts.append(f"RETURNING {', '.join(self.returning)}")

        return " ".join(parts)


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""

    connection_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    slow_queries: int = 0
    average_query_time: float = 0.0
    cache_hit_ratio: float = 0.0
    transaction_count: int = 0
    rollback_count: int = 0
    deadlock_count: int = 0
    disk_usage_bytes: Optional[int] = None
    memory_usage_bytes: Optional[int] = None
    cpu_usage_percent: Optional[float] = None


@dataclass
class BackupMetadata:
    """Database backup metadata"""

    backup_id: str
    connection_name: str
    backup_type: Literal["full", "incremental", "differential"] = "full"
    format: Literal["sql", "binary", "tar", "custom"] = "sql"
    compression: Optional[str] = None
    file_path: str = ""
    file_size_bytes: Optional[int] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    tables_included: List[str] = field(default_factory=list)
    tables_excluded: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
