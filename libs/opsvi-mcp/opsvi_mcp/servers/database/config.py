"""
Configuration for Database Integration MCP Server
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""

    min_size: int = 1
    max_size: int = 10
    max_idle_time: int = 300  # seconds
    max_lifetime: int = 3600  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    command_timeout: int = 30  # seconds
    connection_timeout: int = 10  # seconds


@dataclass
class DatabaseConnection:
    """Database connection configuration"""

    name: str
    type: DatabaseType
    host: str = "localhost"
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: str = "prefer"
    connection_string: Optional[str] = None
    pool_config: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Set default ports if not specified
        if self.port is None:
            if self.type == DatabaseType.POSTGRESQL:
                self.port = 5432
            elif self.type == DatabaseType.MYSQL:
                self.port = 3306

        # Build connection string if not provided
        if not self.connection_string:
            self._build_connection_string()

    def _build_connection_string(self):
        """Build connection string from components"""
        if self.type == DatabaseType.POSTGRESQL:
            params = []
            if self.host:
                params.append(f"host={self.host}")
            if self.port:
                params.append(f"port={self.port}")
            if self.database:
                params.append(f"dbname={self.database}")
            if self.username:
                params.append(f"user={self.username}")
            if self.password:
                params.append(f"password={self.password}")
            if self.ssl_mode:
                params.append(f"sslmode={self.ssl_mode}")

            # Add extra params
            for key, value in self.extra_params.items():
                params.append(f"{key}={value}")

            self.connection_string = " ".join(params)

        elif self.type == DatabaseType.MYSQL:
            auth = ""
            if self.username:
                auth = self.username
                if self.password:
                    auth += f":{self.password}"
                auth += "@"

            self.connection_string = (
                f"mysql://{auth}{self.host}:{self.port}/{self.database}"
            )

            # Add extra params
            if self.extra_params:
                params = "&".join([f"{k}={v}" for k, v in self.extra_params.items()])
                self.connection_string += f"?{params}"

        elif self.type == DatabaseType.SQLITE:
            self.connection_string = f"sqlite:///{self.database}"


@dataclass
class MigrationConfig:
    """Migration management configuration"""

    enabled: bool = True
    migrations_path: str = "migrations"
    auto_migrate: bool = False
    version_table: str = "schema_migrations"
    lock_timeout: int = 60  # seconds
    transaction_mode: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""

    log_level: str = "INFO"
    log_queries: bool = False
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0  # seconds
    log_connections: bool = True
    log_transactions: bool = False
    logs_dir: str = "/home/opsvi/master_root/logs/database"


@dataclass
class SecurityConfig:
    """Security configuration"""

    encrypt_passwords: bool = True
    require_ssl: bool = False
    allowed_statements: List[str] = field(
        default_factory=lambda: [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
        ]
    )
    max_query_length: int = 100000
    prevent_sql_injection: bool = True
    sanitize_inputs: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration"""

    query_cache_enabled: bool = True
    query_cache_size: int = 100
    query_cache_ttl: int = 300  # seconds
    prepared_statements: bool = True
    batch_size: int = 1000
    fetch_size: int = 100


@dataclass
class DatabaseServerConfig:
    """Main database server configuration"""

    default_connection: Optional[str] = None
    connections: Dict[str, DatabaseConnection] = field(default_factory=dict)
    migration: MigrationConfig = field(default_factory=MigrationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    def __post_init__(self):
        # Load connections from environment
        self._load_env_connections()

        # Set default connection if not specified
        if not self.default_connection and self.connections:
            self.default_connection = next(iter(self.connections.keys()))

    def _load_env_connections(self):
        """Load database connections from environment variables"""
        # PostgreSQL connection
        pg_host = os.getenv("DB_PG_HOST")
        if pg_host:
            self.connections["postgres"] = DatabaseConnection(
                name="postgres",
                type=DatabaseType.POSTGRESQL,
                host=pg_host,
                port=int(os.getenv("DB_PG_PORT", 5432)),
                database=os.getenv("DB_PG_DATABASE", "postgres"),
                username=os.getenv("DB_PG_USERNAME"),
                password=os.getenv("DB_PG_PASSWORD"),
                ssl_mode=os.getenv("DB_PG_SSL_MODE", "prefer"),
            )

        # MySQL connection
        mysql_host = os.getenv("DB_MYSQL_HOST")
        if mysql_host:
            self.connections["mysql"] = DatabaseConnection(
                name="mysql",
                type=DatabaseType.MYSQL,
                host=mysql_host,
                port=int(os.getenv("DB_MYSQL_PORT", 3306)),
                database=os.getenv("DB_MYSQL_DATABASE", "mysql"),
                username=os.getenv("DB_MYSQL_USERNAME"),
                password=os.getenv("DB_MYSQL_PASSWORD"),
            )

        # SQLite connection
        sqlite_path = os.getenv("DB_SQLITE_PATH")
        if sqlite_path:
            self.connections["sqlite"] = DatabaseConnection(
                name="sqlite", type=DatabaseType.SQLITE, database=sqlite_path
            )

    def get_connection(
        self, name: Optional[str] = None
    ) -> Optional[DatabaseConnection]:
        """Get a database connection by name"""
        if name:
            return self.connections.get(name)
        elif self.default_connection:
            return self.connections.get(self.default_connection)
        return None


# Create global configuration instance
config = DatabaseServerConfig()
