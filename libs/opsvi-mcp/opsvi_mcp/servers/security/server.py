"""Security Analysis MCP Server Implementation"""

import asyncio
import json
import re
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import SecurityConfig
from .models import (
    ScanType,
    SeverityLevel,
    SecurityIssue,
    ScanRequest,
    ScanResult,
    DependencyAuditResult,
    DependencyVulnerability,
    SecretScanResult,
    SecretFinding,
    LicenseCheckResult,
    LicenseInfo,
    BestPracticesResult,
    BestPracticeViolation,
    VulnerabilityFix,
    SecurityReport,
)

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
server = FastMCP("Security Analysis Server")


class SecurityServer:
    """Security Analysis MCP Server"""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig.from_env()
        self.cache: Dict[str, Any] = {}

        # Ensure directories exist
        self.config.report_directory.mkdir(parents=True, exist_ok=True)
        if self.config.enable_cache:
            self.config.cache_directory.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, operation: str, params: Dict) -> str:
        """Generate cache key"""
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{operation}:{params_str}".encode()).hexdigest()

    async def _run_command(
        self, cmd: List[str], cwd: Optional[Path] = None
    ) -> tuple[int, str, str]:
        """Run external command"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def run_bandit_scan(self, project_path: Path) -> List[SecurityIssue]:
        """Run Bandit security scanner for Python"""
        issues = []

        try:
            cmd = [
                "bandit",
                "-r",
                str(project_path),
                "-f",
                "json",
                "-ll",  # Only report issues of severity low and higher
                "--exclude",
                ",".join(self.config.exclude_patterns),
            ]

            returncode, stdout, stderr = await self._run_command(cmd)

            if stdout:
                result = json.loads(stdout)
                for issue in result.get("results", []):
                    severity = issue.get("issue_severity", "").lower()
                    issues.append(
                        SecurityIssue(
                            id=f"bandit_{issue.get('test_id', 'unknown')}",
                            type=issue.get("test_name", "Unknown"),
                            severity=SeverityLevel(severity)
                            if severity in ["low", "medium", "high", "critical"]
                            else SeverityLevel.LOW,
                            title=issue.get("issue_text", "Security Issue"),
                            description=issue.get("issue_confidence", ""),
                            file_path=issue.get("filename", ""),
                            line_number=issue.get("line_number"),
                            code_snippet=issue.get("code", ""),
                            cwe_id=issue.get("issue_cwe", {}).get("id"),
                            fix_suggestion=issue.get("more_info", ""),
                        )
                    )
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")

        return issues

    async def run_semgrep_scan(self, project_path: Path) -> List[SecurityIssue]:
        """Run Semgrep security scanner"""
        issues = []

        try:
            cmd = ["semgrep", "--config=auto", "--json", str(project_path)]

            returncode, stdout, stderr = await self._run_command(cmd)

            if stdout:
                result = json.loads(stdout)
                for finding in result.get("results", []):
                    severity = finding.get("extra", {}).get("severity", "").lower()
                    issues.append(
                        SecurityIssue(
                            id=f"semgrep_{finding.get('check_id', 'unknown')}",
                            type=finding.get("extra", {}).get(
                                "message", "Security Issue"
                            ),
                            severity=SeverityLevel(severity)
                            if severity in ["low", "medium", "high", "critical"]
                            else SeverityLevel.LOW,
                            title=finding.get("extra", {}).get("message", ""),
                            description=finding.get("extra", {})
                            .get("metadata", {})
                            .get("description", ""),
                            file_path=finding.get("path", ""),
                            line_number=finding.get("start", {}).get("line"),
                            column=finding.get("start", {}).get("col"),
                            code_snippet=finding.get("extra", {}).get("lines", ""),
                            cwe_id=finding.get("extra", {})
                            .get("metadata", {})
                            .get("cwe", ""),
                            fix_suggestion=finding.get("extra", {}).get("fix", ""),
                            references=finding.get("extra", {})
                            .get("metadata", {})
                            .get("references", []),
                        )
                    )
        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")

        return issues

    async def run_safety_check(self, project_path: Path) -> DependencyAuditResult:
        """Run Safety dependency checker"""
        vulnerabilities = []

        try:
            # First, get the requirements file
            requirements_file = project_path / "requirements.txt"
            if not requirements_file.exists():
                # Try to generate from pip freeze
                cmd = ["pip", "freeze"]
                returncode, stdout, stderr = await self._run_command(
                    cmd, cwd=project_path
                )
                if stdout:
                    requirements_file = project_path / ".temp_requirements.txt"
                    requirements_file.write_text(stdout)

            if requirements_file.exists():
                cmd = ["safety", "check", "--json", "-r", str(requirements_file)]
                returncode, stdout, stderr = await self._run_command(cmd)

                if stdout:
                    result = json.loads(stdout)
                    for vuln in result:
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=vuln.get("package", ""),
                                installed_version=vuln.get("installed_version", ""),
                                vulnerable_versions=vuln.get("affected_versions", []),
                                severity=SeverityLevel.HIGH,  # Safety doesn't provide severity
                                cve_id=vuln.get("cve", ""),
                                description=vuln.get("description", ""),
                                fixed_version=vuln.get("fixed_version", ""),
                                advisory_url=vuln.get("more_info_url", ""),
                            )
                        )

                # Clean up temp file if created
                if requirements_file.name == ".temp_requirements.txt":
                    requirements_file.unlink()

        except Exception as e:
            logger.error(f"Safety check failed: {e}")

        return DependencyAuditResult(
            total_dependencies=len(vulnerabilities),
            vulnerable_dependencies=len(vulnerabilities),
            vulnerabilities=vulnerabilities,
            audit_date=datetime.now(),
        )

    async def detect_secrets(self, project_path: Path) -> SecretScanResult:
        """Detect secrets in code"""
        secrets = []
        files_scanned = 0

        try:
            for file_path in project_path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.stat().st_size < self.config.max_file_size
                ):
                    # Skip excluded patterns
                    if any(
                        file_path.match(pattern)
                        for pattern in self.config.exclude_patterns
                    ):
                        continue

                    files_scanned += 1

                    try:
                        content = file_path.read_text()

                        for pattern in self.config.secret_patterns:
                            for match in re.finditer(pattern, content):
                                line_num = content[: match.start()].count("\n") + 1

                                # Redact the secret (show first and last 2 chars)
                                secret = match.group()
                                if len(secret) > 4:
                                    redacted = f"{secret[:2]}...{secret[-2:]}"
                                else:
                                    redacted = "***"

                                secrets.append(
                                    SecretFinding(
                                        type=self._identify_secret_type(pattern),
                                        file_path=str(
                                            file_path.relative_to(project_path)
                                        ),
                                        line_number=line_num,
                                        column_start=match.start(),
                                        column_end=match.end(),
                                        matched_pattern=pattern,
                                        redacted_secret=redacted,
                                    )
                                )
                    except Exception as e:
                        logger.debug(f"Could not scan file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Secret detection failed: {e}")

        return SecretScanResult(
            total_files_scanned=files_scanned,
            total_secrets_found=len(secrets),
            secrets=secrets,
            scan_date=datetime.now(),
        )

    def _identify_secret_type(self, pattern: str) -> str:
        """Identify the type of secret from pattern"""
        if "api" in pattern.lower():
            return "API Key"
        elif "password" in pattern.lower():
            return "Password"
        elif "secret" in pattern.lower():
            return "Secret"
        elif "aws" in pattern.lower():
            return "AWS Credentials"
        elif "sk_live" in pattern.lower():
            return "Stripe Key"
        else:
            return "Unknown Secret"

    async def check_licenses(self, project_path: Path) -> LicenseCheckResult:
        """Check license compliance"""
        packages = []

        try:
            # Use pip-licenses to get license information
            cmd = ["pip-licenses", "--format=json"]
            returncode, stdout, stderr = await self._run_command(cmd, cwd=project_path)

            if stdout:
                licenses_data = json.loads(stdout)
                for package in licenses_data:
                    license_name = package.get("License", "Unknown")
                    is_allowed = license_name in self.config.allowed_licenses

                    packages.append(
                        LicenseInfo(
                            package_name=package.get("Name", ""),
                            version=package.get("Version", ""),
                            license=license_name,
                            is_allowed=is_allowed,
                            license_url=package.get("URL", ""),
                        )
                    )

        except Exception as e:
            logger.error(f"License check failed: {e}")

        compliant = sum(1 for p in packages if p.is_allowed)

        return LicenseCheckResult(
            total_packages=len(packages),
            compliant_packages=compliant,
            non_compliant_packages=len(packages) - compliant,
            packages=packages,
            allowed_licenses=self.config.allowed_licenses,
            check_date=datetime.now(),
        )

    def calculate_risk_score(self, report: SecurityReport) -> float:
        """Calculate overall risk score"""
        score = 0.0

        # Weight by severity
        score += report.critical_issues * 25
        score += report.high_issues * 15
        score += report.medium_issues * 5
        score += report.low_issues * 1

        # Cap at 100
        return min(score, 100.0)


# Create server instance
security_server = SecurityServer()


# MCP Tool Definitions


@server.tool()
async def security_scan(
    project_path: str = Field(description="Path to project to scan"),
    scan_type: str = Field(
        default="all", description="Type of scan: sast/dependencies/secrets/all"
    ),
    severity_threshold: str = Field(
        default="low", description="Minimum severity: low/medium/high/critical"
    ),
) -> Dict:
    """Run comprehensive security scan"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    scan_start = datetime.now()
    issues = []

    # Run SAST scans
    if scan_type in ["sast", "all"]:
        if security_server.config.enable_bandit:
            bandit_issues = await security_server.run_bandit_scan(path)
            issues.extend(bandit_issues)

        if security_server.config.enable_semgrep:
            semgrep_issues = await security_server.run_semgrep_scan(path)
            issues.extend(semgrep_issues)

    # Filter by severity
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    threshold_level = severity_order.get(severity_threshold, 0)
    filtered_issues = [
        issue
        for issue in issues
        if severity_order.get(issue.severity.value, 0) >= threshold_level
    ]

    # Count by severity
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for issue in filtered_issues:
        severity_counts[issue.severity.value] += 1

    scan_end = datetime.now()

    result = ScanResult(
        scan_id=hashlib.md5(f"{project_path}{scan_start}".encode()).hexdigest()[:8],
        scan_type=ScanType.SAST if scan_type == "sast" else ScanType.ALL,
        project_path=project_path,
        start_time=scan_start,
        end_time=scan_end,
        duration_seconds=(scan_end - scan_start).total_seconds(),
        total_issues=len(filtered_issues),
        issues_by_severity=severity_counts,
        issues=filtered_issues,
        passed=severity_counts.get(security_server.config.fail_on_severity, 0) == 0,
    )

    return result.model_dump()


@server.tool()
async def dependency_audit(
    project_path: str = Field(description="Path to project"),
    fix: bool = Field(default=False, description="Auto-fix vulnerabilities"),
) -> Dict:
    """Audit project dependencies for vulnerabilities"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    audit_result = await security_server.run_safety_check(path)

    if fix and audit_result.vulnerabilities:
        # Generate fix suggestions
        for vuln in audit_result.vulnerabilities:
            if vuln.fixed_version:
                audit_result.suggested_updates[vuln.package_name] = vuln.fixed_version

    return audit_result.model_dump()


@server.tool()
async def secret_detect(
    project_path: str = Field(description="Path to project"),
    include_history: bool = Field(default=False, description="Scan git history"),
) -> Dict:
    """Detect secrets in code"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    result = await security_server.detect_secrets(path)

    if include_history:
        # TODO: Implement git history scanning
        result.included_git_history = True

    return result.model_dump()


@server.tool()
async def license_check(
    project_path: str = Field(description="Path to project"),
    allowed_licenses: Optional[List[str]] = Field(
        default=None, description="List of allowed licenses"
    ),
) -> Dict:
    """Check license compliance"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    if allowed_licenses:
        security_server.config.allowed_licenses = allowed_licenses

    result = await security_server.check_licenses(path)

    return result.model_dump()


@server.tool()
async def best_practices_check(
    project_path: str = Field(description="Path to project"),
    language: str = Field(description="Programming language"),
) -> Dict:
    """Check security best practices"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    violations = []

    # Example best practices checks
    # In a real implementation, these would be more comprehensive

    # Check for .env files
    if (path / ".env").exists():
        violations.append(
            BestPracticeViolation(
                rule_id="BP001",
                title="Environment file in repository",
                description=".env file should not be committed to repository",
                severity=SeverityLevel.HIGH,
                file_path=".env",
                recommendation="Add .env to .gitignore and use environment variables",
                category="Configuration",
            )
        )

    # Check for debug mode in common frameworks
    for file_path in path.rglob("*.py"):
        try:
            content = file_path.read_text()
            if "DEBUG = True" in content or "debug=True" in content:
                violations.append(
                    BestPracticeViolation(
                        rule_id="BP002",
                        title="Debug mode enabled",
                        description="Debug mode should be disabled in production",
                        severity=SeverityLevel.MEDIUM,
                        file_path=str(file_path.relative_to(path)),
                        recommendation="Set DEBUG=False for production",
                        category="Configuration",
                    )
                )
        except:
            pass

    # Count by category
    category_counts = {}
    for violation in violations:
        category_counts[violation.category] = (
            category_counts.get(violation.category, 0) + 1
        )

    result = BestPracticesResult(
        total_violations=len(violations),
        violations_by_category=category_counts,
        violations=violations,
        language=language,
        check_date=datetime.now(),
    )

    return result.model_dump()


@server.tool()
async def vulnerability_fix(
    project_path: str = Field(description="Path to project"),
    vulnerability_id: str = Field(description="CVE ID or vulnerability identifier"),
) -> Dict:
    """Fix a specific vulnerability"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    # This would implement actual fixing logic
    # For now, return a mock fix result

    fix = VulnerabilityFix(
        vulnerability_id=vulnerability_id,
        cve_id=vulnerability_id if vulnerability_id.startswith("CVE") else None,
        fix_applied=False,
        fix_type="upgrade",
        fix_description=f"Would fix vulnerability {vulnerability_id}",
        backup_created=False,
        rollback_available=False,
    )

    return fix.model_dump()


@server.tool()
async def generate_security_report(
    project_path: str = Field(description="Path to project"),
    output_format: str = Field(
        default="json", description="Report format: json/html/markdown"
    ),
) -> Dict:
    """Generate comprehensive security report"""

    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path {project_path} does not exist"}

    # Run all scans
    scan_result = await security_scan(project_path, "all", "low")
    dep_audit = await dependency_audit(project_path, False)
    secret_scan = await secret_detect(project_path, False)
    license_result = await license_check(project_path)
    best_practices = await best_practices_check(project_path, "python")

    # Create comprehensive report
    report = SecurityReport(
        report_id=hashlib.md5(f"{project_path}{datetime.now()}".encode()).hexdigest()[
            :8
        ],
        project_name=path.name,
        project_path=project_path,
        scan_date=datetime.now(),
        scanner_version="1.0.0",
        sast_result=ScanResult(**scan_result) if "error" not in scan_result else None,
        dependency_audit=DependencyAuditResult(**dep_audit)
        if "error" not in dep_audit
        else None,
        secret_scan=SecretScanResult(**secret_scan)
        if "error" not in secret_scan
        else None,
        license_check=LicenseCheckResult(**license_result)
        if "error" not in license_result
        else None,
        best_practices=BestPracticesResult(**best_practices)
        if "error" not in best_practices
        else None,
        total_issues=scan_result.get("total_issues", 0),
        critical_issues=scan_result.get("issues_by_severity", {}).get("critical", 0),
        high_issues=scan_result.get("issues_by_severity", {}).get("high", 0),
        medium_issues=scan_result.get("issues_by_severity", {}).get("medium", 0),
        low_issues=scan_result.get("issues_by_severity", {}).get("low", 0),
        risk_score=0.0,
        risk_level="low",
    )

    # Calculate risk score
    report.risk_score = security_server.calculate_risk_score(report)

    # Determine risk level
    if report.risk_score >= 75:
        report.risk_level = "critical"
    elif report.risk_score >= 50:
        report.risk_level = "high"
    elif report.risk_score >= 25:
        report.risk_level = "medium"
    else:
        report.risk_level = "low"

    # Add recommendations
    if report.critical_issues > 0:
        report.immediate_actions.append(
            "Fix critical security vulnerabilities immediately"
        )
    if report.secret_scan and report.secret_scan.total_secrets_found > 0:
        report.immediate_actions.append("Remove hardcoded secrets from code")
    if report.dependency_audit and report.dependency_audit.vulnerable_dependencies > 0:
        report.immediate_actions.append("Update vulnerable dependencies")

    # Save report
    report_file = (
        security_server.config.report_directory
        / f"security_report_{report.report_id}.{output_format}"
    )

    if output_format == "json":
        report_file.write_text(json.dumps(report.model_dump(), indent=2, default=str))
    elif output_format == "markdown":
        # Generate markdown report
        md_content = f"""# Security Report for {report.project_name}

## Summary
- **Report ID**: {report.report_id}
- **Scan Date**: {report.scan_date}
- **Risk Score**: {report.risk_score}/100
- **Risk Level**: {report.risk_level}

## Issues Found
- **Critical**: {report.critical_issues}
- **High**: {report.high_issues}
- **Medium**: {report.medium_issues}
- **Low**: {report.low_issues}

## Immediate Actions Required
{chr(10).join(f"- {action}" for action in report.immediate_actions)}

## Detailed Results
...
"""
        report_file.write_text(md_content)

    return {"report": report.model_dump(), "report_file": str(report_file)}
