"""Database models and connection management for URL shortener."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""

    pass


class URLDatabase:
    """Database manager for URL storage and retrieval."""

    def __init__(self, db_path: str = "url_shortener.db"):
        """
        Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_url TEXT NOT NULL,
                        short_code TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        click_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        expires_at TIMESTAMP
                    )
                """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_short_code
                    ON urls(short_code)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_created_at
                    ON urls(created_at)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_is_active
                    ON urls(is_active)
                """
                )

                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection context manager."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
        finally:
            if conn:
                conn.close()

    def insert_url(
        self, original_url: str, short_code: str, expires_at: Optional[datetime] = None
    ) -> int:
        """
        Insert a new URL into the database.

        Args:
            original_url: The original long URL.
            short_code: The generated short code.
            expires_at: Optional expiration timestamp.

        Returns:
            The ID of the inserted URL.

        Raises:
            DatabaseError: If insertion fails.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO urls (original_url, short_code, expires_at)
                    VALUES (?, ?, ?)
                """,
                    (original_url, short_code, expires_at),
                )
                conn.commit()

                url_id = cursor.lastrowid
                logger.info(f"Inserted URL with ID {url_id}")
                return url_id
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise DatabaseError(f"Short code already exists: {short_code}")
            raise DatabaseError(f"Failed to insert URL: {e}")
        except sqlite3.Error as e:
            logger.error(f"Database insert error: {e}")
            raise DatabaseError(f"Failed to insert URL: {e}")

    def get_url_by_code(self, short_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a URL by its short code.

        Args:
            short_code: The short code to look up.

        Returns:
            Dictionary containing URL data or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, original_url, short_code, created_at,
                           click_count, is_active, expires_at
                    FROM urls
                    WHERE short_code = ? AND is_active = 1
                    AND (expires_at IS NULL OR expires_at > datetime('now'))
                """,
                    (short_code,),
                )

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            raise DatabaseError(f"Failed to retrieve URL: {e}")

    def get_url_by_id(self, url_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a URL by its ID.

        Args:
            url_id: The database ID of the URL.

        Returns:
            Dictionary containing URL data or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, original_url, short_code, created_at,
                           click_count, is_active, expires_at
                    FROM urls
                    WHERE id = ?
                """,
                    (url_id,),
                )

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            raise DatabaseError(f"Failed to retrieve URL: {e}")

    def increment_click_count(self, short_code: str) -> bool:
        """
        Increment the click count for a URL.

        Args:
            short_code: The short code of the URL.

        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE urls
                    SET click_count = click_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE short_code = ? AND is_active = 1
                """,
                    (short_code,),
                )
                conn.commit()

                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to update click count: {e}")
            return False

    def deactivate_url(self, short_code: str) -> bool:
        """
        Deactivate a URL (soft delete).

        Args:
            short_code: The short code of the URL to deactivate.

        Returns:
            True if deactivated successfully, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE urls
                    SET is_active = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE short_code = ?
                """,
                    (short_code,),
                )
                conn.commit()

                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to deactivate URL: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary containing various statistics.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total URLs
                cursor.execute("SELECT COUNT(*) as total FROM urls")
                total = cursor.fetchone()["total"]

                # Active URLs
                cursor.execute(
                    "SELECT COUNT(*) as active FROM urls WHERE is_active = 1"
                )
                active = cursor.fetchone()["active"]

                # Total clicks
                cursor.execute("SELECT SUM(click_count) as clicks FROM urls")
                clicks = cursor.fetchone()["clicks"] or 0

                # Most clicked
                cursor.execute(
                    """
                    SELECT original_url, short_code, click_count
                    FROM urls
                    WHERE is_active = 1
                    ORDER BY click_count DESC
                    LIMIT 5
                """
                )
                top_urls = [dict(row) for row in cursor.fetchall()]

                return {
                    "total_urls": total,
                    "active_urls": active,
                    "total_clicks": clicks,
                    "top_urls": top_urls,
                }
        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def cleanup_expired(self) -> int:
        """
        Remove expired URLs from the database.

        Returns:
            Number of URLs cleaned up.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE urls
                    SET is_active = 0
                    WHERE expires_at IS NOT NULL
                    AND expires_at <= datetime('now')
                    AND is_active = 1
                """
                )
                conn.commit()

                cleaned = cursor.rowcount
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired URLs")
                return cleaned
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup expired URLs: {e}")
            return 0
