"""Data models for Security Analysis MCP Server"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum


class SeverityLevel(str, Enum):
    """Security issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScanType(str, Enum):
    """Types of security scans"""
    SAST = "sast"  # Static Application Security Testing
    DEPENDENCIES = "dependencies"
    SECRETS = "secrets"
    LICENSE = "license"
    BEST_PRACTICES = "best_practices"
    ALL = "all"


class SecurityIssue(BaseModel):
    """Individual security issue"""
    id: str = Field(description="Unique issue identifier")
    type: str = Field(description="Issue type (e.g., SQL Injection, Hardcoded Secret)")
    severity: SeverityLevel
    title: str = Field(description="Issue title")
    description: str = Field(description="Detailed description")
    file_path: Optional[str] = Field(default=None, description="Affected file")
    line_number: Optional[int] = Field(default=None, description="Line number")
    column: Optional[int] = Field(default=None, description="Column number")
    code_snippet: Optional[str] = Field(default=None, description="Affected code")
    cwe_id: Optional[str] = Field(default=None, description="CWE identifier")
    cve_id: Optional[str] = Field(default=None, description="CVE identifier")
    fix_suggestion: Optional[str] = Field(default=None, description="How to fix the issue")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    
    
class DependencyVulnerability(BaseModel):
    """Dependency vulnerability information"""
    package_name: str
    installed_version: str
    vulnerable_versions: List[str]
    severity: SeverityLevel
    cve_id: Optional[str] = None
    description: str
    fixed_version: Optional[str] = None
    advisory_url: Optional[str] = None


class LicenseInfo(BaseModel):
    """License information for a package"""
    package_name: str
    version: str
    license: str
    is_allowed: bool
    license_url: Optional[str] = None
    
    
class SecretFinding(BaseModel):
    """Detected secret in code"""
    type: str = Field(description="Type of secret (e.g., API Key, Password)")
    file_path: str
    line_number: int
    column_start: int
    column_end: int
    matched_pattern: str
    redacted_secret: str = Field(description="Partially redacted secret for identification")
    commit_sha: Optional[str] = Field(default=None, description="Git commit SHA if applicable")
    author: Optional[str] = Field(default=None, description="Commit author if applicable")
    date: Optional[datetime] = None


class BestPracticeViolation(BaseModel):
    """Security best practice violation"""
    rule_id: str
    title: str
    description: str
    severity: SeverityLevel
    file_path: str
    line_number: Optional[int] = None
    recommendation: str
    category: str = Field(description="Category (e.g., Authentication, Cryptography)")


class ScanRequest(BaseModel):
    """Security scan request"""
    project_path: str = Field(description="Path to project to scan")
    scan_type: ScanType = Field(default=ScanType.ALL)
    severity_threshold: Optional[SeverityLevel] = Field(default=SeverityLevel.LOW)
    exclude_paths: List[str] = Field(default_factory=list)
    include_dev_dependencies: bool = Field(default=False)
    fix_vulnerabilities: bool = Field(default=False)
    output_format: Literal["json", "html", "markdown"] = Field(default="json")


class ScanResult(BaseModel):
    """Security scan result"""
    scan_id: str
    scan_type: ScanType
    project_path: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[SecurityIssue] = Field(default_factory=list)
    dependencies_scanned: Optional[int] = None
    files_scanned: Optional[int] = None
    lines_scanned: Optional[int] = None
    passed: bool = Field(description="Whether scan passed based on threshold")
    
    
class DependencyAuditResult(BaseModel):
    """Dependency audit result"""
    total_dependencies: int
    vulnerable_dependencies: int
    vulnerabilities: List[DependencyVulnerability]
    suggested_updates: Dict[str, str] = Field(
        default_factory=dict,
        description="Package name to suggested version mapping"
    )
    audit_date: datetime
    
    
class SecretScanResult(BaseModel):
    """Secret scanning result"""
    total_files_scanned: int
    total_secrets_found: int
    secrets: List[SecretFinding]
    scan_date: datetime
    included_git_history: bool = False
    
    
class LicenseCheckResult(BaseModel):
    """License compliance check result"""
    total_packages: int
    compliant_packages: int
    non_compliant_packages: int
    packages: List[LicenseInfo]
    allowed_licenses: List[str]
    check_date: datetime
    
    
class BestPracticesResult(BaseModel):
    """Security best practices check result"""
    total_violations: int
    violations_by_category: Dict[str, int]
    violations: List[BestPracticeViolation]
    language: str
    framework: Optional[str] = None
    check_date: datetime
    

class VulnerabilityFix(BaseModel):
    """Vulnerability fix information"""
    vulnerability_id: str
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    current_version: Optional[str] = None
    fixed_version: Optional[str] = None
    fix_applied: bool
    fix_type: Literal["upgrade", "patch", "workaround", "configuration"]
    fix_description: str
    backup_created: bool = False
    rollback_available: bool = False
    

class SecurityReport(BaseModel):
    """Comprehensive security report"""
    report_id: str
    project_name: str
    project_path: str
    scan_date: datetime
    scanner_version: str
    
    # Scan results
    sast_result: Optional[ScanResult] = None
    dependency_audit: Optional[DependencyAuditResult] = None
    secret_scan: Optional[SecretScanResult] = None
    license_check: Optional[LicenseCheckResult] = None
    best_practices: Optional[BestPracticesResult] = None
    
    # Summary
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list)
    recommended_fixes: List[VulnerabilityFix] = Field(default_factory=list)
    
    # Compliance
    compliance_status: Dict[str, bool] = Field(
        default_factory=dict,
        description="Compliance with various standards (e.g., OWASP, PCI-DSS)"
    )
    
    # Risk score (0-100)
    risk_score: float = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]