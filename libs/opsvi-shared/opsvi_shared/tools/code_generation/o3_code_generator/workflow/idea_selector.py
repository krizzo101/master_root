"""
Best Idea Selection Algorithm

Automatically selects the optimal idea from brainstorm results based on
multiple scoring criteria including feasibility, impact, and alignment.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple


class BestIdeaSelector:
    """
    Intelligent algorithm for automatically selecting the best idea from brainstorm results.

    Uses a multi-criteria scoring system that considers:
    - Feasibility (ease of implementation)
    - Impact (potential value and reach)
    - Novelty (innovation and uniqueness)
    - Alignment (match with original problem)
    - Clarity (how well-defined the idea is)
    """

    def __init__(self):
        """Initialize the idea selector."""
        self.logger = logging.getLogger(__name__)

        # Scoring weights for different criteria
        self.criteria_weights = {
            "feasibility": 0.25,  # 25% - Can it be built?
            "impact": 0.30,  # 30% - Will it make a difference?
            "novelty": 0.15,  # 15% - Is it innovative?
            "alignment": 0.20,  # 20% - Does it solve the problem?
            "clarity": 0.10,  # 10% - Is it well-defined?
        }

    def select_best_idea(
        self,
        brainstorm_results: Dict[str, Any],
        original_problem: str,
        selection_criteria: Optional[Dict[str, float]] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Select the best idea from brainstorm results.

        Args:
            brainstorm_results: Results from brainstorm step
            original_problem: The original problem statement
            selection_criteria: Optional custom weights for criteria

        Returns:
            Tuple of (selected_idea, selection_rationale)
        """
        ideas = brainstorm_results.get("ideas", [])
        if not ideas:
            raise ValueError("No ideas found in brainstorm results")

        # Use custom criteria if provided
        if selection_criteria:
            self.criteria_weights.update(selection_criteria)

        self.logger.info(f"Evaluating {len(ideas)} ideas for optimal selection")

        # Score all ideas
        scored_ideas = []
        for idea in ideas:
            score_breakdown = self._score_idea(idea, original_problem)
            total_score = sum(
                score_breakdown[criterion] * weight
                for criterion, weight in self.criteria_weights.items()
            )

            scored_ideas.append(
                {
                    "idea": idea,
                    "total_score": total_score,
                    "score_breakdown": score_breakdown,
                }
            )

        # Sort by total score (descending)
        scored_ideas.sort(key=lambda x: x["total_score"], reverse=True)

        # Select the best idea
        best_idea_entry = scored_ideas[0]
        best_idea = best_idea_entry["idea"]

        # Generate selection rationale
        rationale = self._generate_selection_rationale(
            best_idea_entry, scored_ideas, original_problem
        )

        self.logger.info(
            f"Selected idea: '{best_idea.get('title', 'Untitled')}' with score {best_idea_entry['total_score']:.2f}"
        )

        return best_idea, rationale

    def _score_idea(
        self, idea: Dict[str, Any], original_problem: str
    ) -> Dict[str, float]:
        """
        Score an individual idea across all criteria.

        Args:
            idea: The idea to score
            original_problem: Original problem statement for alignment scoring

        Returns:
            Dictionary of scores for each criterion (0.0 to 1.0)
        """
        return {
            "feasibility": self._score_feasibility(idea),
            "impact": self._score_impact(idea),
            "novelty": self._score_novelty(idea),
            "alignment": self._score_alignment(idea, original_problem),
            "clarity": self._score_clarity(idea),
        }

    def _score_feasibility(self, idea: Dict[str, Any]) -> float:
        """
        Score the feasibility of implementing the idea.

        Considers:
        - Implementation complexity
        - Resource requirements
        - Technical difficulty
        - Timeline feasibility
        """
        score = 0.5  # Base score

        # Check if idea has feasibility indicators
        feasibility_text = idea.get("feasibility", "").lower()
        implementation_notes = idea.get("implementation_notes", "").lower()
        description = idea.get("description", "").lower()

        # Positive feasibility indicators
        positive_indicators = [
            "simple",
            "easy",
            "straightforward",
            "quick",
            "minimal",
            "existing",
            "standard",
            "proven",
            "available",
            "ready",
            "basic",
            "common",
        ]

        # Negative feasibility indicators
        negative_indicators = [
            "complex",
            "difficult",
            "challenging",
            "expensive",
            "time-consuming",
            "advanced",
            "novel",
            "cutting-edge",
            "research",
            "experimental",
            "requires",
            "needs",
            "depends",
            "custom",
            "proprietary",
        ]

        combined_text = f"{feasibility_text} {implementation_notes} {description}"

        # Count positive and negative indicators
        positive_count = sum(
            1 for indicator in positive_indicators if indicator in combined_text
        )
        negative_count = sum(
            1 for indicator in negative_indicators if indicator in combined_text
        )

        # Adjust score based on indicators
        score += (positive_count * 0.1) - (negative_count * 0.1)

        # Check explicit feasibility rating
        if "high" in feasibility_text or "easy" in feasibility_text:
            score += 0.3
        elif "medium" in feasibility_text or "moderate" in feasibility_text:
            score += 0.1
        elif "low" in feasibility_text or "difficult" in feasibility_text:
            score -= 0.2

        # Check for specific implementation details (indicates more feasible)
        if len(implementation_notes) > 50:  # Detailed implementation notes
            score += 0.2

        return max(0.0, min(1.0, score))

    def _score_impact(self, idea: Dict[str, Any]) -> float:
        """
        Score the potential impact of the idea.

        Considers:
        - User value
        - Market potential
        - Problem-solving effectiveness
        - Scalability
        """
        score = 0.5  # Base score

        impact_text = idea.get("impact", "").lower()
        description = idea.get("description", "").lower()
        title = idea.get("title", "").lower()

        # High impact indicators
        high_impact_indicators = [
            "revolutionary",
            "game-changing",
            "significant",
            "major",
            "substantial",
            "widespread",
            "scalable",
            "transformative",
            "breakthrough",
            "disruptive",
            "efficiency",
            "automation",
            "optimization",
            "users",
            "market",
            "revenue",
        ]

        # Low impact indicators
        low_impact_indicators = [
            "minor",
            "small",
            "limited",
            "niche",
            "specific",
            "narrow",
            "incremental",
            "marginal",
            "cosmetic",
            "superficial",
        ]

        combined_text = f"{impact_text} {description} {title}"

        # Count impact indicators
        high_count = sum(
            1 for indicator in high_impact_indicators if indicator in combined_text
        )
        low_count = sum(
            1 for indicator in low_impact_indicators if indicator in combined_text
        )

        # Adjust score based on indicators
        score += (high_count * 0.08) - (low_count * 0.1)

        # Check explicit impact rating
        if "high" in impact_text:
            score += 0.3
        elif "medium" in impact_text or "moderate" in impact_text:
            score += 0.1
        elif "low" in impact_text:
            score -= 0.2

        # Longer descriptions often indicate more impactful ideas
        if len(description) > 100:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_novelty(self, idea: Dict[str, Any]) -> float:
        """
        Score the novelty and innovation of the idea.

        Considers:
        - Uniqueness
        - Innovation level
        - Creative approach
        - Differentiation
        """
        score = 0.5  # Base score

        description = idea.get("description", "").lower()
        title = idea.get("title", "").lower()
        category = idea.get("category", "").lower()

        # Novelty indicators
        novelty_indicators = [
            "innovative",
            "novel",
            "unique",
            "creative",
            "original",
            "new",
            "cutting-edge",
            "advanced",
            "pioneering",
            "breakthrough",
            "ai",
            "machine learning",
            "blockchain",
            "vr",
            "ar",
            "automation",
            "intelligent",
            "smart",
            "adaptive",
            "personalized",
        ]

        # Common/standard indicators
        standard_indicators = [
            "standard",
            "typical",
            "common",
            "basic",
            "simple",
            "traditional",
            "conventional",
            "usual",
            "regular",
            "ordinary",
            "existing",
        ]

        combined_text = f"{description} {title} {category}"

        # Count novelty indicators
        novelty_count = sum(
            1 for indicator in novelty_indicators if indicator in combined_text
        )
        standard_count = sum(
            1 for indicator in standard_indicators if indicator in combined_text
        )

        # Adjust score based on indicators
        score += (novelty_count * 0.1) - (standard_count * 0.1)

        # Check for technology-specific keywords that indicate innovation
        tech_keywords = ["ai", "ml", "api", "cloud", "mobile", "web", "platform"]
        tech_count = sum(1 for keyword in tech_keywords if keyword in combined_text)
        score += tech_count * 0.05

        return max(0.0, min(1.0, score))

    def _score_alignment(self, idea: Dict[str, Any], original_problem: str) -> float:
        """
        Score how well the idea aligns with the original problem.

        Uses keyword matching and semantic similarity to determine alignment.
        """
        score = 0.5  # Base score

        description = idea.get("description", "").lower()
        title = idea.get("title", "").lower()
        problem_lower = original_problem.lower()

        # Extract key words from problem statement
        problem_words = set(
            word.strip(".,!?()[]{}") for word in problem_lower.split() if len(word) > 3
        )

        # Extract key words from idea
        idea_text = f"{title} {description}"
        idea_words = set(
            word.strip(".,!?()[]{}") for word in idea_text.split() if len(word) > 3
        )

        # Calculate word overlap
        if problem_words:
            overlap = len(problem_words.intersection(idea_words))
            overlap_ratio = overlap / len(problem_words)
            score += overlap_ratio * 0.4

        # Check for direct problem addressing
        problem_keywords = ["solve", "address", "fix", "improve", "enhance", "optimize"]
        if any(keyword in description for keyword in problem_keywords):
            score += 0.2

        # Bonus for explicitly mentioning problem domain
        if any(word in idea_text for word in problem_words if len(word) > 5):
            score += 0.2

        return max(0.0, min(1.0, score))

    def _score_clarity(self, idea: Dict[str, Any]) -> float:
        """
        Score how clearly defined and detailed the idea is.

        Considers:
        - Description completeness
        - Implementation detail
        - Specificity
        - Structure
        """
        score = 0.5  # Base score

        title = idea.get("title", "")
        description = idea.get("description", "")
        implementation_notes = idea.get("implementation_notes", "")
        category = idea.get("category", "")

        # Score based on completeness
        if title and len(title) > 10:
            score += 0.1
        if description and len(description) > 50:
            score += 0.2
        if implementation_notes and len(implementation_notes) > 30:
            score += 0.2
        if category and len(category) > 3:
            score += 0.1

        # Check for specific details
        specific_indicators = [
            "step",
            "process",
            "method",
            "approach",
            "system",
            "feature",
            "component",
            "module",
            "interface",
            "database",
            "api",
            "user",
        ]

        combined_text = f"{description} {implementation_notes}".lower()
        specific_count = sum(
            1 for indicator in specific_indicators if indicator in combined_text
        )
        score += min(specific_count * 0.05, 0.2)

        return max(0.0, min(1.0, score))

    def _generate_selection_rationale(
        self,
        best_idea_entry: Dict[str, Any],
        all_scored_ideas: List[Dict[str, Any]],
        original_problem: str,
    ) -> str:
        """
        Generate a human-readable rationale for why this idea was selected.

        Args:
            best_idea_entry: The selected best idea with scores
            all_scored_ideas: All ideas with their scores
            original_problem: Original problem statement

        Returns:
            Detailed rationale string
        """
        best_idea = best_idea_entry["idea"]
        best_score = best_idea_entry["total_score"]
        best_breakdown = best_idea_entry["score_breakdown"]

        # Find the strongest criteria for this idea
        sorted_criteria = sorted(
            best_breakdown.items(),
            key=lambda x: x[1] * self.criteria_weights[x[0]],
            reverse=True,
        )

        top_criterion = sorted_criteria[0][0]
        top_score = sorted_criteria[0][1]

        # Compare with other ideas
        num_ideas = len(all_scored_ideas)
        score_margin = (
            best_score - all_scored_ideas[1]["total_score"] if num_ideas > 1 else 0
        )

        rationale_parts = [
            f"Selected '{best_idea.get('title', 'Untitled')}' as the optimal solution for '{original_problem}'.",
            f"",
            f"Selection Score: {best_score:.2f} out of 1.0",
            f"Evaluated against {num_ideas} total ideas"
            + (
                f" with a {score_margin:.2f} point margin over the next best option."
                if score_margin > 0
                else "."
            ),
            f"",
            f"Key Strengths:",
        ]

        # Add top scoring criteria
        for criterion, score in sorted_criteria[:3]:
            criterion_name = criterion.replace("_", " ").title()
            weighted_contribution = score * self.criteria_weights[criterion]
            rationale_parts.append(
                f"• {criterion_name}: {score:.2f} (weighted contribution: {weighted_contribution:.2f})"
            )

        # Add specific reasons based on top criterion
        rationale_parts.append(f"")
        rationale_parts.append(f"Primary Selection Factors:")

        if top_criterion == "feasibility":
            rationale_parts.append(
                "• High implementation feasibility with clear technical path"
            )
            rationale_parts.append(
                "• Minimal resource requirements and reasonable complexity"
            )
        elif top_criterion == "impact":
            rationale_parts.append("• Significant potential value and user benefit")
            rationale_parts.append(
                "• Strong market opportunity and scalability potential"
            )
        elif top_criterion == "alignment":
            rationale_parts.append("• Direct alignment with the core problem statement")
            rationale_parts.append("• Clear addressing of identified user needs")
        elif top_criterion == "novelty":
            rationale_parts.append(
                "• Innovative approach with competitive differentiation"
            )
            rationale_parts.append("• Creative solution leveraging modern technologies")
        elif top_criterion == "clarity":
            rationale_parts.append(
                "• Well-defined concept with clear implementation path"
            )
            rationale_parts.append("• Detailed specifications and structured approach")

        # Add idea description
        if best_idea.get("description"):
            rationale_parts.extend(
                [
                    f"",
                    f"Idea Description:",
                    f"{best_idea['description']}",
                ]
            )

        return "\n".join(rationale_parts)

    def compare_ideas(
        self, ideas: List[Dict[str, Any]], original_problem: str
    ) -> List[Dict[str, Any]]:
        """
        Compare and rank all ideas with detailed scoring.

        Args:
            ideas: List of ideas to compare
            original_problem: Original problem statement

        Returns:
            List of ideas with scores, sorted by total score
        """
        scored_ideas = []

        for idea in ideas:
            score_breakdown = self._score_idea(idea, original_problem)
            total_score = sum(
                score_breakdown[criterion] * weight
                for criterion, weight in self.criteria_weights.items()
            )

            scored_ideas.append(
                {
                    "idea": idea,
                    "total_score": total_score,
                    "score_breakdown": score_breakdown,
                    "rank": 0,  # Will be set after sorting
                }
            )

        # Sort by total score and assign ranks
        scored_ideas.sort(key=lambda x: x["total_score"], reverse=True)
        for i, scored_idea in enumerate(scored_ideas):
            scored_idea["rank"] = i + 1

        return scored_ideas
