"""Configuration for Security Analysis MCP Server"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path


@dataclass
class SecurityConfig:
    """Security server configuration"""
    
    # Scanning tools
    enable_bandit: bool = True
    enable_semgrep: bool = True
    enable_safety: bool = True
    enable_secret_detection: bool = True
    
    # Paths
    scan_directory: Path = field(default_factory=lambda: Path.cwd())
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.pyc", "__pycache__", ".git", "node_modules", ".venv", "venv"
    ])
    
    # Severity thresholds
    severity_threshold: str = "low"  # low, medium, high, critical
    fail_on_severity: str = "high"  # Fail scan if issues >= this severity
    
    # Secret detection
    secret_patterns: List[str] = field(default_factory=lambda: [
        r"(?i)(api[_\s-]?key|api[_\s-]?secret|access[_\s-]?token)",
        r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
        r"(?i)(secret|private[_\s-]?key)\s*=\s*['\"][^'\"]+['\"]",
        r"(?i)AWS[A-Z0-9]{16,}",
        r"(?i)sk_live_[a-zA-Z0-9]{24,}"
    ])
    
    # License compliance
    allowed_licenses: List[str] = field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause",
        "ISC", "Python-2.0", "LGPL-3.0", "GPL-3.0"
    ])
    
    # Reporting
    output_format: str = "json"  # json, html, markdown
    report_directory: Path = field(default_factory=lambda: Path("/tmp/security_reports"))
    
    # Performance
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    scan_timeout: int = 300  # 5 minutes
    parallel_scans: bool = True
    max_workers: int = 4
    
    # Cache
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    cache_directory: Path = field(default_factory=lambda: Path("/tmp/security_cache"))
    
    # CI/CD Integration
    github_token: Optional[str] = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    gitlab_token: Optional[str] = field(default_factory=lambda: os.getenv("GITLAB_TOKEN"))
    
    # Semgrep rules
    semgrep_rules: List[str] = field(default_factory=lambda: [
        "auto",  # Use Semgrep's auto configuration
        "security",
        "secrets"
    ])
    
    # Custom rules
    custom_rules_directory: Optional[Path] = None
    
    # Notifications
    slack_webhook: Optional[str] = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK"))
    email_notifications: bool = False
    email_recipients: List[str] = field(default_factory=list)
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create config from environment variables"""
        return cls(
            enable_bandit=os.getenv("SECURITY_ENABLE_BANDIT", "true").lower() == "true",
            enable_semgrep=os.getenv("SECURITY_ENABLE_SEMGREP", "true").lower() == "true",
            enable_safety=os.getenv("SECURITY_ENABLE_SAFETY", "true").lower() == "true",
            enable_secret_detection=os.getenv("SECURITY_ENABLE_SECRETS", "true").lower() == "true",
            severity_threshold=os.getenv("SECURITY_SEVERITY_THRESHOLD", "low"),
            fail_on_severity=os.getenv("SECURITY_FAIL_ON_SEVERITY", "high"),
            output_format=os.getenv("SECURITY_OUTPUT_FORMAT", "json"),
            parallel_scans=os.getenv("SECURITY_PARALLEL_SCANS", "true").lower() == "true",
            max_workers=int(os.getenv("SECURITY_MAX_WORKERS", "4")),
            enable_cache=os.getenv("SECURITY_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.getenv("SECURITY_CACHE_TTL", "3600"))
        )