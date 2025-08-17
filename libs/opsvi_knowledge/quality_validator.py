#!/usr/bin/env python3
"""
Knowledge Quality Validator
Validates and scores knowledge entries for quality assurance
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

import numpy as np
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality levels for knowledge entries"""

    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"  # 75-89%
    FAIR = "fair"  # 60-74%
    POOR = "poor"  # 40-59%
    UNACCEPTABLE = "unacceptable"  # <40%


class ValidationRule(Enum):
    """Validation rules for knowledge"""

    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    CLARITY = "clarity"
    ACTIONABILITY = "actionability"
    REFERENCES = "references"


@dataclass
class ValidationResult:
    """Result of knowledge validation"""

    knowledge_id: str
    overall_score: float
    quality_level: QualityLevel
    passed_rules: List[ValidationRule] = field(default_factory=list)
    failed_rules: List[ValidationRule] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


class KnowledgeQualityValidator:
    """Validates knowledge quality"""

    def __init__(
        self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None
    ):
        self.neo4j_uri = neo4j_uri or "bolt://localhost:7687"
        self.neo4j_user = neo4j_user or "neo4j"
        self.neo4j_password = neo4j_password or "password"
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
        )

        # Weights for different validation rules
        self.rule_weights = {
            ValidationRule.COMPLETENESS: 0.20,
            ValidationRule.ACCURACY: 0.15,
            ValidationRule.RELEVANCE: 0.15,
            ValidationRule.CONSISTENCY: 0.15,
            ValidationRule.UNIQUENESS: 0.10,
            ValidationRule.CLARITY: 0.10,
            ValidationRule.ACTIONABILITY: 0.10,
            ValidationRule.REFERENCES: 0.05,
        }

    def validate_knowledge(self, knowledge: Dict) -> ValidationResult:
        """Validate a single knowledge entry"""
        result = ValidationResult(
            knowledge_id=knowledge.get("knowledge_id", "unknown"),
            overall_score=0.0,
            quality_level=QualityLevel.UNACCEPTABLE,
        )

        # Run validation rules
        scores = {}

        # Check completeness
        completeness_score = self._check_completeness(knowledge, result)
        scores[ValidationRule.COMPLETENESS] = completeness_score

        # Check accuracy
        accuracy_score = self._check_accuracy(knowledge, result)
        scores[ValidationRule.ACCURACY] = accuracy_score

        # Check relevance
        relevance_score = self._check_relevance(knowledge, result)
        scores[ValidationRule.RELEVANCE] = relevance_score

        # Check consistency
        consistency_score = self._check_consistency(knowledge, result)
        scores[ValidationRule.CONSISTENCY] = consistency_score

        # Check uniqueness
        uniqueness_score = self._check_uniqueness(knowledge, result)
        scores[ValidationRule.UNIQUENESS] = uniqueness_score

        # Check clarity
        clarity_score = self._check_clarity(knowledge, result)
        scores[ValidationRule.CLARITY] = clarity_score

        # Check actionability
        actionability_score = self._check_actionability(knowledge, result)
        scores[ValidationRule.ACTIONABILITY] = actionability_score

        # Check references
        references_score = self._check_references(knowledge, result)
        scores[ValidationRule.REFERENCES] = references_score

        # Calculate overall score
        overall_score = sum(
            score * self.rule_weights[rule] for rule, score in scores.items()
        )

        result.overall_score = overall_score
        result.quality_level = self._determine_quality_level(overall_score)
        result.details["rule_scores"] = {
            rule.value: score for rule, score in scores.items()
        }

        # Categorize passed/failed rules
        for rule, score in scores.items():
            if score >= 0.7:
                result.passed_rules.append(rule)
            else:
                result.failed_rules.append(rule)

        # Generate suggestions
        self._generate_suggestions(knowledge, result, scores)

        return result

    def _check_completeness(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check if knowledge has all required fields"""
        required_fields = [
            "knowledge_id",
            "knowledge_type",
            "content",
            "confidence_score",
        ]
        optional_fields = ["context", "tags", "description", "embedding"]

        # Check required fields
        missing_required = [f for f in required_fields if not knowledge.get(f)]
        if missing_required:
            result.warnings.append(
                f"Missing required fields: {', '.join(missing_required)}"
            )
            return 0.0

        # Check optional fields
        present_optional = [f for f in optional_fields if knowledge.get(f)]
        optional_score = len(present_optional) / len(optional_fields)

        # Check content length
        content = knowledge.get("content", "")
        if len(content) < 20:
            result.warnings.append("Content is too short (< 20 characters)")
            return 0.3
        elif len(content) < 50:
            result.warnings.append("Content could be more detailed")
            return 0.6 + optional_score * 0.2

        return 0.8 + optional_score * 0.2

    def _check_accuracy(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check accuracy indicators"""
        score = 1.0

        # Check confidence score
        confidence = knowledge.get("confidence_score", 0)
        if confidence < 0.5:
            result.warnings.append(f"Low confidence score: {confidence:.2f}")
            score *= 0.5
        elif confidence < 0.7:
            score *= 0.8

        # Check if it has been validated
        if knowledge.get("validated", False):
            score *= 1.1  # Bonus for validation

        # Check failure count
        failure_count = knowledge.get("failure_count", 0)
        if failure_count > 0:
            score *= max(0.5, 1 - failure_count * 0.1)
            result.warnings.append(f"Has {failure_count} recorded failures")

        return min(1.0, score)

    def _check_relevance(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check relevance to knowledge type"""
        knowledge_type = knowledge.get("knowledge_type", "")
        content = knowledge.get("content", "").lower()

        # Type-specific keywords
        type_keywords = {
            "ERROR_SOLUTION": ["error", "fix", "solution", "resolve", "issue"],
            "CODE_PATTERN": ["code", "pattern", "implementation", "function", "class"],
            "WORKFLOW": ["workflow", "process", "step", "procedure", "flow"],
            "USER_PREFERENCE": ["preference", "setting", "config", "option"],
            "TOOL_USAGE": ["tool", "command", "usage", "utility"],
            "CONTEXT_PATTERN": ["context", "pattern", "scenario", "situation"],
        }

        if knowledge_type in type_keywords:
            keywords = type_keywords[knowledge_type]
            matches = sum(1 for kw in keywords if kw in content)
            relevance = min(1.0, matches / 2)  # At least 2 keywords for full score

            if relevance < 0.5:
                result.warnings.append(f"Content doesn't match type '{knowledge_type}'")

            return relevance

        return 0.8  # Default for unknown types

    def _check_consistency(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check internal consistency"""
        score = 1.0

        # Check if tags match content
        tags = knowledge.get("tags", [])
        content = knowledge.get("content", "").lower()

        if tags:
            tag_matches = sum(1 for tag in tags if str(tag).lower() in content)
            tag_consistency = tag_matches / len(tags)
            if tag_consistency < 0.5:
                result.warnings.append("Tags don't match content well")
                score *= 0.8

        # Check timestamp consistency
        created_at = knowledge.get("created_at")
        updated_at = knowledge.get("updated_at")

        if created_at and updated_at:
            try:
                if updated_at < created_at:
                    result.warnings.append("Updated timestamp before created timestamp")
                    score *= 0.5
            except Exception:
                pass

        return score

    def _check_uniqueness(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check if knowledge is unique"""
        # Check for duplicates in database
        with self.driver.session() as session:
            # Check exact content match
            exact_query = """
            MATCH (k:Knowledge)
            WHERE k.content = $content
            AND k.knowledge_id <> $id
            RETURN count(k) as duplicates
            """

            exact_result = session.run(
                exact_query,
                content=knowledge.get("content", ""),
                id=knowledge.get("knowledge_id", ""),
            )

            duplicates = exact_result.single()["duplicates"]

            if duplicates > 0:
                result.warnings.append(f"Found {duplicates} exact duplicates")
                return 0.0

            # Check similar content (would need embedding comparison in production)
            # For now, just return high score if no exact duplicates
            return 1.0

    def _check_clarity(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check clarity and readability"""
        content = knowledge.get("content", "")

        if not content:
            return 0.0

        score = 1.0

        # Check sentence structure
        sentences = content.split(".")
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])

        if avg_sentence_length > 30:
            result.warnings.append("Sentences are too long (avg > 30 words)")
            score *= 0.7
        elif avg_sentence_length < 5:
            result.warnings.append("Sentences are too short (avg < 5 words)")
            score *= 0.8

        # Check for code blocks if it's code-related
        if knowledge.get("knowledge_type") == "CODE_PATTERN":
            if (
                "```" not in content
                and "def " not in content
                and "class " not in content
            ):
                result.warnings.append("Code pattern lacks code examples")
                score *= 0.6

        # Check for structure markers
        structure_markers = ["1.", "2.", "*", "-", "#", "##"]
        has_structure = any(marker in content for marker in structure_markers)

        if len(content) > 200 and not has_structure:
            result.warnings.append(
                "Long content lacks structure (bullets, numbers, etc)"
            )
            score *= 0.8

        return score

    def _check_actionability(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check if knowledge is actionable"""
        content = knowledge.get("content", "").lower()
        knowledge_type = knowledge.get("knowledge_type", "")

        score = 1.0

        # Action words
        action_words = [
            "do",
            "use",
            "run",
            "execute",
            "implement",
            "apply",
            "follow",
            "create",
            "update",
            "delete",
            "modify",
            "check",
            "verify",
        ]

        has_actions = any(word in content for word in action_words)

        if knowledge_type in ["ERROR_SOLUTION", "WORKFLOW", "TOOL_USAGE"]:
            if not has_actions:
                result.warnings.append("Lacks actionable instructions")
                score *= 0.5

        # Check for specific instructions
        instruction_patterns = [
            r"\b(step \d+)",  # Step 1, Step 2, etc.
            r"\b(first|then|next|finally)",  # Sequence words
            r"\b(run|execute|call)\s+\w+",  # Commands
        ]

        has_instructions = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in instruction_patterns
        )

        if knowledge_type == "WORKFLOW" and not has_instructions:
            result.warnings.append("Workflow lacks clear instructions")
            score *= 0.6

        return score

    def _check_references(self, knowledge: Dict, result: ValidationResult) -> float:
        """Check for proper references and sources"""
        content = knowledge.get("content", "")
        context = knowledge.get("context", {})

        score = 0.8  # Base score

        # Check for URLs
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, content)

        if urls:
            score += 0.1

        # Check for file references
        file_pattern = r"[a-zA-Z0-9_\-/]+\.(py|js|ts|md|txt|json|yaml)"
        files = re.findall(file_pattern, content)

        if files:
            score += 0.1

        # Check if context has sources
        if context and isinstance(context, dict):
            if "source" in context or "reference" in context or "url" in context:
                score = 1.0

        return min(1.0, score)

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score"""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.75:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.FAIR
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _generate_suggestions(
        self, knowledge: Dict, result: ValidationResult, scores: Dict
    ):
        """Generate improvement suggestions"""

        # Completeness suggestions
        if scores[ValidationRule.COMPLETENESS] < 0.8:
            if not knowledge.get("description"):
                result.suggestions.append("Add a description field for better context")
            if not knowledge.get("tags"):
                result.suggestions.append("Add tags for better categorization")
            if not knowledge.get("embedding"):
                result.suggestions.append("Generate embedding for similarity search")

        # Clarity suggestions
        if scores[ValidationRule.CLARITY] < 0.8:
            result.suggestions.append(
                "Improve content structure with bullets or numbered lists"
            )
            if knowledge.get("knowledge_type") == "CODE_PATTERN":
                result.suggestions.append("Add code examples with proper formatting")

        # Actionability suggestions
        if scores[ValidationRule.ACTIONABILITY] < 0.8:
            result.suggestions.append("Add specific action steps or commands")
            result.suggestions.append("Include concrete examples of usage")

        # Reference suggestions
        if scores[ValidationRule.REFERENCES] < 0.8:
            result.suggestions.append("Add references to documentation or sources")
            result.suggestions.append("Include relevant URLs or file paths")

    def validate_batch(self, limit: int = 100) -> List[ValidationResult]:
        """Validate a batch of knowledge entries"""
        query = """
        MATCH (k:Knowledge)
        WHERE k.last_validated IS NULL
        OR k.last_validated < datetime() - duration('P7D')
        RETURN k
        LIMIT $limit
        """

        results = []

        with self.driver.session() as session:
            result = session.run(query, limit=limit)

            for record in result:
                knowledge = dict(record["k"])
                validation = self.validate_knowledge(knowledge)
                results.append(validation)

                # Update validation timestamp
                update_query = """
                MATCH (k:Knowledge {knowledge_id: $id})
                SET k.last_validated = datetime(),
                    k.quality_score = $score,
                    k.quality_level = $level
                """

                session.run(
                    update_query,
                    id=validation.knowledge_id,
                    score=validation.overall_score,
                    level=validation.quality_level.value,
                )

        return results

    def get_quality_report(self) -> Dict:
        """Generate quality report for all knowledge"""
        query = """
        MATCH (k:Knowledge)
        WITH k.quality_level as level, count(*) as count
        RETURN level, count
        ORDER BY level
        """

        with self.driver.session() as session:
            result = session.run(query)

            distribution = {}
            total = 0

            for record in result:
                level = record["level"]
                count = record["count"]
                distribution[level] = count
                total += count

            # Calculate average quality
            avg_query = """
            MATCH (k:Knowledge)
            WHERE k.quality_score IS NOT NULL
            RETURN avg(k.quality_score) as avg_score
            """

            avg_result = session.run(avg_query)
            avg_score = avg_result.single()["avg_score"] or 0

            return {
                "total_entries": total,
                "average_quality_score": avg_score,
                "distribution": distribution,
                "recommendations": self._generate_report_recommendations(
                    distribution, avg_score
                ),
            }

    def _generate_report_recommendations(
        self, distribution: Dict, avg_score: float
    ) -> List[str]:
        """Generate recommendations based on quality report"""
        recommendations = []

        if avg_score < 0.7:
            recommendations.append(
                "Overall quality is below acceptable levels - focus on improvement"
            )

        poor_count = distribution.get("poor", 0) + distribution.get("unacceptable", 0)
        if poor_count > 0:
            recommendations.append(
                f"Review and improve {poor_count} low-quality entries"
            )

        if distribution.get("excellent", 0) < distribution.get("fair", 0):
            recommendations.append(
                "Focus on elevating 'fair' entries to 'good' or 'excellent'"
            )

        return recommendations

    def close(self):
        """Close database connection"""
        self.driver.close()


# Example usage
def main():
    """Example validation"""
    validator = KnowledgeQualityValidator()

    # Example knowledge entry
    knowledge = {
        "knowledge_id": "test-123",
        "knowledge_type": "ERROR_SOLUTION",
        "content": (
            "To fix ImportError, run: pip install missing-package. "
            "This resolves the missing module issue."
        ),
        "confidence_score": 0.92,
        "tags": ["error", "python", "import"],
        "context": {"error_type": "ImportError"},
    }

    # Validate
    result = validator.validate_knowledge(knowledge)

    print(f"Knowledge ID: {result.knowledge_id}")
    print(f"Quality Score: {result.overall_score:.2%}")
    print(f"Quality Level: {result.quality_level.value}")
    print(f"Passed Rules: {[r.value for r in result.passed_rules]}")
    print(f"Failed Rules: {[r.value for r in result.failed_rules]}")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")

    validator.close()


if __name__ == "__main__":
    main()
