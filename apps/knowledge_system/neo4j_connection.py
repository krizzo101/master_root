#!/usr/bin/env python3
"""
Singleton Neo4j connection manager to avoid authentication issues
"""

import logging
import os
from typing import Optional

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Singleton Neo4j connection manager"""

    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_driver(self):
        """Get or create Neo4j driver"""
        if self._driver is None:
            try:
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password")

                self._driver = GraphDatabase.driver(uri, auth=(user, password))

                # Test the connection
                with self._driver.session() as session:
                    result = session.run("RETURN 1")
                    result.single()

                logger.info("Neo4j driver initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Neo4j driver: {e}")
                self._driver = None
                raise

        return self._driver

    def close(self):
        """Close the driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def execute_query(self, query: str, params: dict = None):
        """Execute a query and return results"""
        driver = self.get_driver()
        if not driver:
            raise ConnectionError("Neo4j driver not available")

        with driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]


# Global singleton instance
neo4j_conn = Neo4jConnection()
