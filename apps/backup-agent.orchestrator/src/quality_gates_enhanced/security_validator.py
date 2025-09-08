"""
Security Validator for Enhanced Quality Gates
Comprehensive security validation with vulnerability scanning and threat detection
"""
import hashlib
import json
import logging
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import requests

logger = logging.getLogger(__name__)


class VulnerabilityType(Enum):
    """Types of security vulnerabilities"""

    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRETS = "hardcoded_secrets"
    INSECURE_CRYPTO = "insecure_cryptography"
    WEAK_AUTHENTICATION = "weak_authentication"
    IMPROPER_VALIDATION = "improper_validation"
    BUFFER_OVERFLOW = "buffer_overflow"
    RACE_CONDITION = "race_condition"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    INSUFFICIENT_LOGGING = "insufficient_logging"


class VulnerabilitySeverity(Enum):
    """Severity levels for vulnerabilities"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityVulnerability:
    """Individual security vulnerability finding"""

    vulnerability_type: VulnerabilityType
    severity: VulnerabilitySeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    cvss_score: Optional[float] = None  # Common Vulnerability Scoring System
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityResult:
    """Result of security validation"""

    scan_id: str
    timestamp: float
    total_vulnerabilities: int
    vulnerabilities_by_severity: Dict[str, int] = field(default_factory=dict)
    vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    scan_duration: float = 0.0
    scanned_files: List[str] = field(default_factory=list)
    scan_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_secure(self) -> bool:
        """Check if the scan result indicates the code is secure"""
        critical_count = self.vulnerabilities_by_severity.get("critical", 0)
        high_count = self.vulnerabilities_by_severity.get("high", 0)
        return critical_count == 0 and high_count == 0

    @property
    def risk_score(self) -> float:
        """Calculate overall risk score (0-100)"""
        weights = {
            "critical": 10.0,
            "high": 7.5,
            "medium": 5.0,
            "low": 2.5,
            "info": 1.0,
        }

        total_weighted = sum(
            count * weights.get(severity, 0)
            for severity, count in self.vulnerabilities_by_severity.items()
        )

        # Normalize to 0-100 scale
        max_possible = len(self.scanned_files) * 10.0 if self.scanned_files else 100.0
        return min(100.0, (total_weighted / max_possible) * 100.0)


class SecurityValidator:
    """Comprehensive security validator with multiple scanning engines"""

    def __init__(
        self,
        enable_static_analysis: bool = True,
        enable_dependency_scan: bool = True,
        enable_secrets_scan: bool = True,
        enable_pattern_matching: bool = True,
    ):
        self.enable_static_analysis = enable_static_analysis
        self.enable_dependency_scan = enable_dependency_scan
        self.enable_secrets_scan = enable_secrets_scan
        self.enable_pattern_matching = enable_pattern_matching

        # Security patterns for pattern matching
        self.security_patterns = self._load_security_patterns()

        # Known vulnerability patterns
        self.secret_patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret_key": r"[0-9a-zA-Z/+]{40}",
            "github_token": r"gh[ps]_[A-Za-z0-9_]{36}",
            "slack_token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
            "private_key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
            "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\']?[0-9a-zA-Z]{32,}',
            "password": r'password["\']?\s*[:=]\s*["\'][^"\'\s]{8,}["\']',
        }

        logger.info("SecurityValidator initialized")

    async def validate_directory(
        self, directory_path: Union[str, Path]
    ) -> SecurityResult:
        """Validate security for an entire directory"""
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        scan_id = self._generate_scan_id(str(directory))
        start_time = time.time()

        logger.info("Starting security scan for directory: %s", directory)

        # Collect all files to scan
        files_to_scan = []
        for pattern in [
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.java",
            "**/*.go",
            "**/*.rs",
        ]:
            files_to_scan.extend(directory.glob(pattern))

        all_vulnerabilities = []

        # Pattern-based scanning
        if self.enable_pattern_matching:
            for file_path in files_to_scan:
                vulnerabilities = await self._scan_file_patterns(file_path)
                all_vulnerabilities.extend(vulnerabilities)

        # Secrets scanning
        if self.enable_secrets_scan:
            for file_path in files_to_scan:
                vulnerabilities = await self._scan_secrets(file_path)
                all_vulnerabilities.extend(vulnerabilities)

        # Static analysis (if bandit is available for Python)
        if self.enable_static_analysis:
            python_files = list(directory.glob("**/*.py"))
            if python_files:
                vulnerabilities = await self._run_bandit_scan(python_files)
                all_vulnerabilities.extend(vulnerabilities)

        # Dependency scanning
        if self.enable_dependency_scan:
            vulnerabilities = await self._scan_dependencies(directory)
            all_vulnerabilities.extend(vulnerabilities)

        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in VulnerabilitySeverity}
        for vuln in all_vulnerabilities:
            severity_counts[vuln.severity.value] += 1

        end_time = time.time()

        result = SecurityResult(
            scan_id=scan_id,
            timestamp=end_time,
            total_vulnerabilities=len(all_vulnerabilities),
            vulnerabilities_by_severity=severity_counts,
            vulnerabilities=all_vulnerabilities,
            scan_duration=end_time - start_time,
            scanned_files=[str(f) for f in files_to_scan],
            scan_metadata={
                "directory": str(directory),
                "scanners_used": {
                    "pattern_matching": self.enable_pattern_matching,
                    "secrets_scan": self.enable_secrets_scan,
                    "static_analysis": self.enable_static_analysis,
                    "dependency_scan": self.enable_dependency_scan,
                },
            },
        )

        logger.info(
            "Security scan completed. Found %d vulnerabilities",
            len(all_vulnerabilities),
        )

        return result

    async def validate_file(self, file_path: Union[str, Path]) -> SecurityResult:
        """Validate security for a single file"""
        file = Path(file_path)
        if not file.exists():
            raise ValueError(f"File does not exist: {file}")

        scan_id = self._generate_scan_id(str(file))
        start_time = time.time()

        logger.info("Starting security scan for file: %s", file)

        all_vulnerabilities = []

        # Pattern-based scanning
        if self.enable_pattern_matching:
            vulnerabilities = await self._scan_file_patterns(file)
            all_vulnerabilities.extend(vulnerabilities)

        # Secrets scanning
        if self.enable_secrets_scan:
            vulnerabilities = await self._scan_secrets(file)
            all_vulnerabilities.extend(vulnerabilities)

        # Static analysis for Python files
        if self.enable_static_analysis and file.suffix == ".py":
            vulnerabilities = await self._run_bandit_scan([file])
            all_vulnerabilities.extend(vulnerabilities)

        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in VulnerabilitySeverity}
        for vuln in all_vulnerabilities:
            severity_counts[vuln.severity.value] += 1

        end_time = time.time()

        result = SecurityResult(
            scan_id=scan_id,
            timestamp=end_time,
            total_vulnerabilities=len(all_vulnerabilities),
            vulnerabilities_by_severity=severity_counts,
            vulnerabilities=all_vulnerabilities,
            scan_duration=end_time - start_time,
            scanned_files=[str(file)],
            scan_metadata={
                "file": str(file),
                "file_size": file.stat().st_size,
                "scanners_used": {
                    "pattern_matching": self.enable_pattern_matching,
                    "secrets_scan": self.enable_secrets_scan,
                    "static_analysis": self.enable_static_analysis
                    and file.suffix == ".py",
                },
            },
        )

        logger.info(
            "Security scan completed for file. Found %d vulnerabilities",
            len(all_vulnerabilities),
        )

        return result

    async def _scan_file_patterns(self, file_path: Path) -> List[SecurityVulnerability]:
        """Scan file for security patterns"""
        vulnerabilities = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern_name, patterns in self.security_patterns.items():
                    for pattern_info in patterns:
                        if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                            vulnerability = SecurityVulnerability(
                                vulnerability_type=VulnerabilityType(
                                    pattern_info["type"]
                                ),
                                severity=VulnerabilitySeverity(
                                    pattern_info["severity"]
                                ),
                                title=f"{pattern_name} detected",
                                description=pattern_info["description"],
                                file_path=str(file_path),
                                line_number=line_num,
                                code_snippet=line.strip(),
                                remediation=pattern_info.get("remediation"),
                                metadata={"pattern_name": pattern_name},
                            )
                            vulnerabilities.append(vulnerability)

        except Exception as e:
            logger.error("Error scanning file %s: %s", file_path, e)

        return vulnerabilities

    async def _scan_secrets(self, file_path: Path) -> List[SecurityVulnerability]:
        """Scan file for hardcoded secrets"""
        vulnerabilities = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            for secret_type, pattern in self.secret_patterns.items():
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    # Find line number
                    line_num = content[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    vulnerability = SecurityVulnerability(
                        vulnerability_type=VulnerabilityType.HARDCODED_SECRETS,
                        severity=VulnerabilitySeverity.HIGH,
                        title=f"Hardcoded {secret_type.replace('_', ' ').title()} Detected",
                        description=f"Potential hardcoded {secret_type} found in source code",
                        file_path=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        remediation="Move secrets to environment variables or secure vault",
                        metadata={
                            "secret_type": secret_type,
                            "match": match.group()[:20] + "...",
                        },
                    )
                    vulnerabilities.append(vulnerability)

        except Exception as e:
            logger.error("Error scanning secrets in file %s: %s", file_path, e)

        return vulnerabilities

    async def _run_bandit_scan(self, files: List[Path]) -> List[SecurityVulnerability]:
        """Run bandit static analysis tool"""
        vulnerabilities = []

        try:
            # Check if bandit is available
            result = subprocess.run(
                ["bandit", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                logger.warning("Bandit not available, skipping static analysis")
                return vulnerabilities

            # Create temporary file list
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                for file_path in files:
                    f.write(str(file_path) + "\n")
                file_list_path = f.name

            try:
                # Run bandit
                cmd = [
                    "bandit",
                    "-r",
                    "-f",
                    "json",
                    "--confidence-level",
                    "medium",
                    "--severity-level",
                    "medium",
                    *[str(f) for f in files],
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.stdout:
                    bandit_data = json.loads(result.stdout)
                    for issue in bandit_data.get("results", []):
                        severity_map = {
                            "LOW": VulnerabilitySeverity.LOW,
                            "MEDIUM": VulnerabilitySeverity.MEDIUM,
                            "HIGH": VulnerabilitySeverity.HIGH,
                        }

                        vulnerability = SecurityVulnerability(
                            vulnerability_type=VulnerabilityType.IMPROPER_VALIDATION,
                            severity=severity_map.get(
                                issue.get("issue_severity", "MEDIUM"),
                                VulnerabilitySeverity.MEDIUM,
                            ),
                            title=issue.get("test_name", "Static Analysis Issue"),
                            description=issue.get(
                                "issue_text", "Security issue detected"
                            ),
                            file_path=issue.get("filename"),
                            line_number=issue.get("line_number"),
                            code_snippet=issue.get("code", "").strip(),
                            cwe_id=issue.get("test_id"),
                            remediation="Review and fix the security issue as recommended",
                            metadata={"bandit_test_id": issue.get("test_id")},
                        )
                        vulnerabilities.append(vulnerability)

            finally:
                # Clean up temp file
                Path(file_list_path).unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            logger.error("Bandit scan timed out")
        except Exception as e:
            logger.error("Error running bandit scan: %s", e)

        return vulnerabilities

    async def _scan_dependencies(self, directory: Path) -> List[SecurityVulnerability]:
        """Scan for vulnerable dependencies"""
        vulnerabilities = []

        # Scan Python dependencies
        requirements_files = list(directory.glob("**/requirements*.txt"))
        requirements_files.extend(directory.glob("**/Pipfile"))
        requirements_files.extend(directory.glob("**/pyproject.toml"))

        for req_file in requirements_files:
            vulns = await self._scan_python_dependencies(req_file)
            vulnerabilities.extend(vulns)

        # Scan Node.js dependencies
        package_json_files = list(directory.glob("**/package.json"))
        for package_file in package_json_files:
            vulns = await self._scan_nodejs_dependencies(package_file)
            vulnerabilities.extend(vulns)

        return vulnerabilities

    async def _scan_python_dependencies(
        self, requirements_file: Path
    ) -> List[SecurityVulnerability]:
        """Scan Python dependencies for vulnerabilities"""
        vulnerabilities = []

        try:
            # Try using safety if available
            result = subprocess.run(
                ["safety", "check", "--json", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout:
                safety_data = json.loads(result.stdout)
                for issue in safety_data:
                    vulnerability = SecurityVulnerability(
                        vulnerability_type=VulnerabilityType.INSECURE_DESERIALIZATION,
                        severity=VulnerabilitySeverity.HIGH,
                        title=f"Vulnerable dependency: {issue.get('package', 'Unknown')}",
                        description=issue.get(
                            "advisory", "Known vulnerability in dependency"
                        ),
                        file_path=str(requirements_file),
                        remediation=f"Update to version {issue.get('analyzed_version', 'latest')} or higher",
                        metadata={
                            "package": issue.get("package"),
                            "vulnerability_id": issue.get("id"),
                        },
                    )
                    vulnerabilities.append(vulnerability)

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as e:
            logger.debug("Could not run safety check: %s", e)

        return vulnerabilities

    async def _scan_nodejs_dependencies(
        self, package_file: Path
    ) -> List[SecurityVulnerability]:
        """Scan Node.js dependencies for vulnerabilities"""
        vulnerabilities = []

        try:
            # Try using npm audit
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=package_file.parent,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)
                for vuln_id, vuln in audit_data.get("vulnerabilities", {}).items():
                    severity_map = {
                        "info": VulnerabilitySeverity.INFO,
                        "low": VulnerabilitySeverity.LOW,
                        "moderate": VulnerabilitySeverity.MEDIUM,
                        "high": VulnerabilitySeverity.HIGH,
                        "critical": VulnerabilitySeverity.CRITICAL,
                    }

                    vulnerability = SecurityVulnerability(
                        vulnerability_type=VulnerabilityType.INSECURE_DESERIALIZATION,
                        severity=severity_map.get(
                            vuln.get("severity", "medium"), VulnerabilitySeverity.MEDIUM
                        ),
                        title=f"Vulnerable Node.js dependency: {vuln.get('name', 'Unknown')}",
                        description=vuln.get(
                            "title", "Known vulnerability in Node.js dependency"
                        ),
                        file_path=str(package_file),
                        remediation=vuln.get(
                            "recommendation", "Update to latest secure version"
                        ),
                        references=vuln.get("references", []),
                        metadata={
                            "package": vuln.get("name"),
                            "vulnerability_id": vuln_id,
                            "via": vuln.get("via", []),
                        },
                    )
                    vulnerabilities.append(vulnerability)

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as e:
            logger.debug("Could not run npm audit: %s", e)

        return vulnerabilities

    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security patterns for scanning"""
        return {
            "sql_injection": [
                {
                    "pattern": r"(SELECT|INSERT|UPDATE|DELETE).*(\+|%|\|\|).*",
                    "type": "sql_injection",
                    "severity": "high",
                    "description": "Potential SQL injection vulnerability",
                    "remediation": "Use parameterized queries or prepared statements",
                }
            ],
            "command_injection": [
                {
                    "pattern": r"(exec|eval|system|shell_exec|passthru|subprocess\.(run|call|Popen))\s*\([^)]*\$",
                    "type": "command_injection",
                    "severity": "critical",
                    "description": "Potential command injection vulnerability",
                    "remediation": "Validate and sanitize all user input before execution",
                }
            ],
            "xss": [
                {
                    "pattern": r"innerHTML\s*=.*\+",
                    "type": "cross_site_scripting",
                    "severity": "medium",
                    "description": "Potential XSS vulnerability with innerHTML",
                    "remediation": "Use textContent or properly escape HTML",
                }
            ],
            "path_traversal": [
                {
                    "pattern": r"(\.\.\/|\.\.\\)",
                    "type": "path_traversal",
                    "severity": "medium",
                    "description": "Potential path traversal vulnerability",
                    "remediation": "Validate and canonicalize file paths",
                }
            ],
            "weak_crypto": [
                {
                    "pattern": r"(MD5|SHA1|DES|RC4)\s*\(",
                    "type": "insecure_cryptography",
                    "severity": "medium",
                    "description": "Use of weak cryptographic algorithm",
                    "remediation": "Use SHA-256 or stronger cryptographic algorithms",
                }
            ],
        }

    def _generate_scan_id(self, input_string: str) -> str:
        """Generate unique scan ID"""
        import time

        return hashlib.sha256(f"{input_string}_{time.time()}".encode()).hexdigest()[:16]


# Convenience function for quick security scans
async def quick_security_scan(
    path: Union[str, Path], enable_all_scanners: bool = True
) -> SecurityResult:
    """Perform a quick security scan on a file or directory"""
    validator = SecurityValidator(
        enable_static_analysis=enable_all_scanners,
        enable_dependency_scan=enable_all_scanners,
        enable_secrets_scan=True,
        enable_pattern_matching=True,
    )

    path_obj = Path(path)
    if path_obj.is_dir():
        return await validator.validate_directory(path_obj)
    else:
        return await validator.validate_file(path_obj)
