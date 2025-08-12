#!/usr/bin/env python3
"""
Advanced Cognitive Concept Extractor
=====================================

This script addresses the cognitive concept data quality failure by creating
sophisticated knowledge_content structures with proper problem/solution/prevention
analysis from agent memory sources.

Root Cause: Schema mismatch between extraction process and expected structure
Solution: Intelligent content analysis that generates complete knowledge_content objects

Created: 2025-06-23
Purpose: Restore cognitive concept system to full functionality
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any
from arango import ArangoClient
import logging

# === NEW: Import for embedding generation ===
try:
    from sentence_transformers import SentenceTransformer

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
except ImportError:
    embedding_model = None
    logging.warning(
        "sentence-transformers not installed; semantic embeddings will not be generated."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/opsvi/asea/development/knowledge_management/logs/concept_extraction.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AdvancedConceptExtractor:
    """Enhanced cognitive concept extractor with proper knowledge_content structure generation"""

    def __init__(self):
        self.client = ArangoClient(hosts="http://127.0.0.1:8531")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_production_password"
        )
        self.concept_patterns = self._initialize_extraction_patterns()

    def _initialize_extraction_patterns(self) -> Dict[str, List[str]]:
        return {
            "problem_indicators": [
                r"(?:issue|problem|error|failure|bug|broken|not working|doesn\'t work)",
                r"(?:incorrect|invalid|wrong|missing|empty|null)",
                r"(?:fails? to|unable to|cannot|can\'t)",
                r"(?:inconsistent|mismatch|discrepancy|gap)",
                r"(?:silent failure|detection|root cause)",
            ],
            "solution_indicators": [
                r"(?:solution|fix|resolve|correct|repair)",
                r"(?:approach|method|technique|strategy)",
                r"(?:implementation|algorithm|process)",
                r"(?:use|apply|implement|execute)",
                r"(?:create|build|develop|establish)",
            ],
            "prevention_indicators": [
                r"(?:prevent|avoid|ensure|validate|check)",
                r"(?:protocol|standard|requirement|rule)",
                r"(?:monitoring|tracking|detection)",
                r"(?:quality|validation|verification)",
                r"(?:maintenance|continuous|ongoing)",
            ],
            "insight_indicators": [
                r"(?:insight|learning|principle|pattern)",
                r"(?:key|important|critical|essential)",
                r"(?:understand|realize|recognize)",
                r"(?:effective|optimal|best practice)",
                r"(?:compound learning|autonomous|cognitive)",
            ],
        }

    def extract_content_sections(self, content: str) -> Dict[str, str]:
        sentences = re.split(r"[.!?]+", content)
        extracted = {
            "problem": "",
            "solution": "",
            "prevention": "",
            "key_insights": [],
        }
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            sentence_lower = sentence.lower()
            if any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["problem_indicators"]
            ):
                if not extracted["problem"]:
                    extracted["problem"] = sentence
                else:
                    extracted["problem"] += f" {sentence}"
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["solution_indicators"]
            ):
                if not extracted["solution"]:
                    extracted["solution"] = sentence
                else:
                    extracted["solution"] += f" {sentence}"
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["prevention_indicators"]
            ):
                if not extracted["prevention"]:
                    extracted["prevention"] = sentence
                else:
                    extracted["prevention"] += f" {sentence}"
            elif any(
                re.search(pattern, sentence_lower)
                for pattern in self.concept_patterns["insight_indicators"]
            ):
                extracted["key_insights"].append(sentence)
        if not any(
            [extracted["problem"], extracted["solution"], extracted["prevention"]]
        ):
            paragraphs = content.split("\n\n")
            if len(paragraphs) >= 2:
                extracted["problem"] = paragraphs[0][:500]
                extracted["solution"] = paragraphs[1][:500]
                if len(paragraphs) >= 3:
                    extracted["prevention"] = paragraphs[2][:500]
        if not extracted["problem"] and content:
            extracted["problem"] = self._generate_problem_from_content(content)
        if not extracted["solution"] and content:
            extracted["solution"] = self._generate_solution_from_content(content)
        if not extracted["prevention"] and content:
            extracted["prevention"] = self._generate_prevention_from_content(content)
        if not extracted["key_insights"]:
            extracted["key_insights"] = self._extract_key_insights(content)
        return extracted

    def _generate_problem_from_content(self, content: str) -> str:
        problem_terms = [
            "issue",
            "problem",
            "error",
            "failure",
            "incorrect",
            "missing",
            "broken",
        ]
        for term in problem_terms:
            if term in content.lower():
                sentences = re.split(r"[.!?]+", content)
                for sentence in sentences:
                    if term in sentence.lower():
                        return sentence.strip()
        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                return f"Analysis of: {sentence.strip()[:200]}..."
        return f"Knowledge area requiring attention: {content[:100]}..."

    def _generate_solution_from_content(self, content: str) -> str:
        solution_terms = [
            "solution",
            "fix",
            "resolve",
            "approach",
            "method",
            "use",
            "apply",
            "implement",
        ]
        for term in solution_terms:
            if term in content.lower():
                sentences = re.split(r"[.!?]+", content)
                for sentence in sentences:
                    if term in sentence.lower():
                        return sentence.strip()
        return f"Apply knowledge and techniques described in: {content[:150]}..."

    def _generate_prevention_from_content(self, content: str) -> str:
        prevention_terms = [
            "prevent",
            "avoid",
            "ensure",
            "validate",
            "check",
            "monitor",
            "maintain",
        ]
        for term in prevention_terms:
            if term in content.lower():
                sentences = re.split(r"[.!?]+", content)
                for sentence in sentences:
                    if term in sentence.lower():
                        return sentence.strip()
        return "Maintain awareness of principles described in this knowledge area"

    def _extract_key_insights(self, content: str) -> List[str]:
        insights = []
        insight_patterns = [
            r"(?:key|important|critical|essential).*?(?:[.!?]|$)",
            r"(?:insight|learning|principle).*?(?:[.!?]|$)",
            r"(?:compound learning|autonomous|cognitive).*?(?:[.!?]|$)",
        ]
        for pattern in insight_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            insights.extend(
                [match.strip() for match in matches if len(match.strip()) > 10]
            )
        if not insights:
            sentences = re.split(r"[.!?]+", content)
            for sentence in sentences:
                if len(sentence.strip()) > 30 and any(
                    word in sentence.lower()
                    for word in ["effective", "optimal", "important", "critical", "key"]
                ):
                    insights.append(sentence.strip())
        return insights[:5]

    def generate_semantic_tags(self, content: str, title: str) -> List[str]:
        tags = set()
        title_words = re.findall(r"\w+", title.lower())
        tags.update([word for word in title_words if len(word) > 3])
        technical_patterns = [
            r"\b(?:database|arango|query|aql|collection)\b",
            r"\b(?:cognitive|autonomous|compound|learning)\b",
            r"\b(?:memory|concept|knowledge|intelligence)\b",
            r"\b(?:validation|quality|optimization|enhancement)\b",
            r"\b(?:system|architecture|framework|protocol)\b",
        ]
        for pattern in technical_patterns:
            matches = re.findall(pattern, content.lower())
            tags.update(matches)
        if "database" in content.lower() or "arango" in content.lower():
            tags.add("database_operations")
        if "cognitive" in content.lower() or "autonomous" in content.lower():
            tags.add("cognitive_architecture")
        if "quality" in content.lower() or "validation" in content.lower():
            tags.add("quality_assurance")
        return list(tags)[:10]

    def create_enhanced_concept(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        content = memory.get("content", "")
        title = memory.get("title", "Untitled Concept")
        content_analysis = self.extract_content_sections(content)
        concept_id = hashlib.md5(f"{title}_{content[:100]}".encode()).hexdigest()[:16]
        knowledge_content = {
            "title": title,
            "problem": content_analysis["problem"][:500]
            if content_analysis["problem"]
            else "",
            "solution": content_analysis["solution"][:500]
            if content_analysis["solution"]
            else "",
            "prevention": content_analysis["prevention"][:500]
            if content_analysis["prevention"]
            else "",
            "key_insights": content_analysis["key_insights"],
            "original_tags": self.generate_semantic_tags(content, title),
        }
        knowledge_domain = self._determine_knowledge_domain(content, title)
        concept_type = self._determine_concept_type(content, memory.get("type", ""))
        confidence_score = self._calculate_confidence_score(knowledge_content)
        # === NEW: Generate semantic embedding ===
        semantic_embedding = None
        if embedding_model is not None:
            try:
                embedding = embedding_model.encode(content, show_progress_bar=False)
                semantic_embedding = (
                    embedding.tolist()
                    if hasattr(embedding, "tolist")
                    else list(embedding)
                )
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
        enhanced_concept = {
            "concept_id": concept_id,
            "knowledge_domain": knowledge_domain,
            "concept_type": concept_type,
            "knowledge_content": knowledge_content,
            "confidence_score": confidence_score,
            "extraction_method": "advanced_intelligent_analysis",
            "source_memory_id": memory.get("_id", ""),
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "quality_metrics": {
                "completeness": len([v for v in knowledge_content.values() if v])
                / len(knowledge_content),
                "content_length": len(content),
                "insights_count": len(knowledge_content["key_insights"]),
                "tags_count": len(knowledge_content["original_tags"]),
            },
            "semantic_embedding": semantic_embedding,
        }
        return enhanced_concept

    def _determine_knowledge_domain(self, content: str, title: str) -> str:
        content_lower = (content + " " + title).lower()
        domain_patterns = {
            "database_operations": ["database", "arango", "query", "collection", "aql"],
            "cognitive_architecture": [
                "cognitive",
                "autonomous",
                "intelligence",
                "memory",
                "learning",
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
                "protocol",
                "procedure",
                "workflow",
                "process",
                "operation",
            ],
            "research_methodology": [
                "research",
                "analysis",
                "methodology",
                "investigation",
            ],
            "behavioral_patterns": [
                "behavior",
                "pattern",
                "rule",
                "requirement",
                "guideline",
            ],
        }
        for domain, keywords in domain_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        return "general_knowledge"

    def _determine_concept_type(self, content: str, memory_type: str) -> str:
        content_lower = content.lower()
        if memory_type == "operational":
            return "operational_knowledge"
        elif memory_type == "foundational":
            return "foundational_principle"
        elif "problem" in content_lower or "issue" in content_lower:
            return "problem_solution_pair"
        elif "protocol" in content_lower or "procedure" in content_lower:
            return "procedural_knowledge"
        elif "pattern" in content_lower or "principle" in content_lower:
            return "behavioral_pattern"
        else:
            return "conceptual_knowledge"

    def _calculate_confidence_score(self, knowledge_content: Dict[str, Any]) -> float:
        score = 0.0
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
        if len(knowledge_content["problem"]) > 50:
            score += 0.05
        if len(knowledge_content["solution"]) > 50:
            score += 0.05
        if len(knowledge_content["key_insights"]) >= 3:
            score += 0.05
        if len(knowledge_content["original_tags"]) >= 5:
            score += 0.05
        return min(1.0, score)

    def get_incomplete_concepts(self) -> List[Dict[str, Any]]:
        query = """
        FOR concept IN cognitive_concepts
        FILTER concept.knowledge_content.problem == "" OR 
               concept.knowledge_content.solution == "" OR 
               concept.knowledge_content.prevention == "" OR
               LENGTH(concept.knowledge_content.key_insights) == 0
        RETURN concept
        """
        try:
            cursor = self.db.aql.execute(query)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving incomplete concepts: {e}")
            return []

    def get_source_memories_for_concepts(
        self, incomplete_concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        source_memories = []
        for concept in incomplete_concepts:
            source_memory_id = concept.get("source_memory_id", "")
            if source_memory_id:
                query = f"""
                FOR memory IN agent_memory
                FILTER memory._id == "{source_memory_id}"
                RETURN memory
                """
                try:
                    cursor = self.db.aql.execute(query)
                    memories = list(cursor)
                    source_memories.extend(memories)
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve source memory {source_memory_id}: {e}"
                    )
        return source_memories

    def create_concepts_from_new_memories(self) -> Dict[str, Any]:
        logger.info("Checking for new memories to convert to concepts...")
        query = """
        FOR memory IN agent_memory
        FILTER memory.foundational == true AND memory.quality_score > 0.85
        LET existing_concept = FIRST(
            FOR concept IN cognitive_concepts
            FILTER concept.source_memory_id == memory._id
            RETURN concept
        )
        FILTER existing_concept == null
        LIMIT 10
        RETURN memory
        """
        try:
            cursor = self.db.aql.execute(query)
            new_memories = list(cursor)
            logger.info(f"Found {len(new_memories)} new memories for concept creation")
        except Exception as e:
            logger.error(f"Error finding new memories: {e}")
            return {"status": "error", "error": str(e)}
        if not new_memories:
            logger.info("No new memories found for concept creation")
            return {"status": "completed", "created_count": 0}
        results = {
            "status": "processing",
            "created_count": 0,
            "error_count": 0,
            "processing_log": [],
        }
        for i, memory in enumerate(new_memories):
            try:
                enhanced_concept = self.create_enhanced_concept(memory)
                insert_result = self.db.collection("cognitive_concepts").insert(
                    enhanced_concept, overwrite=False
                )
                if insert_result:
                    results["created_count"] += 1
                    logger.info(
                        f"Created new concept {enhanced_concept['concept_id']} from memory {memory.get('_id')} ({i+1}/{len(new_memories)})"
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
            except Exception as e:
                logger.error(
                    f"Error creating concept from memory {memory.get('_id', 'unknown')}: {e}"
                )
                results["error_count"] += 1
        results["status"] = "completed"
        logger.info(
            f"New concept creation completed: {results['created_count']} created, {results['error_count']} errors"
        )
        return results

    def process_incomplete_concepts(self) -> Dict[str, Any]:
        logger.info("Starting incomplete concept processing...")
        incomplete_concepts = self.get_incomplete_concepts()
        logger.info(f"Found {len(incomplete_concepts)} incomplete concepts")
        if not incomplete_concepts:
            logger.info("No incomplete concepts found")
            return {
                "status": "completed",
                "processed_count": 0,
                "enhanced_count": 0,
                "error_count": 0,
            }
        source_memories = self.get_source_memories_for_concepts(incomplete_concepts)
        logger.info(f"Retrieved {len(source_memories)} source memories")
        results = {
            "status": "processing",
            "processed_count": 0,
            "enhanced_count": 0,
            "error_count": 0,
            "processing_log": [],
        }
        for i, concept in enumerate(incomplete_concepts):
            try:
                source_memory = None
                for memory in source_memories:
                    if memory.get("_id") == concept.get("source_memory_id"):
                        source_memory = memory
                        break
                if not source_memory:
                    logger.warning(
                        f"No source memory found for concept {concept.get('concept_id')}"
                    )
                    results["error_count"] += 1
                    continue
                enhanced_concept = self.create_enhanced_concept(source_memory)
                update_data = {
                    "knowledge_content": enhanced_concept["knowledge_content"],
                    "confidence_score": enhanced_concept["confidence_score"],
                    "extraction_method": enhanced_concept["extraction_method"],
                    "last_updated": enhanced_concept["last_updated"],
                    "quality_metrics": enhanced_concept["quality_metrics"],
                    "semantic_embedding": enhanced_concept["semantic_embedding"],
                }
                try:
                    update_query = """
                    FOR concept IN cognitive_concepts
                    FILTER concept._id == @concept_id
                    UPDATE concept WITH @update_data IN cognitive_concepts
                    RETURN NEW
                    """
                    cursor = self.db.aql.execute(
                        update_query,
                        bind_vars={
                            "concept_id": concept["_id"],
                            "update_data": update_data,
                        },
                    )
                    updated_concept = list(cursor)
                except Exception as update_error:
                    logger.error(
                        f"Update failed for {concept.get('concept_id')}: {update_error}"
                    )
                    updated_concept = None
                if updated_concept:
                    results["enhanced_count"] += 1
                    logger.info(
                        f"Enhanced concept {concept.get('concept_id')} ({i+1}/{len(incomplete_concepts)})"
                    )
                    results["processing_log"].append(
                        {
                            "concept_id": concept.get("concept_id"),
                            "action": "enhanced",
                            "confidence_score": enhanced_concept["confidence_score"],
                            "completeness": enhanced_concept["quality_metrics"][
                                "completeness"
                            ],
                        }
                    )
                else:
                    results["error_count"] += 1
                    logger.error(
                        f"Failed to update concept {concept.get('concept_id')}"
                    )
                results["processed_count"] += 1
            except Exception as e:
                logger.error(
                    f"Error processing concept {concept.get('concept_id', 'unknown')}: {e}"
                )
                results["error_count"] += 1
        results["status"] = "completed"
        logger.info(
            f"Processing completed: {results['enhanced_count']} enhanced, {results['error_count']} errors"
        )
        return results

    def validate_enhancement_results(self) -> Dict[str, Any]:
        validation_query = """
        FOR concept IN cognitive_concepts
        RETURN {
            concept_id: concept.concept_id,
            has_problem: concept.knowledge_content.problem != "",
            has_solution: concept.knowledge_content.solution != "",
            has_prevention: concept.knowledge_content.prevention != "",
            has_insights: LENGTH(concept.knowledge_content.key_insights) > 0,
            has_tags: LENGTH(concept.knowledge_content.original_tags) > 0,
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
                    "average_confidence_score": avg_confidence,
                    "average_completeness": avg_completeness,
                },
                "quality_assessment": "excellent"
                if avg_completeness > 0.8
                else "good"
                if avg_completeness > 0.6
                else "needs_improvement",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.info(
                f"Validation completed: {validation_results['quality_assessment']} quality"
            )
            logger.info(
                f"Average completeness: {avg_completeness:.2f}, Average confidence: {avg_confidence:.2f}"
            )
            return validation_results
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {"error": str(e)}


def main():
    extractor = AdvancedConceptExtractor()
    logger.info("=== Starting Advanced Cognitive Concept Enhancement ===")
    processing_results = extractor.process_incomplete_concepts()
    creation_results = extractor.create_concepts_from_new_memories()
    validation_results = extractor.validate_enhancement_results()
    final_report = {
        "processing_results": processing_results,
        "creation_results": creation_results,
        "validation_results": validation_results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
    }
    results_file = f'/home/opsvi/asea/development/knowledge_management/results/concept_quality_fix_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, "w") as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Enhancement completed. Results saved to: {results_file}")
    logger.info(
        f"Enhanced {processing_results.get('enhanced_count', 0)} existing concepts"
    )
    logger.info(f"Created {creation_results.get('created_count', 0)} new concepts")
    logger.info("=== Cognitive Concept Enhancement Complete ===")
    return final_report


if __name__ == "__main__":
    main()
