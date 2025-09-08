"""
Code Security Analyzer for Enhanced Quality Gates
Advanced static analysis for security issues in source code
"""
import ast
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class SecuritySeverity(Enum):
    """Security issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityIssueType(Enum):
    """Types of security issues"""

    INJECTION_FLAW = "injection_flaw"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    SESSION_MANAGEMENT = "session_management"
    INSECURE_DIRECT_OBJECT_REFS = "insecure_direct_object_references"
    CROSS_SITE_SCRIPTING = "cross_site_scripting"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    INSECURE_CRYPTOGRAPHIC_STORAGE = "insecure_cryptographic_storage"
    INSECURE_COMMUNICATIONS = "insecure_communications"
    INSUFFICIENT_URL_ACCESS_RESTRICTION = "insufficient_url_access_restriction"
    UNVALIDATED_REDIRECTS = "unvalidated_redirects"
    HARDCODED_CREDENTIALS = "hardcoded_credentials"
    WEAK_RANDOMNESS = "weak_randomness"
    RACE_CONDITIONS = "race_conditions"
    BUFFER_OVERFLOWS = "buffer_overflows"
    FORMAT_STRING_VULNERABILITIES = "format_string_vulnerabilities"


@dataclass
class SecurityIssue:
    """Individual security issue found in code"""

    issue_type: SecurityIssueType
    severity: SecuritySeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    remediation_advice: Optional[str] = None
    confidence: float = 1.0  # 0-1 confidence score
    cwe_id: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSecurityResult:
    """Result of code security analysis"""

    scan_id: str
    timestamp: float
    total_issues: int
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues: List[SecurityIssue] = field(default_factory=list)
    scan_duration: float = 0.0
    files_analyzed: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def security_score(self) -> float:
        """Calculate security score (0-100, higher is better)"""
        if not self.issues:
            return 100.0

        severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 1}
        total_weight = sum(
            count * severity_weights.get(severity, 1)
            for severity, count in self.issues_by_severity.items()
        )

        # Normalize based on files analyzed
        max_possible = len(self.files_analyzed) * 10 if self.files_analyzed else 100
        score = max(0.0, 100.0 - (total_weight / max_possible * 100.0))
        return round(score, 2)

    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical security issues"""
        return self.issues_by_severity.get("critical", 0) > 0


class PythonSecurityAnalyzer:
    """Python-specific security analyzer using AST"""

    def __init__(self):
        self.dangerous_functions = {
            "eval": {
                "severity": SecuritySeverity.CRITICAL,
                "type": SecurityIssueType.INJECTION_FLAW,
            },
            "exec": {
                "severity": SecuritySeverity.CRITICAL,
                "type": SecurityIssueType.INJECTION_FLAW,
            },
            "compile": {
                "severity": SecuritySeverity.HIGH,
                "type": SecurityIssueType.INJECTION_FLAW,
            },
            "__import__": {
                "severity": SecuritySeverity.HIGH,
                "type": SecurityIssueType.INJECTION_FLAW,
            },
            "input": {
                "severity": SecuritySeverity.MEDIUM,
                "type": SecurityIssueType.INJECTION_FLAW,
            },
        }

        self.weak_crypto_functions = {
            "md5": SecuritySeverity.HIGH,
            "sha1": SecuritySeverity.MEDIUM,
            "des": SecuritySeverity.HIGH,
            "rc4": SecuritySeverity.HIGH,
        }

    def analyze_file(self, file_path: Path) -> List[SecurityIssue]:
        """Analyze a Python file for security issues"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                visitor = SecurityASTVisitor(str(file_path), content.splitlines())
                visitor.visit(tree)
                issues.extend(visitor.issues)
            except SyntaxError as e:
                logger.debug("Syntax error in file %s: %s", file_path, e)

        except Exception as e:
            logger.error("Error analyzing file %s: %s", file_path, e)

        return issues


class SecurityASTVisitor(ast.NodeVisitor):
    """AST visitor for finding security issues in Python code"""

    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.lines = lines
        self.issues = []
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ["eval", "exec", "compile", "__import__"]:
                self._add_issue(
                    SecurityIssueType.INJECTION_FLAW,
                    SecuritySeverity.CRITICAL,
                    f"Dangerous function call: {func_name}",
                    f"Use of {func_name}() can lead to code injection vulnerabilities",
                    node.lineno,
                    node.col_offset,
                    f"Avoid using {func_name}(). Use safer alternatives.",
                )
            elif func_name == "input" and len(node.args) == 0:
                self._add_issue(
                    SecurityIssueType.INJECTION_FLAW,
                    SecuritySeverity.MEDIUM,
                    "Unvalidated user input",
                    "Direct user input without validation can be dangerous",
                    node.lineno,
                    node.col_offset,
                    "Validate and sanitize user input before processing",
                )

        # Check for subprocess calls with shell=True
        elif isinstance(node.func, ast.Attribute):
            if (
                hasattr(node.func.value, "id")
                and node.func.value.id == "subprocess"
                and node.func.attr in ["run", "call", "Popen"]
            ):
                # Check for shell=True
                for keyword in node.keywords:
                    if (
                        keyword.arg == "shell"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        self._add_issue(
                            SecurityIssueType.INJECTION_FLAW,
                            SecuritySeverity.HIGH,
                            "Subprocess with shell=True",
                            "Using shell=True can lead to command injection",
                            node.lineno,
                            node.col_offset,
                            "Use shell=False and pass commands as lists",
                        )

        self.generic_visit(node)

    def visit_Assign(self, node):
        # Check for hardcoded credentials
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            value = node.value.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(
                        keyword in var_name
                        for keyword in ["password", "secret", "key", "token"]
                    ):
                        if len(value) > 8:  # Likely a real credential
                            self._add_issue(
                                SecurityIssueType.HARDCODED_CREDENTIALS,
                                SecuritySeverity.HIGH,
                                f"Hardcoded credential: {target.id}",
                                "Hardcoded credentials in source code are insecure",
                                node.lineno,
                                node.col_offset,
                                "Use environment variables or secure configuration",
                            )

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ["random"]:
                self._add_issue(
                    SecurityIssueType.WEAK_RANDOMNESS,
                    SecuritySeverity.MEDIUM,
                    "Use of weak random module",
                    "The 'random' module is not cryptographically secure",
                    node.lineno,
                    node.col_offset,
                    "Use 'secrets' module for cryptographic operations",
                )

        self.generic_visit(node)

    def _add_issue(
        self,
        issue_type: SecurityIssueType,
        severity: SecuritySeverity,
        title: str,
        description: str,
        line_num: int,
        col_num: int,
        remediation: str = None,
    ):
        """Add a security issue to the list"""
        code_snippet = ""
        if line_num <= len(self.lines):
            code_snippet = self.lines[line_num - 1].strip()

        issue = SecurityIssue(
            issue_type=issue_type,
            severity=severity,
            title=title,
            description=description,
            file_path=self.file_path,
            line_number=line_num,
            column_number=col_num,
            code_snippet=code_snippet,
            function_name=self.current_function,
            class_name=self.current_class,
            remediation_advice=remediation,
        )

        self.issues.append(issue)


class CodeSecurityAnalyzer:
    """Main code security analyzer supporting multiple languages"""

    def __init__(self, languages: List[str] = None):
        self.languages = languages or ["python", "javascript", "typescript", "java"]

        # Initialize language-specific analyzers
        self.python_analyzer = PythonSecurityAnalyzer()

        # Security patterns for pattern-based detection
        self.security_patterns = self._load_security_patterns()

        logger.info(
            "CodeSecurityAnalyzer initialized for languages: %s", self.languages
        )

    async def analyze_directory(
        self, directory_path: Union[str, Path]
    ) -> CodeSecurityResult:
        """Analyze security for all supported files in a directory"""
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        scan_id = self._generate_scan_id(str(directory))
        start_time = time.time()

        logger.info("Starting code security analysis for directory: %s", directory)

        # Collect files to analyze
        files_to_analyze = []
        language_patterns = {
            "python": ["**/*.py"],
            "javascript": ["**/*.js", "**/*.jsx"],
            "typescript": ["**/*.ts", "**/*.tsx"],
            "java": ["**/*.java"],
            "go": ["**/*.go"],
            "rust": ["**/*.rs"],
        }

        for language in self.languages:
            patterns = language_patterns.get(language, [])
            for pattern in patterns:
                files_to_analyze.extend(directory.glob(pattern))

        all_issues = []

        # Analyze each file
        for file_path in files_to_analyze:
            file_issues = await self._analyze_file(file_path)
            all_issues.extend(file_issues)

        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in SecuritySeverity}
        type_counts = {issue_type.value: 0 for issue_type in SecurityIssueType}

        for issue in all_issues:
            severity_counts[issue.severity.value] += 1
            type_counts[issue.issue_type.value] += 1

        end_time = time.time()

        result = CodeSecurityResult(
            scan_id=scan_id,
            timestamp=end_time,
            total_issues=len(all_issues),
            issues_by_severity=severity_counts,
            issues_by_type=type_counts,
            issues=all_issues,
            scan_duration=end_time - start_time,
            files_analyzed=[str(f) for f in files_to_analyze],
            analysis_metadata={
                "directory": str(directory),
                "languages": self.languages,
                "files_count": len(files_to_analyze),
            },
        )

        logger.info(
            "Code security analysis completed. Found %d issues in %d files",
            len(all_issues),
            len(files_to_analyze),
        )

        return result

    async def analyze_file(self, file_path: Union[str, Path]) -> CodeSecurityResult:
        """Analyze security for a single file"""
        file = Path(file_path)
        if not file.exists():
            raise ValueError(f"File does not exist: {file}")

        scan_id = self._generate_scan_id(str(file))
        start_time = time.time()

        logger.info("Starting code security analysis for file: %s", file)

        issues = await self._analyze_file(file)

        # Calculate statistics
        severity_counts = {severity.value: 0 for severity in SecuritySeverity}
        type_counts = {issue_type.value: 0 for issue_type in SecurityIssueType}

        for issue in issues:
            severity_counts[issue.severity.value] += 1
            type_counts[issue.issue_type.value] += 1

        end_time = time.time()

        result = CodeSecurityResult(
            scan_id=scan_id,
            timestamp=end_time,
            total_issues=len(issues),
            issues_by_severity=severity_counts,
            issues_by_type=type_counts,
            issues=issues,
            scan_duration=end_time - start_time,
            files_analyzed=[str(file)],
            analysis_metadata={
                "file": str(file),
                "file_size": file.stat().st_size,
                "language": self._detect_language(file),
            },
        )

        return result

    async def _analyze_file(self, file_path: Path) -> List[SecurityIssue]:
        """Analyze a single file for security issues"""
        issues = []

        # Determine file language
        language = self._detect_language(file_path)

        # Use language-specific analyzer if available
        if language == "python":
            issues.extend(self.python_analyzer.analyze_file(file_path))

        # Always run pattern-based analysis
        pattern_issues = await self._pattern_based_analysis(file_path, language)
        issues.extend(pattern_issues)

        return issues

    async def _pattern_based_analysis(
        self, file_path: Path, language: str
    ) -> List[SecurityIssue]:
        """Perform pattern-based security analysis"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Get patterns for the detected language
            patterns = self.security_patterns.get(language, [])

            for pattern_info in patterns:
                matches = re.finditer(
                    pattern_info["pattern"], content, re.MULTILINE | re.IGNORECASE
                )

                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    issue = SecurityIssue(
                        issue_type=SecurityIssueType(pattern_info["type"]),
                        severity=SecuritySeverity(pattern_info["severity"]),
                        title=pattern_info["title"],
                        description=pattern_info["description"],
                        file_path=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        remediation_advice=pattern_info.get("remediation"),
                        confidence=pattern_info.get("confidence", 0.8),
                        cwe_id=pattern_info.get("cwe_id"),
                        metadata={"pattern": pattern_info["pattern"]},
                    )
                    issues.append(issue)

        except Exception as e:
            logger.error("Error in pattern analysis for file %s: %s", file_path, e)

        return issues

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
        }
        return language_map.get(suffix, "unknown")

    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security patterns for different languages"""
        return {
            "javascript": [
                {
                    "pattern": r"eval\s*\(",
                    "type": "injection_flaw",
                    "severity": "critical",
                    "title": "JavaScript eval() usage",
                    "description": "Use of eval() can lead to code injection",
                    "remediation": "Avoid eval(). Use JSON.parse() for JSON or safer alternatives",
                    "cwe_id": "CWE-95",
                },
                {
                    "pattern": r"innerHTML\s*=.*\+",
                    "type": "cross_site_scripting",
                    "severity": "medium",
                    "title": "Potential XSS via innerHTML",
                    "description": "Dynamic innerHTML assignment can lead to XSS",
                    "remediation": "Use textContent or properly escape HTML content",
                    "cwe_id": "CWE-79",
                },
            ],
            "python": [
                {
                    "pattern": r"pickle\.loads?\s*\(",
                    "type": "insecure_cryptographic_storage",
                    "severity": "high",
                    "title": "Unsafe pickle deserialization",
                    "description": "pickle.load/loads can execute arbitrary code",
                    "remediation": "Use json or other safe serialization formats",
                    "cwe_id": "CWE-502",
                }
            ],
            "java": [
                {
                    "pattern": r"Runtime\.getRuntime\(\)\.exec",
                    "type": "injection_flaw",
                    "severity": "high",
                    "title": "Runtime.exec() usage",
                    "description": "Runtime.exec() can lead to command injection",
                    "remediation": "Validate and sanitize command arguments",
                    "cwe_id": "CWE-78",
                }
            ],
        }

    def _generate_scan_id(self, input_string: str) -> str:
        """Generate unique scan ID"""
        import hashlib

        return hashlib.sha256(f"{input_string}_{time.time()}".encode()).hexdigest()[:16]


# Convenience function for quick security analysis
async def quick_security_analysis(
    path: Union[str, Path], languages: List[str] = None
) -> CodeSecurityResult:
    """Perform a quick security analysis on a file or directory"""
    analyzer = CodeSecurityAnalyzer(languages=languages)

    path_obj = Path(path)
    if path_obj.is_dir():
        return await analyzer.analyze_directory(path_obj)
    else:
        return await analyzer.analyze_file(path_obj)
