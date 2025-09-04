"""
Enhanced Quality Gate Manager
Orchestrates comprehensive security validation, compliance checking, and code analysis
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .compliance_checker import ComplianceChecker, ComplianceResult, ComplianceStandard
from .code_security_analyzer import CodeSecurityAnalyzer, CodeSecurityResult
from .security_validator import SecurityValidator, SecurityResult

logger = logging.getLogger(__name__)


class QualityGateStatus(Enum):
    """Quality gate validation status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class QualityGateType(Enum):
    """Types of quality gates"""
    SECURITY_SCAN = "security_scan"
    COMPLIANCE_CHECK = "compliance_check"
    CODE_ANALYSIS = "code_analysis"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    COMBINED_SECURITY = "combined_security"


@dataclass
class QualityGateResult:
    """Individual quality gate result"""
    gate_type: QualityGateType
    status: QualityGateStatus
    score: float  # 0-100
    title: str
    description: str
    execution_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[Any] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedQualityGateReport:
    """Comprehensive quality gate validation report"""
    scan_id: str
    timestamp: float
    target_path: str
    overall_status: QualityGateStatus
    overall_score: float  # 0-100
    gate_results: List[QualityGateResult] = field(default_factory=list)
    total_execution_time: float = 0.0
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed_gates(self) -> int:
        """Number of gates that passed"""
        return sum(1 for gate in self.gate_results if gate.status == QualityGateStatus.PASSED)
    
    @property
    def failed_gates(self) -> int:
        """Number of gates that failed"""
        return sum(1 for gate in self.gate_results if gate.status == QualityGateStatus.FAILED)
    
    @property
    def total_gates(self) -> int:
        """Total number of gates executed"""
        return len(self.gate_results)
    
    def get_gate_result(self, gate_type: QualityGateType) -> Optional[QualityGateResult]:
        """Get result for specific gate type"""
        for gate in self.gate_results:
            if gate.gate_type == gate_type:
                return gate
        return None


class EnhancedQualityGateManager:
    """Comprehensive quality gate manager with security focus"""
    
    def __init__(self, 
                 enable_security_scan: bool = True,
                 enable_compliance_check: bool = True,
                 enable_code_analysis: bool = True,
                 compliance_standards: List[ComplianceStandard] = None,
                 pass_threshold: float = 80.0,
                 warning_threshold: float = 60.0):
        
        self.enable_security_scan = enable_security_scan
        self.enable_compliance_check = enable_compliance_check
        self.enable_code_analysis = enable_code_analysis
        
        self.pass_threshold = pass_threshold
        self.warning_threshold = warning_threshold
        
        # Initialize validators
        if enable_security_scan:
            self.security_validator = SecurityValidator(
                enable_static_analysis=True,
                enable_dependency_scan=True,
                enable_secrets_scan=True,
                enable_pattern_matching=True
            )
        
        if enable_compliance_check:
            self.compliance_checker = ComplianceChecker(
                standards=compliance_standards or [
                    ComplianceStandard.GDPR,
                    ComplianceStandard.OWASP,
                    ComplianceStandard.NIST
                ]
            )
        
        if enable_code_analysis:
            self.code_analyzer = CodeSecurityAnalyzer(
                languages=['python', 'javascript', 'typescript', 'java']
            )
        
        logger.info("EnhancedQualityGateManager initialized with %d validators",
                   sum([enable_security_scan, enable_compliance_check, enable_code_analysis]))
    
    async def validate_all(self, target_path: Union[str, Path], 
                          parallel_execution: bool = True) -> EnhancedQualityGateReport:
        """Run all enabled quality gates on the target"""
        path = Path(target_path)
        if not path.exists():
            raise ValueError(f"Target path does not exist: {path}")
        
        scan_id = self._generate_scan_id(str(path))
        start_time = time.time()
        
        logger.info("Starting enhanced quality gate validation for: %s", path)
        
        gate_results = []
        
        if parallel_execution:
            # Run all gates in parallel
            tasks = []
            
            if self.enable_security_scan:
                tasks.append(self._run_security_scan_gate(path))
            
            if self.enable_compliance_check:
                tasks.append(self._run_compliance_check_gate(path))
            
            if self.enable_code_analysis:
                tasks.append(self._run_code_analysis_gate(path))
            
            if tasks:
                gate_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle exceptions
                valid_results = []
                for result in gate_results:
                    if isinstance(result, Exception):
                        logger.error("Gate execution failed: %s", result)
                        error_result = QualityGateResult(
                            gate_type=QualityGateType.COMBINED_SECURITY,
                            status=QualityGateStatus.ERROR,
                            score=0.0,
                            title="Gate Execution Error",
                            description=str(result),
                            metadata={'error': str(result)}
                        )
                        valid_results.append(error_result)
                    else:
                        valid_results.append(result)
                
                gate_results = valid_results
        
        else:
            # Run gates sequentially
            if self.enable_security_scan:
                result = await self._run_security_scan_gate(path)
                gate_results.append(result)
            
            if self.enable_compliance_check:
                result = await self._run_compliance_check_gate(path)
                gate_results.append(result)
            
            if self.enable_code_analysis:
                result = await self._run_code_analysis_gate(path)
                gate_results.append(result)
        
        # Calculate overall results
        end_time = time.time()
        total_execution_time = end_time - start_time
        
        overall_score, overall_status = self._calculate_overall_results(gate_results)
        summary = self._generate_summary(gate_results)
        recommendations = self._generate_recommendations(gate_results)
        
        report = EnhancedQualityGateReport(
            scan_id=scan_id,
            timestamp=end_time,
            target_path=str(path),
            overall_status=overall_status,
            overall_score=overall_score,
            gate_results=gate_results,
            total_execution_time=total_execution_time,
            summary=summary,
            recommendations=recommendations,
            metadata={
                'gates_enabled': {
                    'security_scan': self.enable_security_scan,
                    'compliance_check': self.enable_compliance_check,
                    'code_analysis': self.enable_code_analysis
                },
                'thresholds': {
                    'pass': self.pass_threshold,
                    'warning': self.warning_threshold
                }
            }
        )
        
        logger.info("Enhanced quality gate validation completed. Overall status: %s, Score: %.1f",
                   overall_status.value, overall_score)
        
        return report
    
    async def validate_security_only(self, target_path: Union[str, Path]) -> EnhancedQualityGateReport:
        """Run only security-focused gates"""
        if not self.enable_security_scan:
            raise ValueError("Security scan not enabled")
        
        path = Path(target_path)
        result = await self._run_security_scan_gate(path)
        
        overall_status = result.status
        overall_score = result.score
        
        return EnhancedQualityGateReport(
            scan_id=self._generate_scan_id(str(path)),
            timestamp=time.time(),
            target_path=str(path),
            overall_status=overall_status,
            overall_score=overall_score,
            gate_results=[result],
            total_execution_time=result.execution_time,
            summary={'security_focused': True},
            recommendations=result.recommendations
        )
    
    async def _run_security_scan_gate(self, path: Path) -> QualityGateResult:
        """Run comprehensive security scan gate"""
        start_time = time.time()
        
        try:
            if path.is_dir():
                security_result = await self.security_validator.validate_directory(path)
            else:
                security_result = await self.security_validator.validate_file(path)
            
            # Convert security score (lower is better for vulnerabilities) to quality score
            security_score = max(0.0, 100.0 - security_result.risk_score)
            
            # Determine status based on security findings
            if security_result.is_secure and security_score >= self.pass_threshold:
                status = QualityGateStatus.PASSED
            elif security_score >= self.warning_threshold:
                status = QualityGateStatus.WARNING
            else:
                status = QualityGateStatus.FAILED
            
            recommendations = []
            if not security_result.is_secure:
                recommendations.append("Address critical and high severity vulnerabilities immediately")
                recommendations.append("Review and fix hardcoded credentials")
                recommendations.append("Update vulnerable dependencies")
            
            execution_time = time.time() - start_time
            
            return QualityGateResult(
                gate_type=QualityGateType.SECURITY_SCAN,
                status=status,
                score=security_score,
                title="Security Vulnerability Scan",
                description=f"Found {security_result.total_vulnerabilities} vulnerabilities",
                execution_time=execution_time,
                details={
                    'total_vulnerabilities': security_result.total_vulnerabilities,
                    'vulnerabilities_by_severity': security_result.vulnerabilities_by_severity,
                    'risk_score': security_result.risk_score,
                    'is_secure': security_result.is_secure
                },
                issues=[vuln.__dict__ for vuln in security_result.vulnerabilities],
                recommendations=recommendations,
                metadata={'security_result': security_result.__dict__}
            )
        
        except Exception as e:
            logger.error("Security scan gate failed: %s", e)
            return QualityGateResult(
                gate_type=QualityGateType.SECURITY_SCAN,
                status=QualityGateStatus.ERROR,
                score=0.0,
                title="Security Scan Error",
                description=str(e),
                execution_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def _run_compliance_check_gate(self, path: Path) -> QualityGateResult:
        """Run compliance check gate"""
        start_time = time.time()
        
        try:
            if path.is_dir():
                compliance_result = await self.compliance_checker.check_directory(path)
            else:
                compliance_result = await self.compliance_checker.check_file(path)
            
            compliance_score = compliance_result.compliance_score
            
            # Determine status based on compliance score
            if compliance_result.is_compliant and compliance_score >= self.pass_threshold:
                status = QualityGateStatus.PASSED
            elif compliance_score >= self.warning_threshold:
                status = QualityGateStatus.WARNING
            else:
                status = QualityGateStatus.FAILED
            
            recommendations = []
            if not compliance_result.is_compliant:
                recommendations.append("Address critical and high priority compliance issues")
                recommendations.append("Review data handling procedures for GDPR compliance")
                recommendations.append("Implement proper audit logging (NIST/SOX)")
            
            execution_time = time.time() - start_time
            
            return QualityGateResult(
                gate_type=QualityGateType.COMPLIANCE_CHECK,
                status=status,
                score=compliance_score,
                title="Compliance Validation",
                description=f"Found {compliance_result.total_issues} compliance issues",
                execution_time=execution_time,
                details={
                    'total_issues': compliance_result.total_issues,
                    'issues_by_severity': compliance_result.issues_by_severity,
                    'issues_by_standard': compliance_result.issues_by_standard,
                    'is_compliant': compliance_result.is_compliant
                },
                issues=[issue.__dict__ for issue in compliance_result.issues],
                recommendations=recommendations,
                metadata={'compliance_result': compliance_result.__dict__}
            )
        
        except Exception as e:
            logger.error("Compliance check gate failed: %s", e)
            return QualityGateResult(
                gate_type=QualityGateType.COMPLIANCE_CHECK,
                status=QualityGateStatus.ERROR,
                score=0.0,
                title="Compliance Check Error",
                description=str(e),
                execution_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def _run_code_analysis_gate(self, path: Path) -> QualityGateResult:
        """Run code security analysis gate"""
        start_time = time.time()
        
        try:
            if path.is_dir():
                analysis_result = await self.code_analyzer.analyze_directory(path)
            else:
                analysis_result = await self.code_analyzer.analyze_file(path)
            
            security_score = analysis_result.security_score
            
            # Determine status based on security issues
            if not analysis_result.has_critical_issues and security_score >= self.pass_threshold:
                status = QualityGateStatus.PASSED
            elif security_score >= self.warning_threshold:
                status = QualityGateStatus.WARNING
            else:
                status = QualityGateStatus.FAILED
            
            recommendations = []
            if analysis_result.has_critical_issues:
                recommendations.append("Fix critical security issues immediately")
            if analysis_result.issues_by_severity.get('high', 0) > 0:
                recommendations.append("Address high priority security vulnerabilities")
            recommendations.append("Review code for injection vulnerabilities")
            recommendations.append("Implement proper input validation")
            
            execution_time = time.time() - start_time
            
            return QualityGateResult(
                gate_type=QualityGateType.CODE_ANALYSIS,
                status=status,
                score=security_score,
                title="Code Security Analysis",
                description=f"Found {analysis_result.total_issues} security issues in code",
                execution_time=execution_time,
                details={
                    'total_issues': analysis_result.total_issues,
                    'issues_by_severity': analysis_result.issues_by_severity,
                    'issues_by_type': analysis_result.issues_by_type,
                    'has_critical_issues': analysis_result.has_critical_issues
                },
                issues=[issue.__dict__ for issue in analysis_result.issues],
                recommendations=recommendations,
                metadata={'analysis_result': analysis_result.__dict__}
            )
        
        except Exception as e:
            logger.error("Code analysis gate failed: %s", e)
            return QualityGateResult(
                gate_type=QualityGateType.CODE_ANALYSIS,
                status=QualityGateStatus.ERROR,
                score=0.0,
                title="Code Analysis Error",
                description=str(e),
                execution_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def _calculate_overall_results(self, gate_results: List[QualityGateResult]) -> tuple[float, QualityGateStatus]:
        """Calculate overall score and status from individual gate results"""
        if not gate_results:
            return 0.0, QualityGateStatus.ERROR
        
        # Calculate weighted average score
        total_score = sum(result.score for result in gate_results)
        overall_score = total_score / len(gate_results)
        
        # Determine overall status
        failed_count = sum(1 for result in gate_results if result.status == QualityGateStatus.FAILED)
        error_count = sum(1 for result in gate_results if result.status == QualityGateStatus.ERROR)
        warning_count = sum(1 for result in gate_results if result.status == QualityGateStatus.WARNING)
        
        if error_count > 0:
            overall_status = QualityGateStatus.ERROR
        elif failed_count > 0:
            overall_status = QualityGateStatus.FAILED
        elif warning_count > 0:
            overall_status = QualityGateStatus.WARNING
        else:
            overall_status = QualityGateStatus.PASSED
        
        return round(overall_score, 2), overall_status
    
    def _generate_summary(self, gate_results: List[QualityGateResult]) -> Dict[str, Any]:
        """Generate summary statistics from gate results"""
        summary = {
            'total_gates': len(gate_results),
            'passed_gates': sum(1 for r in gate_results if r.status == QualityGateStatus.PASSED),
            'failed_gates': sum(1 for r in gate_results if r.status == QualityGateStatus.FAILED),
            'warning_gates': sum(1 for r in gate_results if r.status == QualityGateStatus.WARNING),
            'error_gates': sum(1 for r in gate_results if r.status == QualityGateStatus.ERROR),
            'average_score': round(sum(r.score for r in gate_results) / len(gate_results), 2) if gate_results else 0,
            'total_execution_time': round(sum(r.execution_time for r in gate_results), 2)
        }
        
        # Add gate-specific summaries
        for result in gate_results:
            gate_key = f"{result.gate_type.value}_summary"
            summary[gate_key] = {
                'status': result.status.value,
                'score': result.score,
                'issues_count': len(result.issues)
            }
        
        return summary
    
    def _generate_recommendations(self, gate_results: List[QualityGateResult]) -> List[str]:
        """Generate prioritized recommendations from all gate results"""
        all_recommendations = []
        
        # Collect all recommendations with priority
        for result in gate_results:
            if result.status in [QualityGateStatus.FAILED, QualityGateStatus.WARNING]:
                all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        # Add general recommendations
        if any(r.status == QualityGateStatus.FAILED for r in gate_results):
            unique_recommendations.insert(0, "⚠️  Critical issues found - address immediately before deployment")
        
        return unique_recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_scan_id(self, input_string: str) -> str:
        """Generate unique scan ID"""
        import hashlib
        return hashlib.sha256(f"{input_string}_{time.time()}".encode()).hexdigest()[:16]
    
    async def export_report(self, report: EnhancedQualityGateReport, 
                          output_path: Union[str, Path], format: str = 'json') -> None:
        """Export quality gate report to file"""
        output_file = Path(output_path)
        
        if format.lower() == 'json':
            report_data = {
                'scan_id': report.scan_id,
                'timestamp': report.timestamp,
                'target_path': report.target_path,
                'overall_status': report.overall_status.value,
                'overall_score': report.overall_score,
                'summary': report.summary,
                'recommendations': report.recommendations,
                'gate_results': [
                    {
                        'gate_type': result.gate_type.value,
                        'status': result.status.value,
                        'score': result.score,
                        'title': result.title,
                        'description': result.description,
                        'execution_time': result.execution_time,
                        'issues_count': len(result.issues),
                        'recommendations': result.recommendations
                    }
                    for result in report.gate_results
                ],
                'metadata': report.metadata
            }
            
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
        
        elif format.lower() == 'markdown':
            markdown_content = self._generate_markdown_report(report)
            with open(output_file, 'w') as f:
                f.write(markdown_content)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info("Quality gate report exported to: %s", output_file)
    
    def _generate_markdown_report(self, report: EnhancedQualityGateReport) -> str:
        """Generate markdown format report"""
        md = f"""# Enhanced Quality Gate Report

## Overview
- **Scan ID**: `{report.scan_id}`
- **Target**: `{report.target_path}`
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}
- **Overall Status**: **{report.overall_status.value.upper()}**
- **Overall Score**: **{report.overall_score:.1f}/100**
- **Total Execution Time**: {report.total_execution_time:.2f}s

## Summary
- Total Gates: {report.total_gates}
- Passed: {report.passed_gates}
- Failed: {report.failed_gates}
- Warnings: {report.summary.get('warning_gates', 0)}

## Gate Results

"""
        
        for result in report.gate_results:
            status_emoji = {
                'passed': '✅',
                'failed': '❌', 
                'warning': '⚠️',
                'error': '🚫',
                'skipped': '⏭️'
            }
            
            md += f"""### {result.title} {status_emoji.get(result.status.value, '❓')}

- **Status**: {result.status.value.upper()}
- **Score**: {result.score:.1f}/100
- **Execution Time**: {result.execution_time:.2f}s
- **Issues Found**: {len(result.issues)}

{result.description}

"""
            if result.recommendations:
                md += "**Recommendations:**\n"
                for rec in result.recommendations:
                    md += f"- {rec}\n"
                md += "\n"
        
        if report.recommendations:
            md += "## Overall Recommendations\n\n"
            for i, rec in enumerate(report.recommendations, 1):
                md += f"{i}. {rec}\n"
        
        return md


# Convenience function for comprehensive quality validation
async def validate_comprehensive_quality(target_path: Union[str, Path],
                                       parallel_execution: bool = True,
                                       export_format: Optional[str] = None,
                                       export_path: Optional[Union[str, Path]] = None) -> EnhancedQualityGateReport:
    """Perform comprehensive quality gate validation"""
    manager = EnhancedQualityGateManager()
    report = await manager.validate_all(target_path, parallel_execution=parallel_execution)
    
    if export_format and export_path:
        await manager.export_report(report, export_path, export_format)
    
    return report