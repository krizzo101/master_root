"""
Module: rule_generator_engine

Implements RuleGeneratorEngine for generating coding rules based on pattern analysis.
Uses O3ModelGenerator to enhance rules and applies project-specific conventions.
Provides methods to generate, enhance, resolve conflicts, and prioritize rules.

This module follows the O3 Code Generator project rules:
- Absolute imports from project root
- O3Logger used for logging via get_logger()
- All classes initialize logger in __init__ and document attributes
"""

from dataclasses import dataclass

from src.tools.code_generation.o3_code_generator.auto_rules_generation.pattern_extractor import (
    PatternAnalysis,
    PatternGroup,
    ViolationReport,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)


@dataclass
class GeneratedRule:
    """A generated rule with metadata.

    Attributes:
        rule_name: Unique name of the rule.
        rule_type: Severity of the rule ('critical', 'important', 'optional').
        rule_text: The text describing the rule.
        confidence_score: Confidence score between 0.0 and 1.0.
        pattern_basis: Pattern signature that formed the basis of the rule.
        examples: Example code snippets or descriptions.
        rationale: Explanation of why the rule is needed.
    """

    rule_name: str
    rule_type: str
    rule_text: str
    confidence_score: float
    pattern_basis: str
    examples: list[str]
    rationale: str


@dataclass
class RuleGenerationResult:
    """Result of rule generation process.

    Attributes:
        generated_rules: List of generated and enhanced rules.
        rule_hierarchy: Mapping from rule_type to list of rules.
        conflict_resolutions: Messages describing resolved conflicts.
        confidence_scores: Mapping from rule_name to adjusted confidence.
        recommendations: Suggested next steps for implementation.
    """

    generated_rules: list[GeneratedRule]
    rule_hierarchy: dict[str, list[GeneratedRule]]
    conflict_resolutions: list[str]
    confidence_scores: dict[str, float]
    recommendations: list[str]


class RuleGeneratorEngine:
    """
    Uses O3ModelGenerator to generate intelligent rules based on pattern analysis.

    Analyzes pattern data, generates rule candidates, enhances them via O3 model,
    resolves conflicts, organizes hierarchy, and produces implementation recommendations.

    Attributes:
        logger: O3Logger instance for logging.
        model_generator: O3ModelGenerator instance for interfacing with the O3 model.
        rule_templates: Templates for rule text generation by pattern type and severity.
    """

    def __init__(self, model_name: str = "o4-mini") -> None:
        """Initialize the rule generator engine."""
        self.logger = get_logger()
        self.model_generator = O3ModelGenerator(model=model_name)
        self.rule_templates = {
            "import": {
                "critical": "All imports must use {pattern} pattern. {rationale}",
                "important": "Prefer {pattern} import pattern. {rationale}",
                "optional": "Consider using {pattern} import pattern. {rationale}",
            },
            "class": {
                "critical": "All classes must follow {pattern} pattern. {rationale}",
                "important": "Classes should follow {pattern} pattern. {rationale}",
                "optional": "Consider following {pattern} pattern for classes. {rationale}",
            },
            "method": {
                "critical": "All methods must follow {pattern} pattern. {rationale}",
                "important": "Methods should follow {pattern} pattern. {rationale}",
                "optional": "Consider following {pattern} pattern for methods. {rationale}",
            },
            "error_handling": {
                "critical": "Error handling must follow {pattern} pattern. {rationale}",
                "important": "Error handling should follow {pattern} pattern. {rationale}",
                "optional": "Consider following {pattern} pattern for error handling. {rationale}",
            },
            "logging": {
                "critical": "Logging must follow {pattern} pattern. {rationale}",
                "important": "Logging should follow {pattern} pattern. {rationale}",
                "optional": "Consider following {pattern} pattern for logging. {rationale}",
            },
        }
        self.logger.log_info(
            f"Initialized RuleGeneratorEngine with model: {model_name}"
        )

    def generate_rules(self, pattern_analysis: PatternAnalysis) -> RuleGenerationResult:
        """
        Generate rules based on pattern analysis.

        Args:
            pattern_analysis: Complete pattern analysis of the codebase.

        Returns:
            RuleGenerationResult: Generated rules and metadata.
        """
        self.logger.log_info("Starting rule generation process")
        candidates = self._generate_rule_candidates(pattern_analysis)
        enhanced = self._enhance_rules_with_o3(candidates, pattern_analysis)
        conflicts = self._resolve_rule_conflicts(enhanced)
        hierarchy = self._create_rule_hierarchy(enhanced)
        scores = self._calculate_confidence_scores(enhanced, pattern_analysis)
        recommendations = self._generate_rule_recommendations(
            enhanced, pattern_analysis
        )
        self.logger.log_info(f"Generated {len(enhanced)} rules")
        return RuleGenerationResult(
            generated_rules=enhanced,
            rule_hierarchy=hierarchy,
            conflict_resolutions=conflicts,
            confidence_scores=scores,
            recommendations=recommendations,
        )

    def _generate_rule_candidates(
        self, pattern_analysis: PatternAnalysis
    ) -> list[GeneratedRule]:
        """Generate initial rule candidates from pattern analysis."""
        candidates: list[GeneratedRule] = []
        candidates.extend(self._generate_import_rules(pattern_analysis.import_patterns))
        candidates.extend(self._generate_class_rules(pattern_analysis.class_patterns))
        candidates.extend(self._generate_method_rules(pattern_analysis.method_patterns))
        candidates.extend(
            self._generate_error_handling_rules(
                pattern_analysis.error_handling_patterns
            )
        )
        candidates.extend(
            self._generate_logging_rules(pattern_analysis.logging_patterns)
        )
        candidates.extend(self._generate_violation_rules(pattern_analysis.violations))
        return candidates

    def _generate_import_rules(
        self, import_patterns: dict[str, PatternGroup]
    ) -> list[GeneratedRule]:
        """Generate rules from import patterns."""
        rules: list[GeneratedRule] = []
        for signature, group in import_patterns.items():
            if group.frequency < 5:
                continue
            if group.frequency > 20 and group.consistency_score > 0.9:
                rule_type = "critical"
            elif group.frequency > 10 and group.consistency_score > 0.7:
                rule_type = "important"
            else:
                rule_type = "optional"
            if "relative:" in signature:
                continue
            pattern_desc = signature.split(":", 1)[1] if ":" in signature else signature
            text = self.rule_templates["import"][rule_type].format(
                pattern=pattern_desc,
                rationale="This pattern is used consistently across the codebase.",
            )
            examples = [f"import {p.module_name}" for p in group.examples[:3]]
            rules.append(
                GeneratedRule(
                    rule_name=f"import_pattern_{signature.replace(':', '_')}",
                    rule_type=rule_type,
                    rule_text=text,
                    confidence_score=group.consistency_score,
                    pattern_basis=signature,
                    examples=examples,
                    rationale="Based on consistent import patterns found in the codebase.",
                )
            )
        return rules

    def _generate_class_rules(
        self, class_patterns: dict[str, PatternGroup]
    ) -> list[GeneratedRule]:
        """Generate rules from class patterns."""
        rules: list[GeneratedRule] = []
        for signature, group in class_patterns.items():
            if group.frequency < 3:
                continue
            if group.frequency > 15 and group.consistency_score > 0.9:
                rule_type = "critical"
            elif group.frequency > 8 and group.consistency_score > 0.7:
                rule_type = "important"
            else:
                rule_type = "optional"
            parts = signature.split(":")
            if len(parts) >= 4:
                has_doc = parts[1] == "True"
                has_init = parts[2] == "True"
                method_count = int(parts[3])
                if has_doc and has_init:
                    desc = "classes with docstrings and __init__ methods"
                    rationale = "Classes with proper documentation and initialization are more maintainable."
                elif has_doc:
                    desc = "classes with docstrings"
                    rationale = "Documented classes improve code readability and maintainability."
                else:
                    desc = f"classes with {method_count} methods"
                    rationale = "Consistent class structure improves code organization."
                text = self.rule_templates["class"][rule_type].format(
                    pattern=desc, rationale=rationale
                )
                examples = [f"class {p.class_name}" for p in group.examples[:3]]
                rules.append(
                    GeneratedRule(
                        rule_name=f"class_pattern_{signature.replace(':', '_')}",
                        rule_type=rule_type,
                        rule_text=text,
                        confidence_score=group.consistency_score,
                        pattern_basis=signature,
                        examples=examples,
                        rationale=rationale,
                    )
                )
        return rules

    def _generate_method_rules(
        self, method_patterns: dict[str, PatternGroup]
    ) -> list[GeneratedRule]:
        """Generate rules from method patterns."""
        rules: list[GeneratedRule] = []
        for signature, group in method_patterns.items():
            if group.frequency < 5:
                continue
            if group.frequency > 20 and group.consistency_score > 0.9:
                rule_type = "critical"
            elif group.frequency > 10 and group.consistency_score > 0.7:
                rule_type = "important"
            else:
                rule_type = "optional"
            parts = signature.split(":")
            if len(parts) >= 4:
                is_static = parts[1] == "True"
                has_doc = parts[2] == "True"
                param_count = int(parts[3])
                if has_doc:
                    desc = "methods with docstrings"
                    rationale = "Documented methods improve code readability and maintainability."
                elif is_static:
                    desc = "static methods"
                    rationale = "Static methods should be used when appropriate for utility functions."
                else:
                    desc = f"methods with {param_count} parameters"
                    rationale = (
                        "Consistent method signatures improve code organization."
                    )
                text = self.rule_templates["method"][rule_type].format(
                    pattern=desc, rationale=rationale
                )
                examples = [f"def {p.method_name}" for p in group.examples[:3]]
                rules.append(
                    GeneratedRule(
                        rule_name=f"method_pattern_{signature.replace(':', '_')}",
                        rule_type=rule_type,
                        rule_text=text,
                        confidence_score=group.consistency_score,
                        pattern_basis=signature,
                        examples=examples,
                        rationale=rationale,
                    )
                )
        return rules

    def _generate_error_handling_rules(
        self, error_patterns: dict[str, PatternGroup]
    ) -> list[GeneratedRule]:
        """Generate rules from error handling patterns."""
        rules: list[GeneratedRule] = []
        for signature, group in error_patterns.items():
            if group.frequency < 3:
                continue
            if group.frequency > 10 and group.consistency_score > 0.9:
                rule_type = "critical"
            elif group.frequency > 5 and group.consistency_score > 0.7:
                rule_type = "important"
            else:
                rule_type = "optional"
            parts = signature.split(":")
            if len(parts) >= 3:
                ptype = parts[1]
                has_log = parts[2] == "True"
                if ptype == "specific_except" and has_log:
                    desc = "specific exception handling with logging"
                    rationale = "Specific exception handling with proper logging improves debugging."
                elif ptype == "specific_except":
                    desc = "specific exception handling"
                    rationale = "Specific exception handling is preferred over bare except statements."
                else:
                    desc = "error handling with logging"
                    rationale = (
                        "Error handling should include proper logging for debugging."
                    )
                text = self.rule_templates["error_handling"][rule_type].format(
                    pattern=desc, rationale=rationale
                )
                examples = [
                    f"try/except at line {p.line_number}" for p in group.examples[:3]
                ]
                rules.append(
                    GeneratedRule(
                        rule_name=f"error_handling_pattern_{signature.replace(':', '_')}",
                        rule_type=rule_type,
                        rule_text=text,
                        confidence_score=group.consistency_score,
                        pattern_basis=signature,
                        examples=examples,
                        rationale=rationale,
                    )
                )
        return rules

    def _generate_logging_rules(
        self, logging_patterns: dict[str, PatternGroup]
    ) -> list[GeneratedRule]:
        """Generate rules from logging patterns."""
        rules: list[GeneratedRule] = []
        for signature, group in logging_patterns.items():
            if group.frequency < 5:
                continue
            if group.frequency > 15 and group.consistency_score > 0.9:
                rule_type = "critical"
            elif group.frequency > 8 and group.consistency_score > 0.7:
                rule_type = "important"
            else:
                rule_type = "optional"
            parts = signature.split(":")
            if len(parts) >= 3:
                ltype = parts[1]
                level = parts[2]
                if ltype == "print":
                    continue
                if ltype == "O3Logger":
                    desc = f"O3Logger with {level} level"
                    rationale = (
                        "O3Logger provides consistent logging across the application."
                    )
                else:
                    desc = f"logging with {level} level"
                    rationale = (
                        "Consistent logging levels improve debugging and monitoring."
                    )
                text = self.rule_templates["logging"][rule_type].format(
                    pattern=desc, rationale=rationale
                )
                examples = [p.method_name for p in group.examples[:3]]
                rules.append(
                    GeneratedRule(
                        rule_name=f"logging_pattern_{signature.replace(':', '_')}",
                        rule_type=rule_type,
                        rule_text=text,
                        confidence_score=group.consistency_score,
                        pattern_basis=signature,
                        examples=examples,
                        rationale=rationale,
                    )
                )
        return rules

    def _generate_violation_rules(
        self, violations: list[ViolationReport]
    ) -> list[GeneratedRule]:
        """Generate rules from violation patterns."""
        groups: dict[str, list[ViolationReport]] = {}
        for v in violations:
            groups.setdefault(v.rule_name, []).append(v)
        rules: list[GeneratedRule] = []
        for name, vs in groups.items():
            if len(vs) < 3:
                continue
            severities = [v.severity for v in vs]
            if "critical" in severities:
                rule_type = "critical"
            elif "important" in severities:
                rule_type = "important"
            else:
                rule_type = "optional"
            text = f"Enforce {name} rule - {len(vs)} violations found"
            examples = [v.description for v in vs[:3]]
            rules.append(
                GeneratedRule(
                    rule_name=f"enforce_{name}",
                    rule_type=rule_type,
                    rule_text=text,
                    confidence_score=0.8,
                    pattern_basis=name,
                    examples=examples,
                    rationale=f"Based on {len(vs)} violations of existing rule.",
                )
            )
        return rules

    def _enhance_rules_with_o3(
        self, rules: list[GeneratedRule], pattern_analysis: PatternAnalysis
    ) -> list[GeneratedRule]:
        """Use O3 model to enhance and validate rules."""
        enhanced: list[GeneratedRule] = []
        for rule in rules:
            try:
                prompt = self._create_rule_enhancement_prompt(rule, pattern_analysis)
                # Convert string prompt to messages format expected by O3ModelGenerator
                messages = [{"role": "user", "content": prompt}]
                response = self.model_generator.generate(messages)
                enhanced.append(self._apply_o3_enhancements(rule, response))
            except Exception as e:
                self.logger.log_error(f"Failed to enhance rule {rule.rule_name}: {e}")
                raise
        return enhanced

    def _create_rule_enhancement_prompt(
        self, rule: GeneratedRule, pattern_analysis: PatternAnalysis
    ) -> str:
        """Create prompt for O3 model to enhance a rule."""
        return (
            f"Enhance the following coding rule based on pattern analysis:\n\n"
            f"Current Rule: {rule.rule_text}\n"
            f"Rule Type: {rule.rule_type}\n"
            f"Confidence Score: {rule.confidence_score}\n"
            f"Pattern Basis: {rule.pattern_basis}\n"
            f"Examples: {', '.join(rule.examples)}\n"
            f"Rationale: {rule.rationale}\n\n"
            f"Pattern Analysis Context:\n"
            f"- Total violations: {len(pattern_analysis.violations)}\n"
            f"- Consistency scores: {pattern_analysis.consistency_scores}\n"
            f"- Recommendations: {pattern_analysis.recommendations}\n\n"
            f"Please enhance this rule to be:\n"
            f"1. More specific and actionable\n"
            f"2. Clearer in its requirements\n"
            f"3. Better justified with rationale\n"
            f"4. More comprehensive in coverage\n\n"
            f"Return the enhanced rule text only, without markdown formatting."
        )

    def _apply_o3_enhancements(
        self, rule: GeneratedRule, o3_response: str
    ) -> GeneratedRule:
        """Apply O3 model enhancements to a rule."""
        text = o3_response.strip()
        if not (20 < len(text) < 500):
            text = rule.rule_text
        return GeneratedRule(
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            rule_text=text,
            confidence_score=rule.confidence_score,
            pattern_basis=rule.pattern_basis,
            examples=rule.examples,
            rationale=rule.rationale,
        )

    def _resolve_rule_conflicts(self, rules: list[GeneratedRule]) -> list[str]:
        """Resolve conflicts between rules."""
        conflicts: list[str] = []
        for r1 in rules:
            for r2 in rules:
                if r1 is not r2 and self._rules_conflict(r1, r2):
                    conflicts.append(
                        f"Conflict between {r1.rule_name} ({r1.rule_type}) and {r2.rule_name} ({r2.rule_type})"
                    )
        return conflicts

    def _rules_conflict(self, r1: GeneratedRule, r2: GeneratedRule) -> bool:
        """Check if two rules conflict."""
        if r1.pattern_basis == r2.pattern_basis and r1.rule_type != r2.rule_type:
            return True
        if "absolute" in r1.pattern_basis and "relative" in r2.pattern_basis:
            return True
        return False

    def _create_rule_hierarchy(
        self, rules: list[GeneratedRule]
    ) -> dict[str, list[GeneratedRule]]:
        """Create rule hierarchy by type."""
        hierarchy: dict[str, list[GeneratedRule]] = {
            "critical": [],
            "important": [],
            "optional": [],
        }
        for rule in rules:
            hierarchy[rule.rule_type].append(rule)
        return hierarchy

    def _calculate_confidence_scores(
        self, rules: list[GeneratedRule], pattern_analysis: PatternAnalysis
    ) -> dict[str, float]:
        """Calculate adjusted confidence scores for rules."""
        scores: dict[str, float] = {}
        for rule in rules:
            base = rule.confidence_score
            count = sum(
                1
                for v in pattern_analysis.violations
                if v.rule_name in rule.pattern_basis
            )
            adj = min(1.0, base + 0.1) if count > 0 else base
            scores[rule.rule_name] = adj
        return scores

    def _generate_rule_recommendations(
        self, rules: list[GeneratedRule], pattern_analysis: PatternAnalysis
    ) -> list[str]:
        """Generate recommendations for rule implementation."""
        recs: list[str] = []
        high = [r for r in rules if r.confidence_score > 0.8]
        if high:
            recs.append(f"Implement {len(high)} high-confidence rules immediately")
        critical = [r for r in rules if r.rule_type == "critical"]
        if critical:
            recs.append(f"Prioritize implementation of {len(critical)} critical rules")
        if pattern_analysis.violations:
            recs.append("Focus on rules that address frequent violations")
        return recs
