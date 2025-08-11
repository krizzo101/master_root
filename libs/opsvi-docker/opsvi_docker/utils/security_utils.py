"""
Security Utility Functions

Docker security scanning and vulnerability detection utilities.
Provides security assessment and compliance checking capabilities.
"""

import logging
import subprocess
import json
import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Security finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """Security finding data."""

    id: str
    title: str
    description: str
    severity: Severity
    category: str
    remediation: str
    references: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VulnerabilityReport:
    """Vulnerability scan report."""

    target: str
    scan_type: str
    timestamp: datetime
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings: List[SecurityFinding]
    scan_duration_ms: float
    scanner_version: str = ""


class SecurityUtils:
    """
    Security utility functions.

    Provides security assessment utilities:
    - Container security scanning
    - Image vulnerability assessment
    - Configuration security analysis
    - Compliance checking
    """

    @staticmethod
    def scan_container_security(
        container_info: Dict[str, Any]
    ) -> List[SecurityFinding]:
        """Scan container for security issues."""
        findings = []

        try:
            config = container_info.get("Config", {})
            host_config = container_info.get("HostConfig", {})

            # Check privileged mode
            if host_config.get("Privileged", False):
                findings.append(
                    SecurityFinding(
                        id="PRIV-001",
                        title="Container running in privileged mode",
                        description="Container has full access to host resources",
                        severity=Severity.CRITICAL,
                        category="privilege_escalation",
                        remediation="Remove --privileged flag and use specific capabilities instead",
                    )
                )

            # Check user
            user = config.get("User", "")
            if not user or user == "root" or user == "0":
                findings.append(
                    SecurityFinding(
                        id="USER-001",
                        title="Container running as root user",
                        description="Container processes have root privileges",
                        severity=Severity.HIGH,
                        category="privilege_escalation",
                        remediation="Create and use a non-root user in the container",
                    )
                )

            # Check read-only root filesystem
            if not host_config.get("ReadonlyRootfs", False):
                findings.append(
                    SecurityFinding(
                        id="FS-001",
                        title="Root filesystem is writable",
                        description="Container can modify its root filesystem",
                        severity=Severity.MEDIUM,
                        category="filesystem_security",
                        remediation="Use --read-only flag to make root filesystem read-only",
                    )
                )

        except Exception as e:
            logger.error(f"Error scanning container security: {e}")

        return findings


class VulnerabilityScanner:
    """
    Vulnerability scanner wrapper.

    Provides unified interface for different vulnerability scanners.
    """

    def __init__(self, scanner: str = "trivy"):
        self.scanner = scanner
        self.available_scanners = ["trivy"]

    def is_available(self) -> bool:
        """Check if the scanner is available."""
        try:
            if self.scanner == "trivy":
                result = subprocess.run(
                    ["trivy", "--version"], capture_output=True, timeout=10
                )
                return result.returncode == 0
        except Exception:
            return False

        return False
