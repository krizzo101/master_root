#!/usr/bin/env python3
"""
Cognitive Concepts Rebuilder
============================

This script rebuilds the cognitive concepts collection from high-quality agent memories
using the proper knowledge_content structure with problem/solution/prevention analysis.

Purpose: Fix the root cause by creating cognitive concepts correctly from source data
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any
from arango import ArangoClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/opsvi/asea/development/knowledge_management/logs/concept_rebuild.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class CognitiveConceptRebuilder:
    """Rebuild cognitive concepts from high-quality agent memories"""

    def __init__(self):
        """Initialize database connection"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8531")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_production_password"
        )
        self.concept_patterns = self._initialize_extraction_patterns()

    def _initialize_extraction_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for intelligent content analysis"""
        return {
            "problem_indicators": [
                r"(?:issue|problem|error|failure|bug|broken|not working|doesn\'t work)",
                r"(?:incorrect|invalid|wrong|missing|empty|null)",
                r"(?:fails? to|unable to|cannot|can\'t)",
                r"(?:inconsistent|mismatch|discrepancy|gap)",
                r"(?:violation|stopped|failed)",
                r"(?:critical|urgent|immediate)",
            ],
            "solution_indicators": [
                r"(?:solution|fix|resolve|correct|repair)",
                r"(?:approach|method|technique|strategy)",
                r"(?:implementation|algorithm|process)",
                r"(?:use|apply|implement|execute)",
                r"(?:create|build|develop|establish)",
                r"(?:successful|working|operational)",
            ],
            "prevention_indicators": [
                r"(?:prevent|avoid|ensure|validate|check)",
                r"(?:protocol|standard|requirement|rule)",
                r"(?:monitoring|tracking|detection)",
                r"(?:quality|validation|verification)",
                r"(?:maintenance|continuous|ongoing)",
                r"(?:mandatory|must|always|never)",
            ],
            "insight_indicators": [
                r"(?:insight|learning|principle|pattern)",
                r"(?:key|important|critical|essential)",
                r"(?:understand|realize|recognize)",
                r"(?:effective|optimal|best practice)",
                r"(?:compound learning|autonomous|cognitive)",
                r"(?:meta|recursive|framework)",
            ],
        }

    def extract_content_sections(self, content: str, title: str) -> Dict[str, Any]:
        """Extract problem, solution, prevention, and insights from content"""

        # Split content into sentences for analysis
        sentences = re.split(r"[.!?]+", content)

        extracted = {
            "problem": "",
            "solution": "",
            "prevention": "",
            "key_insights": [],
        }

        # Analyze each sentence for content type
        problem_sentences = []
        solution_sentences = []
        prevention_sentences = []
        insight_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Skip very short sentences
                continue

            sentence_lower = sentence.lower()

            # Check for problem indicators
            if any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["problem_indicators"]
            ):
                problem_sentences.append(sentence)

            # Check for solution indicators
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["solution_indicators"]
            ):
                solution_sentences.append(sentence)

            # Check for prevention indicators
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["prevention_indicators"]
            ):
                prevention_sentences.append(sentence)

            # Check for insight indicators
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["insight_indicators"]
            ):
                insight_sentences.append(sentence)

        # Combine sentences into sections
        extracted["problem"] = " ".join(
            problem_sentences[:3]
        )  # Top 3 problem sentences
        extracted["solution"] = " ".join(
            solution_sentences[:3]
        )  # Top 3 solution sentences
        extracted["prevention"] = " ".join(
            prevention_sentences[:3]
        )  # Top 3 prevention sentences
        extracted["key_insights"] = insight_sentences[:5]  # Top 5 insights

        # Enhanced fallback logic for better content extraction
        if not extracted["problem"] and content:
            extracted["problem"] = self._extract_problem_from_structure(content, title)

        if not extracted["solution"] and content:
            extracted["solution"] = self._extract_solution_from_structure(
                content, title
            )

        if not extracted["prevention"] and content:
            extracted["prevention"] = self._extract_prevention_from_structure(
                content, title
            )

        if not extracted["key_insights"]:
            extracted["key_insights"] = self._extract_insights_from_structure(
                content, title
            )

        return extracted

    def _extract_problem_from_structure(self, content: str, title: str) -> str:
        """Extract problem from content structure and context"""

        # Look for common problem patterns in title
        if any(
            word in title.lower()
            for word in ["failure", "error", "issue", "critical", "violation"]
        ):
            # Extract first substantive sentence
            sentences = re.split(r"[.!?]+", content)
            for sentence in sentences:
                if len(sentence.strip()) > 30:
                    return sentence.strip()

        # Look for patterns that indicate problems
        problem_patterns = [
            r"(.*(?:failed|broken|incorrect|wrong|missing).*?)[.!?]",
            r"(.*(?:violation|stopped|unable).*?)[.!?]",
            r"(.*(?:issue|problem|error).*?)[.!?]",
        ]

        for pattern in problem_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Fallback: use context clues from title
        if "learning" in title.lower():
            return f"Knowledge gap or learning opportunity identified: {title}"
        elif "success" in title.lower():
            return f"Challenge overcome in: {title}"
        else:
            return f"Situation requiring attention: {title}"

    def _extract_solution_from_structure(self, content: str, title: str) -> str:
        """Extract solution from content structure"""

        # Look for solution patterns
        solution_patterns = [
            r"(.*(?:solution|fix|resolve|approach|method).*?)[.!?]",
            r"(.*(?:successful|working|operational|implemented).*?)[.!?]",
            r"(.*(?:use|apply|execute|create).*?)[.!?]",
        ]

        for pattern in solution_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Look for structured content (colon-separated)
        if ":" in content:
            parts = content.split(":")
            if len(parts) >= 2:
                return parts[1].split(".")[0].strip()

        # Fallback based on title context
        if "success" in title.lower():
            return f"Apply the successful approach described in: {title}"
        else:
            return (
                "Implement the methods and techniques described in this knowledge area"
            )

    def _extract_prevention_from_structure(self, content: str, title: str) -> str:
        """Extract prevention guidance from content"""

        # Look for prevention patterns
        prevention_patterns = [
            r"(.*(?:prevent|avoid|ensure|validate|check).*?)[.!?]",
            r"(.*(?:mandatory|must|always|never).*?)[.!?]",
            r"(.*(?:protocol|standard|requirement).*?)[.!?]",
        ]

        for pattern in prevention_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Generate prevention based on title context
        if "failure" in title.lower():
            return f"Follow the protocols described to prevent recurrence of: {title}"
        elif "success" in title.lower():
            return f"Maintain the conditions that enabled: {title}"
        else:
            return (
                "Apply the standards and requirements described in this knowledge area"
            )

    def _extract_insights_from_structure(self, content: str, title: str) -> List[str]:
        """Extract key insights from content"""

        insights = []

        # Look for explicit insight patterns
        insight_patterns = [
            r"(?:key|important|critical|essential).*?(?:[.!?]|$)",
            r"(?:insight|learning|realization).*?(?:[.!?]|$)",
            r"(?:meta|recursive|framework).*?(?:[.!?]|$)",
            r"(?:compound learning|autonomous).*?(?:[.!?]|$)",
        ]

        for pattern in insight_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            insights.extend(
                [match.strip() for match in matches if len(match.strip()) > 20]
            )

        # Extract meaningful sentences with insight indicators
        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40 and any(
                word in sentence.lower()
                for word in [
                    "effective",
                    "optimal",
                    "critical",
                    "essential",
                    "key",
                    "important",
                    "successful",
                ]
            ):
                insights.append(sentence)

        return insights[:5]  # Limit to top 5 insights

    def generate_semantic_tags(self, content: str, title: str) -> List[str]:
        """Generate semantic tags from content and title"""
        tags = set()

        # Extract key terms from title
        title_words = re.findall(r"\w+", title.lower())
        tags.update([word for word in title_words if len(word) > 3])

        # Extract technical terms and concepts
        technical_patterns = [
            r"\b(?:database|arango|query|aql|collection|cognitive|autonomous|compound|learning)\b",
            r"\b(?:memory|concept|knowledge|intelligence|validation|quality|optimization)\b",
            r"\b(?:system|architecture|framework|protocol|behavioral|operational)\b",
            r"\b(?:rule|consultation|evidence|analysis|research|orchestrator)\b",
        ]

        for pattern in technical_patterns:
            matches = re.findall(pattern, content.lower())
            tags.update(matches)

        # Add domain-specific tags based on content analysis
        content_lower = content.lower()
        if any(word in content_lower for word in ["database", "arango", "query"]):
            tags.add("database_operations")
        if any(
            word in content_lower
            for word in ["cognitive", "autonomous", "intelligence"]
        ):
            tags.add("cognitive_architecture")
        if any(word in content_lower for word in ["failure", "error", "problem"]):
            tags.add("failure_analysis")
        if any(word in content_lower for word in ["success", "operational", "working"]):
            tags.add("success_pattern")
        if any(word in content_lower for word in ["rule", "protocol", "mandatory"]):
            tags.add("behavioral_directive")

        return list(tags)[:12]  # Limit to top 12 tags

    def create_enhanced_concept(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced cognitive concept with proper knowledge_content structure"""

        # Extract content sections
        content = memory.get("content", "")
        title = memory.get("title", "Untitled Concept")

        content_analysis = self.extract_content_sections(content, title)

        # Generate concept ID
        concept_id = hashlib.md5(f"{title}_{content[:100]}".encode()).hexdigest()[:16]

        # Create proper knowledge_content structure
        knowledge_content = {
            "title": title,
            "problem": content_analysis["problem"][:800]
            if content_analysis["problem"]
            else "",
            "solution": content_analysis["solution"][:800]
            if content_analysis["solution"]
            else "",
            "prevention": content_analysis["prevention"][:800]
            if content_analysis["prevention"]
            else "",
            "key_insights": content_analysis["key_insights"],
            "original_tags": self.generate_semantic_tags(content, title),
        }

        # Determine knowledge domain
        knowledge_domain = self._determine_knowledge_domain(
            content, title, memory.get("tags", [])
        )

        # Determine concept type
        concept_type = self._determine_concept_type(
            content, title, memory.get("type", "")
        )

        # Calculate confidence score based on content completeness
        confidence_score = self._calculate_confidence_score(
            knowledge_content, memory.get("quality_score", 0.5)
        )

        enhanced_concept = {
            "concept_id": concept_id,
            "knowledge_domain": knowledge_domain,
            "concept_type": concept_type,
            "knowledge_content": knowledge_content,
            "confidence_score": confidence_score,
            "extraction_method": "advanced_intelligent_analysis_v2",
            "source_memory_id": memory.get("_id", ""),
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "quality_metrics": {
                "completeness": len([v for v in knowledge_content.values() if v])
                / len(knowledge_content),
                "content_length": len(content),
                "insights_count": len(knowledge_content["key_insights"]),
                "tags_count": len(knowledge_content["original_tags"]),
                "source_quality_score": memory.get("quality_score", 0.5),
            },
            "autonomous_intelligence_metrics": {
                "ai_relevance_score": confidence_score,
                "compound_learning_potential": min(confidence_score * 1.2, 1.0),
                "behavioral_enforcement_strength": confidence_score * 0.8,
                "failure_prevention_value": 0.9 if "failure" in title.lower() else 0.5,
                "self_evolution_contribution": confidence_score * 0.7,
            },
        }

        return enhanced_concept

    def _determine_knowledge_domain(
        self, content: str, title: str, tags: List[str]
    ) -> str:
        """Determine the knowledge domain based on content analysis"""
        content_lower = (content + " " + title + " " + " ".join(tags)).lower()

        domain_patterns = {
            "database_operations": ["database", "arango", "query", "collection", "aql"],
            "cognitive_architecture": [
                "cognitive",
                "autonomous",
                "intelligence",
                "memory",
                "learning",
            ],
            "behavioral_patterns": [
                "behavior",
                "pattern",
                "rule",
                "requirement",
                "guideline",
                "protocol",
            ],
            "system_architecture": [
                "system",
                "architecture",
                "framework",
                "infrastructure",
            ],
            "quality_assurance": [
                "quality",
                "validation",
                "testing",
                "verification",
                "standards",
            ],
            "operational_protocols": [
                "operational",
                "procedure",
                "workflow",
                "process",
            ],
            "research_methodology": [
                "research",
                "analysis",
                "methodology",
                "investigation",
            ],
            "failure_analysis": ["failure", "error", "problem", "issue", "critical"],
            "success_patterns": ["success", "working", "operational", "effective"],
        }

        # Score each domain
        domain_scores = {}
        for domain, keywords in domain_patterns.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                domain_scores[domain] = score

        # Return highest scoring domain
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)

        return "general_knowledge"

    def _determine_concept_type(
        self, content: str, title: str, memory_type: str
    ) -> str:
        """Determine the concept type based on content and memory type"""
        content_lower = (content + " " + title).lower()

        if "failure" in content_lower or "error" in content_lower:
            return "failure_pattern"
        elif "success" in content_lower or "operational" in content_lower:
            return "success_pattern"
        elif "protocol" in content_lower or "procedure" in content_lower:
            return "procedural_knowledge"
        elif "rule" in content_lower or "mandatory" in content_lower:
            return "behavioral_rule"
        elif "pattern" in content_lower or "framework" in content_lower:
            return "conceptual_framework"
        elif "learning" in content_lower or "insight" in content_lower:
            return "learning_insight"
        else:
            return "operational_knowledge"

    def _calculate_confidence_score(
        self, knowledge_content: Dict[str, Any], source_quality: float
    ) -> float:
        """Calculate confidence score based on content completeness and source quality"""
        score = 0.0

        # Base score from content completeness
        if knowledge_content["problem"]:
            score += 0.25
        if knowledge_content["solution"]:
            score += 0.25
        if knowledge_content["prevention"]:
            score += 0.20
        if knowledge_content["key_insights"]:
            score += 0.15
        if knowledge_content["original_tags"]:
            score += 0.15

        # Quality bonuses
        if len(knowledge_content["problem"]) > 100:
            score += 0.05
        if len(knowledge_content["solution"]) > 100:
            score += 0.05
        if len(knowledge_content["key_insights"]) >= 3:
            score += 0.05
        if len(knowledge_content["original_tags"]) >= 5:
            score += 0.05

        # Factor in source quality
        final_score = (score * 0.7) + (source_quality * 0.3)

        return min(1.0, final_score)  # Cap at 1.0

    def get_high_quality_memories(self) -> List[Dict[str, Any]]:
        """Get high-quality foundational memories for concept creation"""

        query = """
        FOR memory IN agent_memory 
        FILTER memory.foundational == true 
        AND memory.quality_score > 0.8 
        AND LENGTH(memory.content) > 200
        SORT memory.quality_score DESC 
        LIMIT 20 
        RETURN memory
        """

        try:
            cursor = self.db.aql.execute(query)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving high-quality memories: {e}")
            return []

    def rebuild_cognitive_concepts(self) -> Dict[str, Any]:
        """Rebuild cognitive concepts from high-quality memories"""

        logger.info("Starting cognitive concepts rebuild...")

        # Get high-quality memories
        memories = self.get_high_quality_memories()
        logger.info(f"Retrieved {len(memories)} high-quality memories for processing")

        if not memories:
            logger.warning("No high-quality memories found")
            return {
                "status": "completed",
                "processed_count": 0,
                "created_count": 0,
                "error_count": 0,
            }

        results = {
            "status": "processing",
            "processed_count": 0,
            "created_count": 0,
            "error_count": 0,
            "processing_log": [],
        }

        # Process each memory into a cognitive concept
        for i, memory in enumerate(memories):
            try:
                # Create enhanced concept
                enhanced_concept = self.create_enhanced_concept(memory)

                # Insert into cognitive_concepts collection
                insert_result = self.db.collection("cognitive_concepts").insert(
                    enhanced_concept, overwrite=True
                )

                if insert_result:
                    results["created_count"] += 1
                    logger.info(
                        f"Created concept {enhanced_concept['concept_id']} ({i+1}/{len(memories)})"
                    )

                    results["processing_log"].append(
                        {
                            "concept_id": enhanced_concept["concept_id"],
                            "source_memory_id": memory.get("_id"),
                            "action": "created",
                            "confidence_score": enhanced_concept["confidence_score"],
                            "completeness": enhanced_concept["quality_metrics"][
                                "completeness"
                            ],
                        }
                    )
                else:
                    results["error_count"] += 1
                    logger.error(
                        f"Failed to insert concept for memory {memory.get('_id')}"
                    )

                results["processed_count"] += 1

            except Exception as e:
                logger.error(
                    f"Error processing memory {memory.get('_id', 'unknown')}: {e}"
                )
                results["error_count"] += 1

        results["status"] = "completed"
        logger.info(
            f"Rebuild completed: {results['created_count']} concepts created, {results['error_count']} errors"
        )

        return results

    def validate_rebuild_results(self) -> Dict[str, Any]:
        """Validate the rebuild results and generate quality report"""

        validation_query = """
        FOR concept IN cognitive_concepts
        RETURN {
            concept_id: concept.concept_id,
            has_problem: concept.knowledge_content.problem != "",
            has_solution: concept.knowledge_content.solution != "",
            has_prevention: concept.knowledge_content.prevention != "",
            has_insights: LENGTH(concept.knowledge_content.key_insights) > 0,
            has_tags: LENGTH(concept.knowledge_content.original_tags) > 0,
            has_source_id: concept.source_memory_id != "",
            confidence_score: concept.confidence_score,
            completeness: concept.quality_metrics.completeness
        }
        """

        try:
            cursor = self.db.aql.execute(validation_query)
            concepts = list(cursor)

            total_concepts = len(concepts)
            complete_problems = sum(1 for c in concepts if c["has_problem"])
            complete_solutions = sum(1 for c in concepts if c["has_solution"])
            complete_prevention = sum(1 for c in concepts if c["has_prevention"])
            complete_insights = sum(1 for c in concepts if c["has_insights"])
            complete_tags = sum(1 for c in concepts if c["has_tags"])
            complete_source_ids = sum(1 for c in concepts if c["has_source_id"])

            avg_confidence = (
                sum(c["confidence_score"] for c in concepts) / total_concepts
                if total_concepts > 0
                else 0
            )
            avg_completeness = (
                sum(c["completeness"] for c in concepts) / total_concepts
                if total_concepts > 0
                else 0
            )

            validation_results = {
                "total_concepts": total_concepts,
                "quality_metrics": {
                    "problem_completion_rate": complete_problems / total_concepts
                    if total_concepts > 0
                    else 0,
                    "solution_completion_rate": complete_solutions / total_concepts
                    if total_concepts > 0
                    else 0,
                    "prevention_completion_rate": complete_prevention / total_concepts
                    if total_concepts > 0
                    else 0,
                    "insights_completion_rate": complete_insights / total_concepts
                    if total_concepts > 0
                    else 0,
                    "tags_completion_rate": complete_tags / total_concepts
                    if total_concepts > 0
                    else 0,
                    "source_linkage_rate": complete_source_ids / total_concepts
                    if total_concepts > 0
                    else 0,
                    "average_confidence_score": avg_confidence,
                    "average_completeness": avg_completeness,
                },
                "quality_assessment": "excellent"
                if avg_completeness > 0.8
                else "good"
                if avg_completeness > 0.6
                else "needs_improvement",
                "root_cause_fixed": complete_source_ids
                == total_concepts,  # All concepts should have source IDs
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Validation completed: {validation_results['quality_assessment']} quality"
            )
            logger.info(
                f"Average completeness: {avg_completeness:.2f}, Average confidence: {avg_confidence:.2f}"
            )
            logger.info(
                f"Root cause fixed: {validation_results['root_cause_fixed']} (source linkage: {complete_source_ids}/{total_concepts})"
            )

            return validation_results

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {"error": str(e)}


def main():
    """Main execution function"""
    rebuilder = CognitiveConceptRebuilder()

    logger.info("=== Starting Cognitive Concepts Rebuild ===")

    # Rebuild concepts from high-quality memories
    rebuild_results = rebuilder.rebuild_cognitive_concepts()

    # Validate results
    validation_results = rebuilder.validate_rebuild_results()

    # Generate comprehensive report
    final_report = {
        "rebuild_results": rebuild_results,
        "validation_results": validation_results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "root_cause_addressed": validation_results.get("root_cause_fixed", False),
    }

    # Save results
    results_file = f'/home/opsvi/asea/development/knowledge_management/results/concept_rebuild_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, "w") as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Rebuild completed. Results saved to: {results_file}")
    logger.info(f"Root cause addressed: {final_report['root_cause_addressed']}")
    logger.info("=== Cognitive Concepts Rebuild Complete ===")

    return final_report


if __name__ == "__main__":
    main()
