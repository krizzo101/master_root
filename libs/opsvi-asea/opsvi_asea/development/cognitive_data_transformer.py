#!/usr/bin/env python3
"""
Cognitive Data Transformer: Convert human-readable memories to machine-learnable semantic concepts
"""

import json
import re
from typing import Dict, List, Any, Tuple
import hashlib
from datetime import datetime


class CognitiveDataTransformer:
    """Transform text-based memories into semantic cognitive concepts"""

    def __init__(self):
        self.knowledge_domains = {
            "infrastructure": [
                "database",
                "connection",
                "path",
                "filesystem",
                "shell",
                "config",
            ],
            "behavioral": [
                "autonomy",
                "behavioral",
                "rule",
                "protocol",
                "enforcement",
                "validation",
            ],
            "cognitive": [
                "reasoning",
                "analysis",
                "decision",
                "learning",
                "intelligence",
                "meta",
            ],
            "operational": [
                "failure",
                "error",
                "success",
                "pattern",
                "workflow",
                "process",
            ],
            "research": [
                "research",
                "analysis",
                "synthesis",
                "knowledge",
                "discovery",
                "methodology",
            ],
            "technical": [
                "api",
                "tool",
                "implementation",
                "optimization",
                "performance",
                "system",
            ],
        }

        self.concept_types = {
            "failure_pattern": ["error", "failure", "problem", "issue", "bug"],
            "success_pattern": ["success", "solution", "fix", "resolution", "working"],
            "behavioral_rule": [
                "must",
                "never",
                "always",
                "mandatory",
                "required",
                "forbidden",
            ],
            "learning_insight": [
                "learned",
                "discovered",
                "realized",
                "found",
                "insight",
            ],
            "operational_protocol": [
                "protocol",
                "procedure",
                "workflow",
                "process",
                "method",
            ],
            "cognitive_capability": [
                "reasoning",
                "analysis",
                "intelligence",
                "cognitive",
                "meta",
            ],
        }

        self.relationship_indicators = {
            "causes": ["caused by", "due to", "because of", "resulted from"],
            "enables": ["enables", "allows", "permits", "facilitates"],
            "prevents": ["prevents", "stops", "blocks", "avoids"],
            "requires": ["requires", "needs", "depends on", "must have"],
            "contradicts": ["contradicts", "conflicts with", "opposes"],
            "builds_upon": ["builds on", "extends", "enhances", "improves"],
            "compounds_with": ["combined with", "together with", "along with"],
        }

    def extract_concepts_from_memory(
        self, memory: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract semantic concepts from a memory record"""
        concepts = []

        # Primary concept from the memory
        primary_concept = self._create_primary_concept(memory)
        concepts.append(primary_concept)

        # Extract additional concepts from content analysis
        additional_concepts = self._extract_additional_concepts(memory)
        concepts.extend(additional_concepts)

        return concepts

    def _create_primary_concept(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Create the primary concept from a memory"""
        content = memory.get("content", "")
        title = memory.get("title", "")
        tags = memory.get("tags", [])

        # Determine knowledge domain
        domain = self._classify_domain(content + " " + title, tags)

        # Determine concept type
        concept_type = self._classify_concept_type(content + " " + title)

        # Extract key information
        problem, solution, prevention = self._extract_problem_solution_prevention(
            content
        )

        # Generate concept ID
        concept_id = self._generate_concept_id(title, domain, concept_type)

        # Calculate confidence score
        confidence = self._calculate_confidence(memory)

        return {
            "_key": concept_id,
            "concept_id": concept_id,
            "semantic_embedding": None,  # Will be generated later with actual embedding API
            "knowledge_domain": domain,
            "concept_type": concept_type,
            "abstraction_level": self._determine_abstraction_level(content),
            "confidence_score": confidence,
            "evidence_strength": self._assess_evidence_strength(memory),
            "learning_context": {
                "original_memory_id": memory.get("_key"),
                "memory_tier": memory.get("tier"),
                "foundational": memory.get("foundational", False),
                "creation_date": memory.get("created"),
                "validation_method": "memory_migration",
            },
            "knowledge_content": {
                "title": title,
                "problem": problem,
                "solution": solution,
                "prevention": prevention,
                "key_insights": self._extract_key_insights(content),
                "original_tags": tags,
            },
            "created": datetime.utcnow().isoformat() + "Z",
            "last_validated": datetime.utcnow().isoformat() + "Z",
        }

    def _extract_additional_concepts(
        self, memory: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract additional concepts mentioned in the memory"""
        content = memory.get("content", "")
        additional_concepts = []

        # Look for mentioned technologies, tools, or systems
        tech_patterns = [
            r"python-arango",
            r"ArangoDB",
            r"HTTP \d+",
            r"shell commands?",
            r"absolute paths?",
            r"MCP tools?",
            r"rule \d+",
            r"validation",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 3:  # Avoid tiny matches
                    concept = self._create_tech_concept(match, memory)
                    if concept:
                        additional_concepts.append(concept)

        return additional_concepts[:3]  # Limit to avoid noise

    def _create_tech_concept(
        self, tech_term: str, memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a concept for a technology or tool mentioned"""
        concept_id = f"tech_{tech_term.lower().replace('-', '_').replace(' ', '_')}"

        return {
            "_key": concept_id,
            "concept_id": concept_id,
            "semantic_embedding": None,
            "knowledge_domain": "technical",
            "concept_type": "technology_reference",
            "abstraction_level": "operational",
            "confidence_score": 0.7,
            "evidence_strength": "medium",
            "learning_context": {
                "original_memory_id": memory.get("_key"),
                "extraction_method": "pattern_matching",
                "source_context": "technology_mention",
            },
            "knowledge_content": {
                "title": f"Technology: {tech_term}",
                "technology_name": tech_term,
                "usage_context": memory.get("title", ""),
                "domain_relevance": "infrastructure",
            },
            "created": datetime.utcnow().isoformat() + "Z",
            "last_validated": datetime.utcnow().isoformat() + "Z",
        }

    def _classify_domain(self, text: str, tags: List[str]) -> str:
        """Classify the knowledge domain of the content"""
        text_lower = text.lower()
        tag_text = " ".join(tags).lower()
        combined_text = text_lower + " " + tag_text

        domain_scores = {}
        for domain, keywords in self.knowledge_domains.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return "general"

    def _classify_concept_type(self, text: str) -> str:
        """Classify the type of concept"""
        text_lower = text.lower()

        type_scores = {}
        for concept_type, indicators in self.concept_types.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                type_scores[concept_type] = score

        if type_scores:
            return max(type_scores, key=type_scores.get)
        return "general_knowledge"

    def _extract_problem_solution_prevention(
        self, content: str
    ) -> Tuple[str, str, str]:
        """Extract problem, solution, and prevention from content"""
        # Simple pattern matching for now - could be enhanced with NLP
        problem = ""
        solution = ""
        prevention = ""

        # Look for problem indicators
        problem_patterns = [
            r"(?:problem|issue|error|failure)[:\s]+([^.]+)",
            r"(?:caused by|due to)[:\s]+([^.]+)",
            r"(?:root cause)[:\s]+([^.]+)",
        ]

        for pattern in problem_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                problem = match.group(1).strip()
                break

        # Look for solution indicators
        solution_patterns = [
            r"(?:solution|fix|resolution)[:\s]+([^.]+)",
            r"(?:solved by|fixed by)[:\s]+([^.]+)",
            r"(?:use|apply)[:\s]+([^.]+)",
        ]

        for pattern in solution_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                solution = match.group(1).strip()
                break

        # Look for prevention indicators
        prevention_patterns = [
            r"(?:prevent|avoid|stop)[:\s]+([^.]+)",
            r"(?:must|always|never)[:\s]+([^.]+)",
            r"(?:to prevent)[:\s]+([^.]+)",
        ]

        for pattern in prevention_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                prevention = match.group(1).strip()
                break

        return problem[:200], solution[:200], prevention[:200]  # Limit length

    def _extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content"""
        insights = []

        # Look for insight patterns
        insight_patterns = [
            r"(?:learned|discovered|realized|found)[:\s]+([^.]+)",
            r"(?:key insight|important)[:\s]+([^.]+)",
            r"(?:critical|essential)[:\s]+([^.]+)",
        ]

        for pattern in insight_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:  # Avoid tiny insights
                    insights.append(match.strip()[:150])  # Limit length

        return insights[:3]  # Limit to top insights

    def _generate_concept_id(self, title: str, domain: str, concept_type: str) -> str:
        """Generate a unique concept ID"""
        # Create a hash of the title for uniqueness
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"{domain}_{concept_type}_{title_hash}"

    def _calculate_confidence(self, memory: Dict[str, Any]) -> float:
        """Calculate confidence score for the concept"""
        base_confidence = 0.7

        # Boost confidence for foundational memories
        if memory.get("foundational"):
            base_confidence += 0.15

        # Boost confidence for essential tier
        if memory.get("tier") == "essential":
            base_confidence += 0.1

        # Boost confidence for validated memories
        if memory.get("validation_status") == "validated":
            base_confidence += 0.1

        # Boost confidence for behavioral requirements
        if memory.get("behavioral_requirement"):
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _assess_evidence_strength(self, memory: Dict[str, Any]) -> str:
        """Assess the strength of evidence for this concept"""
        evidence_indicators = 0

        if memory.get("foundational"):
            evidence_indicators += 1
        if memory.get("validation_status") == "validated":
            evidence_indicators += 1
        if memory.get("behavioral_requirement"):
            evidence_indicators += 1
        if memory.get("tier") == "essential":
            evidence_indicators += 1

        if evidence_indicators >= 3:
            return "high"
        elif evidence_indicators >= 2:
            return "medium"
        else:
            return "low"

    def _determine_abstraction_level(self, content: str) -> str:
        """Determine the abstraction level of the concept"""
        content_lower = content.lower()

        # Strategic level indicators
        strategic_indicators = [
            "framework",
            "architecture",
            "design",
            "strategy",
            "philosophy",
        ]
        if any(indicator in content_lower for indicator in strategic_indicators):
            return "strategic"

        # Tactical level indicators
        tactical_indicators = [
            "workflow",
            "process",
            "methodology",
            "approach",
            "pattern",
        ]
        if any(indicator in content_lower for indicator in tactical_indicators):
            return "tactical"

        # Default to operational
        return "operational"


def main():
    """Test the transformer with sample data"""
    transformer = CognitiveDataTransformer()

    # Sample memory for testing
    sample_memory = {
        "_key": "1590",
        "title": "Database Connection Issue Resolution - Complete Success",
        "content": "Fixed persistent HTTP 404 database connection errors for python-arango direct connections. Root cause: Incorrect default database name, missing password. Solution: Use absolute configuration with correct credentials.",
        "tags": [
            "database",
            "connectivity",
            "python-arango",
            "configuration",
            "validation",
        ],
        "tier": "essential",
        "foundational": True,
        "validation_status": "validated",
        "behavioral_requirement": True,
        "created": "2024-12-22T15:30:00Z",
    }

    concepts = transformer.extract_concepts_from_memory(sample_memory)

    print("Generated Concepts:")
    for concept in concepts:
        print(json.dumps(concept, indent=2))


if __name__ == "__main__":
    main()
