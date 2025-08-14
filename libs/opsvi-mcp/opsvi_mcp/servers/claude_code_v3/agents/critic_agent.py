"""Critic agent for code review and quality assurance"""

import re
import ast
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    """Severity levels for issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Issue:
    """Represents a code issue"""
    severity: IssueSeverity
    category: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ReviewResult:
    """Result of code review"""
    overall_score: float = 0.0
    passed: bool = False
    issues: List[Issue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Category scores
    code_quality_score: float = 0.0
    architecture_score: float = 0.0
    best_practices_score: float = 0.0
    performance_score: float = 0.0
    security_score: float = 0.0
    documentation_score: float = 0.0


class CriticAgent:
    """Reviews and critiques work performed"""
    
    def __init__(self, config=None):
        self.config = config
        self.quality_threshold = 0.8 if not config else config.quality_threshold
        
    async def review(self, work_product: Dict) -> ReviewResult:
        """Perform comprehensive review"""
        
        result = ReviewResult()
        
        # Determine content type
        content_type = work_product.get('type', 'code')
        content = work_product.get('content', '')
        language = work_product.get('language', 'python')
        
        if content_type == 'code':
            # Perform code review
            result = await self._review_code(content, language)
        elif content_type == 'documentation':
            # Review documentation
            result = await self._review_documentation(content)
        elif content_type == 'configuration':
            # Review configuration
            result = await self._review_configuration(content)
        
        # Calculate overall score
        result.overall_score = self._calculate_overall_score(result)
        result.passed = result.overall_score >= self.quality_threshold
        
        # Generate improvement suggestions
        result.suggestions = self._generate_suggestions(result)
        
        return result
    
    async def _review_code(self, code: str, language: str) -> ReviewResult:
        """Review code quality"""
        
        result = ReviewResult()
        
        # 1. Code quality checks
        quality_issues = self._check_code_quality(code, language)
        result.issues.extend(quality_issues)
        result.code_quality_score = self._score_from_issues(quality_issues)
        
        # 2. Architecture checks
        arch_issues = self._check_architecture(code, language)
        result.issues.extend(arch_issues)
        result.architecture_score = self._score_from_issues(arch_issues)
        
        # 3. Best practices checks
        bp_issues = self._check_best_practices(code, language)
        result.issues.extend(bp_issues)
        result.best_practices_score = self._score_from_issues(bp_issues)
        
        # 4. Performance checks
        perf_issues = self._check_performance(code, language)
        result.issues.extend(perf_issues)
        result.performance_score = self._score_from_issues(perf_issues)
        
        # 5. Security checks
        sec_issues = self._check_security(code, language)
        result.issues.extend(sec_issues)
        result.security_score = self._score_from_issues(sec_issues)
        
        # 6. Documentation checks
        doc_issues = self._check_documentation(code, language)
        result.issues.extend(doc_issues)
        result.documentation_score = self._score_from_issues(doc_issues)
        
        # 7. Calculate metrics
        result.metrics = self._calculate_code_metrics(code, language)
        
        return result
    
    def _check_code_quality(self, code: str, language: str) -> List[Issue]:
        """Check code quality aspects"""
        issues = []
        
        if language == 'python':
            # Check line length
            for i, line in enumerate(code.split('\n'), 1):
                if len(line) > 100:
                    issues.append(Issue(
                        severity=IssueSeverity.LOW,
                        category="formatting",
                        message=f"Line too long ({len(line)} > 100 characters)",
                        line=i,
                        suggestion="Break long lines for better readability"
                    ))
            
            # Check function complexity
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_complexity(node)
                        if complexity > 10:
                            issues.append(Issue(
                                severity=IssueSeverity.MEDIUM,
                                category="complexity",
                                message=f"Function '{node.name}' has high complexity ({complexity})",
                                line=node.lineno,
                                suggestion="Consider breaking down into smaller functions"
                            ))
            except SyntaxError:
                issues.append(Issue(
                    severity=IssueSeverity.CRITICAL,
                    category="syntax",
                    message="Code has syntax errors",
                    suggestion="Fix syntax errors before review"
                ))
        
        # Check naming conventions
        if language in ['python', 'javascript', 'typescript']:
            # Check for non-descriptive names
            bad_names = re.findall(r'\b[a-z]\b|\btemp\b|\bdata\b|\bvar\b', code)
            if bad_names:
                issues.append(Issue(
                    severity=IssueSeverity.LOW,
                    category="naming",
                    message="Found non-descriptive variable names",
                    suggestion="Use descriptive names for better code readability"
                ))
        
        return issues
    
    def _check_architecture(self, code: str, language: str) -> List[Issue]:
        """Check architectural patterns"""
        issues = []
        
        # Check for proper separation of concerns
        if 'database' in code.lower() and 'render' in code.lower():
            issues.append(Issue(
                severity=IssueSeverity.MEDIUM,
                category="architecture",
                message="Mixing data access and presentation logic",
                suggestion="Separate data access from presentation layer"
            ))
        
        # Check for dependency injection
        if language == 'python':
            # Simple check for hardcoded dependencies
            if 'import' in code and '()' in code:
                instantiations = re.findall(r'(\w+)\s*=\s*\w+\(\)', code)
                if len(instantiations) > 5:
                    issues.append(Issue(
                        severity=IssueSeverity.LOW,
                        category="architecture",
                        message="Many hardcoded instantiations detected",
                        suggestion="Consider using dependency injection"
                    ))
        
        return issues
    
    def _check_best_practices(self, code: str, language: str) -> List[Issue]:
        """Check adherence to best practices"""
        issues = []
        
        # Check for error handling
        if language == 'python':
            try_count = code.count('try:')
            except_count = code.count('except:')
            bare_except = code.count('except:')
            
            if bare_except > 0:
                issues.append(Issue(
                    severity=IssueSeverity.MEDIUM,
                    category="error_handling",
                    message="Bare except clauses found",
                    suggestion="Specify exception types in except clauses"
                ))
            
            # Check for missing error handling
            if 'open(' in code and try_count == 0:
                issues.append(Issue(
                    severity=IssueSeverity.MEDIUM,
                    category="error_handling",
                    message="File operations without error handling",
                    suggestion="Add try-except blocks for file operations"
                ))
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{2,}\b', code)
        if len(magic_numbers) > 3:
            issues.append(Issue(
                severity=IssueSeverity.LOW,
                category="maintainability",
                message="Magic numbers detected",
                suggestion="Define constants for magic numbers"
            ))
        
        # Check for commented out code
        if re.search(r'^\s*#.*\(.*\)', code, re.MULTILINE):
            issues.append(Issue(
                severity=IssueSeverity.LOW,
                category="cleanliness",
                message="Commented out code detected",
                suggestion="Remove commented out code"
            ))
        
        return issues
    
    def _check_performance(self, code: str, language: str) -> List[Issue]:
        """Check for performance issues"""
        issues = []
        
        if language == 'python':
            # Check for inefficient loops
            if 'for' in code and 'append' in code:
                # Simple heuristic for list comprehension opportunity
                for_append = re.findall(r'for.*:\s*\n\s*.*\.append\(', code)
                if for_append:
                    issues.append(Issue(
                        severity=IssueSeverity.LOW,
                        category="performance",
                        message="Loop with append could be list comprehension",
                        suggestion="Consider using list comprehension for better performance"
                    ))
            
            # Check for repeated compilations
            if 're.search' in code or 're.match' in code:
                if not 're.compile' in code:
                    issues.append(Issue(
                        severity=IssueSeverity.LOW,
                        category="performance",
                        message="Regex patterns not pre-compiled",
                        suggestion="Pre-compile regex patterns for better performance"
                    ))
        
        # Check for nested loops (O(n²) complexity)
        nested_loops = re.findall(r'for.*:\s*\n\s*for.*:', code)
        if nested_loops:
            issues.append(Issue(
                severity=IssueSeverity.MEDIUM,
                category="performance",
                message="Nested loops detected (potential O(n²) complexity)",
                suggestion="Consider optimizing nested loops"
            ))
        
        return issues
    
    def _check_security(self, code: str, language: str) -> List[Issue]:
        """Check for security vulnerabilities"""
        issues = []
        
        # Check for SQL injection risks
        if 'sql' in code.lower() or 'query' in code.lower():
            if 'format(' in code or '%s' in code or 'f"' in code:
                issues.append(Issue(
                    severity=IssueSeverity.HIGH,
                    category="security",
                    message="Potential SQL injection vulnerability",
                    suggestion="Use parameterized queries"
                ))
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][\w]+["\']',
            r'password\s*=\s*["\'][\w]+["\']',
            r'secret\s*=\s*["\'][\w]+["\']',
            r'token\s*=\s*["\'][\w]+["\']'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(Issue(
                    severity=IssueSeverity.CRITICAL,
                    category="security",
                    message="Hardcoded secrets detected",
                    suggestion="Use environment variables or secure vaults for secrets"
                ))
                break
        
        # Check for unsafe operations
        if language == 'python':
            if 'eval(' in code or 'exec(' in code:
                issues.append(Issue(
                    severity=IssueSeverity.HIGH,
                    category="security",
                    message="Use of eval/exec is dangerous",
                    suggestion="Avoid eval/exec, use safer alternatives"
                ))
        
        return issues
    
    def _check_documentation(self, code: str, language: str) -> List[Issue]:
        """Check documentation quality"""
        issues = []
        
        if language == 'python':
            # Check for missing docstrings
            functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
            docstrings = re.findall(r'def\s+\w+\s*\([^)]*\):\s*\n\s*"""', code)
            
            if functions and len(docstrings) < len(functions) * 0.5:
                issues.append(Issue(
                    severity=IssueSeverity.MEDIUM,
                    category="documentation",
                    message="Many functions lack docstrings",
                    suggestion="Add docstrings to document function purpose and parameters"
                ))
        
        # Check for inline comments
        comment_lines = len(re.findall(r'^\s*#', code, re.MULTILINE))
        total_lines = len(code.split('\n'))
        
        if total_lines > 50 and comment_lines < total_lines * 0.05:
            issues.append(Issue(
                severity=IssueSeverity.LOW,
                category="documentation",
                message="Insufficient inline comments",
                suggestion="Add comments to explain complex logic"
            ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _score_from_issues(self, issues: List[Issue]) -> float:
        """Calculate score based on issues found"""
        if not issues:
            return 1.0
        
        # Weight by severity
        weights = {
            IssueSeverity.CRITICAL: 10,
            IssueSeverity.HIGH: 5,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 1,
            IssueSeverity.INFO: 0.5
        }
        
        total_weight = sum(weights.get(issue.severity, 1) for issue in issues)
        
        # Score decreases with more/severe issues
        score = max(0, 1.0 - (total_weight * 0.05))
        
        return score
    
    def _calculate_overall_score(self, result: ReviewResult) -> float:
        """Calculate overall review score"""
        
        # Weight different aspects
        weights = {
            'code_quality': 0.25,
            'architecture': 0.15,
            'best_practices': 0.20,
            'performance': 0.15,
            'security': 0.20,
            'documentation': 0.05
        }
        
        scores = {
            'code_quality': result.code_quality_score,
            'architecture': result.architecture_score,
            'best_practices': result.best_practices_score,
            'performance': result.performance_score,
            'security': result.security_score,
            'documentation': result.documentation_score
        }
        
        weighted_score = sum(
            scores.get(aspect, 0) * weight
            for aspect, weight in weights.items()
        )
        
        return weighted_score
    
    def _generate_suggestions(self, result: ReviewResult) -> List[str]:
        """Generate improvement suggestions based on review"""
        
        suggestions = []
        
        # Priority suggestions based on lowest scores
        if result.security_score < 0.7:
            suggestions.append("Priority: Address security vulnerabilities immediately")
        
        if result.code_quality_score < 0.6:
            suggestions.append("Refactor code to improve readability and maintainability")
        
        if result.performance_score < 0.6:
            suggestions.append("Optimize performance bottlenecks")
        
        if result.documentation_score < 0.5:
            suggestions.append("Add comprehensive documentation")
        
        # Specific suggestions based on issues
        issue_categories = {}
        for issue in result.issues:
            if issue.category not in issue_categories:
                issue_categories[issue.category] = 0
            issue_categories[issue.category] += 1
        
        for category, count in sorted(issue_categories.items(), key=lambda x: x[1], reverse=True)[:3]:
            suggestions.append(f"Focus on fixing {category} issues ({count} found)")
        
        return suggestions
    
    def _calculate_code_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate various code metrics"""
        
        lines = code.split('\n')
        
        metrics = {
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'average_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0
        }
        
        if language == 'python':
            try:
                tree = ast.parse(code)
                metrics['functions'] = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                metrics['classes'] = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            except:
                pass
        
        return metrics
    
    async def _review_documentation(self, content: str) -> ReviewResult:
        """Review documentation quality"""
        
        result = ReviewResult()
        
        # Check for completeness
        if len(content) < 100:
            result.issues.append(Issue(
                severity=IssueSeverity.MEDIUM,
                category="completeness",
                message="Documentation seems too brief",
                suggestion="Add more detailed explanations"
            ))
        
        # Check for structure
        if not any(marker in content for marker in ['#', '##', '###']):
            result.issues.append(Issue(
                severity=IssueSeverity.LOW,
                category="structure",
                message="Documentation lacks structure",
                suggestion="Use headers to organize content"
            ))
        
        result.documentation_score = self._score_from_issues(result.issues)
        
        return result
    
    async def _review_configuration(self, content: str) -> ReviewResult:
        """Review configuration files"""
        
        result = ReviewResult()
        
        # Check for hardcoded values
        if any(pattern in content for pattern in ['localhost', '127.0.0.1', 'password']):
            result.issues.append(Issue(
                severity=IssueSeverity.MEDIUM,
                category="configuration",
                message="Hardcoded values in configuration",
                suggestion="Use environment variables for environment-specific values"
            ))
        
        result.best_practices_score = self._score_from_issues(result.issues)
        
        return result