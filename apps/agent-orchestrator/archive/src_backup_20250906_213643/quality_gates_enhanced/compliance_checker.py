"""
Compliance Checker for Enhanced Quality Gates  
Enterprise-grade compliance validation for various standards (SOX, GDPR, HIPAA, etc.)
"""
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    SOX = "sarbanes_oxley"  # Sarbanes-Oxley Act
    GDPR = "gdpr"  # General Data Protection Regulation
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001"  # Information Security Management
    NIST = "nist"  # NIST Cybersecurity Framework
    OWASP = "owasp"  # OWASP Security Guidelines
    CIS = "cis"  # Center for Internet Security Controls


class ComplianceSeverity(Enum):
    """Severity levels for compliance issues"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceIssue:
    """Individual compliance issue"""
    standard: ComplianceStandard
    control_id: str
    severity: ComplianceSeverity
    title: str
    description: str
    requirement: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceResult:
    """Result of compliance validation"""
    scan_id: str
    timestamp: float
    standards_checked: List[str] = field(default_factory=list)
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_standard: Dict[str, int] = field(default_factory=dict)
    issues: List[ComplianceIssue] = field(default_factory=list)
    scan_duration: float = 0.0
    scanned_files: List[str] = field(default_factory=list)
    compliance_score: float = 0.0  # 0-100 score
    scan_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_compliant(self) -> bool:
        """Check if the scan indicates compliance"""
        critical_count = self.issues_by_severity.get('critical', 0)
        high_count = self.issues_by_severity.get('high', 0)
        return critical_count == 0 and high_count == 0
    
    def get_compliance_by_standard(self, standard: ComplianceStandard) -> float:
        """Get compliance score for specific standard (0-100)"""
        standard_issues = [issue for issue in self.issues if issue.standard == standard]
        if not standard_issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0.5}
        total_weight = sum(severity_weights.get(issue.severity.value, 1) for issue in standard_issues)
        
        # Calculate compliance score (inverse of issues)
        max_possible = len(self.scanned_files) * 4 if self.scanned_files else 100
        return max(0.0, 100.0 - (total_weight / max_possible * 100.0))


class ComplianceChecker:
    """Enterprise compliance checker with multiple standard support"""
    
    def __init__(self, standards: List[ComplianceStandard] = None):
        self.standards = standards or [
            ComplianceStandard.GDPR,
            ComplianceStandard.SOX, 
            ComplianceStandard.OWASP,
            ComplianceStandard.NIST
        ]
        
        # Load compliance rules
        self.compliance_rules = self._load_compliance_rules()
        
        logger.info("ComplianceChecker initialized for standards: %s", 
                   [s.value for s in self.standards])
    
    async def check_directory(self, directory_path: Union[str, Path]) -> ComplianceResult:
        """Check compliance for an entire directory"""
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        scan_id = self._generate_scan_id(str(directory))
        start_time = time.time()
        
        logger.info("Starting compliance check for directory: %s", directory)
        
        # Collect files to scan
        files_to_scan = []
        for pattern in ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.go', 
                       '**/*.json', '**/*.yml', '**/*.yaml', '**/*.md', '**/*.txt']:
            files_to_scan.extend(directory.glob(pattern))
        
        all_issues = []
        
        # Check each standard
        for standard in self.standards:
            issues = await self._check_standard_compliance(standard, directory, files_to_scan)
            all_issues.extend(issues)
        
        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in ComplianceSeverity}
        standard_counts = {standard.value: 0 for standard in self.standards}
        
        for issue in all_issues:
            severity_counts[issue.severity.value] += 1
            standard_counts[issue.standard.value] += 1
        
        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(all_issues, len(files_to_scan))
        
        end_time = time.time()
        
        result = ComplianceResult(
            scan_id=scan_id,
            timestamp=end_time,
            standards_checked=[s.value for s in self.standards],
            total_issues=len(all_issues),
            issues_by_severity=severity_counts,
            issues_by_standard=standard_counts,
            issues=all_issues,
            scan_duration=end_time - start_time,
            scanned_files=[str(f) for f in files_to_scan],
            compliance_score=compliance_score,
            scan_metadata={
                'directory': str(directory),
                'standards_checked': [s.value for s in self.standards]
            }
        )
        
        logger.info("Compliance check completed. Found %d issues across %d standards", 
                   len(all_issues), len(self.standards))
        
        return result
    
    async def check_file(self, file_path: Union[str, Path], 
                        standards: List[ComplianceStandard] = None) -> ComplianceResult:
        """Check compliance for a single file"""
        file = Path(file_path)
        if not file.exists():
            raise ValueError(f"File does not exist: {file}")
        
        standards = standards or self.standards
        
        scan_id = self._generate_scan_id(str(file))
        start_time = time.time()
        
        logger.info("Starting compliance check for file: %s", file)
        
        all_issues = []
        
        # Check each standard
        for standard in standards:
            issues = await self._check_file_compliance(standard, file)
            all_issues.extend(issues)
        
        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in ComplianceSeverity}
        standard_counts = {standard.value: 0 for standard in standards}
        
        for issue in all_issues:
            severity_counts[issue.severity.value] += 1
            standard_counts[issue.standard.value] += 1
        
        compliance_score = self._calculate_compliance_score(all_issues, 1)
        
        end_time = time.time()
        
        result = ComplianceResult(
            scan_id=scan_id,
            timestamp=end_time,
            standards_checked=[s.value for s in standards],
            total_issues=len(all_issues),
            issues_by_severity=severity_counts,
            issues_by_standard=standard_counts,
            issues=all_issues,
            scan_duration=end_time - start_time,
            scanned_files=[str(file)],
            compliance_score=compliance_score,
            scan_metadata={
                'file': str(file),
                'file_size': file.stat().st_size,
                'standards_checked': [s.value for s in standards]
            }
        )
        
        return result
    
    async def _check_standard_compliance(self, standard: ComplianceStandard, 
                                       directory: Path, 
                                       files: List[Path]) -> List[ComplianceIssue]:
        """Check compliance for a specific standard"""
        issues = []
        
        rules = self.compliance_rules.get(standard.value, [])
        
        for rule in rules:
            rule_issues = await self._apply_rule(rule, standard, directory, files)
            issues.extend(rule_issues)
        
        return issues
    
    async def _check_file_compliance(self, standard: ComplianceStandard, 
                                   file_path: Path) -> List[ComplianceIssue]:
        """Check compliance for a specific standard on a single file"""
        issues = []
        
        rules = self.compliance_rules.get(standard.value, [])
        
        for rule in rules:
            if rule['type'] == 'file_pattern':
                rule_issues = await self._apply_file_pattern_rule(rule, standard, file_path)
                issues.extend(rule_issues)
            elif rule['type'] == 'content_pattern':
                rule_issues = await self._apply_content_pattern_rule(rule, standard, file_path)
                issues.extend(rule_issues)
        
        return issues
    
    async def _apply_rule(self, rule: Dict[str, Any], standard: ComplianceStandard,
                         directory: Path, files: List[Path]) -> List[ComplianceIssue]:
        """Apply a specific compliance rule"""
        issues = []
        
        if rule['type'] == 'file_pattern':
            for file_path in files:
                rule_issues = await self._apply_file_pattern_rule(rule, standard, file_path)
                issues.extend(rule_issues)
        
        elif rule['type'] == 'content_pattern':
            for file_path in files:
                rule_issues = await self._apply_content_pattern_rule(rule, standard, file_path)
                issues.extend(rule_issues)
        
        elif rule['type'] == 'directory_structure':
            rule_issues = await self._apply_directory_structure_rule(rule, standard, directory)
            issues.extend(rule_issues)
        
        elif rule['type'] == 'documentation':
            rule_issues = await self._apply_documentation_rule(rule, standard, directory)
            issues.extend(rule_issues)
        
        return issues
    
    async def _apply_file_pattern_rule(self, rule: Dict[str, Any], 
                                     standard: ComplianceStandard,
                                     file_path: Path) -> List[ComplianceIssue]:
        """Apply file pattern compliance rule"""
        issues = []
        
        pattern = rule.get('pattern', '')
        if re.search(pattern, str(file_path)):
            issue = ComplianceIssue(
                standard=standard,
                control_id=rule['control_id'],
                severity=ComplianceSeverity(rule['severity']),
                title=rule['title'],
                description=rule['description'],
                requirement=rule['requirement'],
                file_path=str(file_path),
                remediation=rule.get('remediation'),
                references=rule.get('references', []),
                metadata={'rule_type': 'file_pattern', 'pattern': pattern}
            )
            issues.append(issue)
        
        return issues
    
    async def _apply_content_pattern_rule(self, rule: Dict[str, Any],
                                        standard: ComplianceStandard,
                                        file_path: Path) -> List[ComplianceIssue]:
        """Apply content pattern compliance rule"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            pattern = rule.get('pattern', '')
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                issue = ComplianceIssue(
                    standard=standard,
                    control_id=rule['control_id'],
                    severity=ComplianceSeverity(rule['severity']),
                    title=rule['title'],
                    description=rule['description'],
                    requirement=rule['requirement'],
                    file_path=str(file_path),
                    line_number=line_num,
                    evidence=line_content.strip(),
                    remediation=rule.get('remediation'),
                    references=rule.get('references', []),
                    metadata={'rule_type': 'content_pattern', 'pattern': pattern}
                )
                issues.append(issue)
        
        except Exception as e:
            logger.debug("Error checking file %s: %s", file_path, e)
        
        return issues
    
    async def _apply_directory_structure_rule(self, rule: Dict[str, Any],
                                            standard: ComplianceStandard,
                                            directory: Path) -> List[ComplianceIssue]:
        """Apply directory structure compliance rule"""
        issues = []
        
        required_paths = rule.get('required_paths', [])
        for req_path in required_paths:
            full_path = directory / req_path
            if not full_path.exists():
                issue = ComplianceIssue(
                    standard=standard,
                    control_id=rule['control_id'],
                    severity=ComplianceSeverity(rule['severity']),
                    title=rule['title'],
                    description=f"{rule['description']} - Missing: {req_path}",
                    requirement=rule['requirement'],
                    file_path=str(directory),
                    remediation=rule.get('remediation'),
                    references=rule.get('references', []),
                    metadata={'rule_type': 'directory_structure', 'missing_path': req_path}
                )
                issues.append(issue)
        
        return issues
    
    async def _apply_documentation_rule(self, rule: Dict[str, Any],
                                      standard: ComplianceStandard,
                                      directory: Path) -> List[ComplianceIssue]:
        """Apply documentation compliance rule"""
        issues = []
        
        doc_patterns = rule.get('documentation_patterns', [])
        for pattern in doc_patterns:
            matching_files = list(directory.glob(pattern))
            if not matching_files:
                issue = ComplianceIssue(
                    standard=standard,
                    control_id=rule['control_id'],
                    severity=ComplianceSeverity(rule['severity']),
                    title=rule['title'],
                    description=f"{rule['description']} - Missing documentation matching: {pattern}",
                    requirement=rule['requirement'],
                    file_path=str(directory),
                    remediation=rule.get('remediation'),
                    references=rule.get('references', []),
                    metadata={'rule_type': 'documentation', 'missing_pattern': pattern}
                )
                issues.append(issue)
        
        return issues
    
    def _load_compliance_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load compliance rules for different standards"""
        return {
            ComplianceStandard.GDPR.value: [
                {
                    'control_id': 'GDPR-7.1',
                    'type': 'content_pattern',
                    'pattern': r'(email|phone|address|ssn|social.security)',
                    'severity': 'medium',
                    'title': 'Potential PII Data Processing',
                    'description': 'Code may process personally identifiable information (PII)',
                    'requirement': 'GDPR requires explicit consent and data protection for PII',
                    'remediation': 'Ensure proper consent handling and data encryption for PII',
                    'references': ['https://gdpr-info.eu/art-7-gdpr/']
                },
                {
                    'control_id': 'GDPR-32',
                    'type': 'content_pattern', 
                    'pattern': r'(password|secret|key)\s*=\s*["\'][^"\']{8,}["\']',
                    'severity': 'high',
                    'title': 'Hardcoded Credentials in PII Context',
                    'description': 'Hardcoded credentials may compromise data protection',
                    'requirement': 'GDPR requires secure data processing and storage',
                    'remediation': 'Use secure credential management and encryption',
                    'references': ['https://gdpr-info.eu/art-32-gdpr/']
                }
            ],
            ComplianceStandard.SOX.value: [
                {
                    'control_id': 'SOX-404',
                    'type': 'documentation',
                    'documentation_patterns': ['**/AUDIT*.md', '**/audit*.txt', '**/control*.md'],
                    'severity': 'high',
                    'title': 'Missing Audit Documentation',
                    'description': 'SOX requires comprehensive audit documentation',
                    'requirement': 'Section 404 requires internal control documentation',
                    'remediation': 'Create detailed audit and control documentation',
                    'references': ['https://www.sox-online.com/sox_404.html']
                },
                {
                    'control_id': 'SOX-302',
                    'type': 'content_pattern',
                    'pattern': r'(financial|revenue|expense|accounting|audit)',
                    'severity': 'medium', 
                    'title': 'Financial Data Processing',
                    'description': 'Code processes financial data subject to SOX controls',
                    'requirement': 'SOX requires controls over financial reporting',
                    'remediation': 'Implement proper access controls and audit trails',
                    'references': ['https://www.sox-online.com/sox_302.html']
                }
            ],
            ComplianceStandard.OWASP.value: [
                {
                    'control_id': 'OWASP-A01',
                    'type': 'content_pattern',
                    'pattern': r'eval\s*\(',
                    'severity': 'critical',
                    'title': 'Code Injection Vulnerability',
                    'description': 'Use of eval() creates injection vulnerabilities',
                    'requirement': 'OWASP Top 10 A01 - Broken Access Control',
                    'remediation': 'Avoid eval() and use safer alternatives',
                    'references': ['https://owasp.org/Top10/A01_2021-Broken_Access_Control/']
                },
                {
                    'control_id': 'OWASP-A02',
                    'type': 'content_pattern',
                    'pattern': r'(MD5|SHA1)\s*\(',
                    'severity': 'high',
                    'title': 'Weak Cryptographic Hash',
                    'description': 'Use of weak cryptographic hash functions',
                    'requirement': 'OWASP Top 10 A02 - Cryptographic Failures',
                    'remediation': 'Use SHA-256 or stronger hash functions',
                    'references': ['https://owasp.org/Top10/A02_2021-Cryptographic_Failures/']
                }
            ],
            ComplianceStandard.NIST.value: [
                {
                    'control_id': 'NIST-SI-10',
                    'type': 'content_pattern',
                    'pattern': r'input\s*\(\s*\)|raw_input\s*\(',
                    'severity': 'medium',
                    'title': 'Insufficient Input Validation',
                    'description': 'Direct input without validation',
                    'requirement': 'NIST SI-10 - Information Input Validation',
                    'remediation': 'Implement comprehensive input validation',
                    'references': ['https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf']
                },
                {
                    'control_id': 'NIST-AU-12',
                    'type': 'directory_structure',
                    'required_paths': ['logs/', 'audit/'],
                    'severity': 'medium',
                    'title': 'Missing Audit Infrastructure',
                    'description': 'No audit or logging infrastructure detected',
                    'requirement': 'NIST AU-12 - Audit Generation',
                    'remediation': 'Implement comprehensive audit logging system',
                    'references': ['https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf']
                }
            ]
        }
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue], 
                                  num_files: int) -> float:
        """Calculate overall compliance score (0-100)"""
        if not issues:
            return 100.0
        
        severity_weights = {
            'critical': 4.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0,
            'info': 0.5
        }
        
        total_weight = sum(severity_weights.get(issue.severity.value, 1.0) for issue in issues)
        
        # Normalize based on number of files and maximum possible weight per file
        max_possible_weight = num_files * 4.0 if num_files > 0 else 100.0
        
        # Calculate compliance score (inverse of issues)
        compliance_percentage = max(0.0, 100.0 - (total_weight / max_possible_weight * 100.0))
        
        return round(compliance_percentage, 2)
    
    def _generate_scan_id(self, input_string: str) -> str:
        """Generate unique scan ID"""
        import hashlib
        return hashlib.sha256(f"{input_string}_{time.time()}".encode()).hexdigest()[:16]


# Convenience function for quick compliance checks
async def quick_compliance_check(path: Union[str, Path], 
                               standards: List[ComplianceStandard] = None) -> ComplianceResult:
    """Perform a quick compliance check on a file or directory"""
    checker = ComplianceChecker(standards=standards)
    
    path_obj = Path(path)
    if path_obj.is_dir():
        return await checker.check_directory(path_obj)
    else:
        return await checker.check_file(path_obj, standards=standards)