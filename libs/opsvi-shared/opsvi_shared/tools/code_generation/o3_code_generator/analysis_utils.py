"""
Analysis utilities for O3 Code Generator

This module provides helper functions for extracting data from various analysis
outputs, saving results for next steps, and managing the pipeline workflow.
"""

from datetime import datetime
import json
from pathlib import Path

from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)


def _ensure_output_directory() -> Path:
    """Ensure the output directory exists and return its path."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def extract_ideas_from_brainstorm_results(brainstorm_data: dict) -> dict:
    """Extract ideas from brainstorm results using cumulative pipeline context."""
    brainstorm_context = brainstorm_data["pipeline_context"]["brainstorm_results"]
    brainstorm_session = brainstorm_data["brainstorming_session"]

    generated_ideas = brainstorm_session["generated_ideas"]
    prioritized_ideas = brainstorm_session["prioritized_ideas"]
    problem_statement = brainstorm_context["problem_statement"]

    # If prioritized_ideas contains strings (IDs), look up the full objects
    if prioritized_ideas and isinstance(prioritized_ideas[0], str):
        ideas_by_id = {idea["id"]: idea for idea in generated_ideas}
        ideas = [ideas_by_id[idea_id] for idea_id in prioritized_ideas]
    else:
        ideas = prioritized_ideas

    top_ideas = ideas[:3]
    concept_descriptions = [
        f"{idea['title']}: {idea['description']}" for idea in top_ideas
    ]
    combined_description = "\n\n".join(concept_descriptions)

    return {
        "concept_description": combined_description,
        "analysis_type": "comprehensive",
        "include_market_research": True,
        "include_feasibility_assessment": True,
        "output_format": "json",
        "model": "o4-mini",
        "max_tokens": 16000,
        "additional_context": f"Original problem: {problem_statement}. These ideas were selected from a brainstorming session that generated {len(ideas)} total ideas.",
    }


def extract_market_research_data_from_idea_analysis(idea_analysis_data: dict) -> dict:
    """Extract market research data from idea analysis using cumulative pipeline context."""
    pipeline_context = idea_analysis_data["pipeline_context"]
    idea_analysis = idea_analysis_data["idea_analysis_results"]

    # Get original brainstorm context
    brainstorm_results = pipeline_context["brainstorm_results"]
    original_problem = brainstorm_results["problem_statement"]
    original_ideas = brainstorm_results["ideas"]

    # Get analysis results
    concept_description = idea_analysis["concept_description"]

    return {
        "product_concept": concept_description,
        "target_market": "Programming education market",
        "include_competitor_analysis": True,
        "include_demand_assessment": True,
        "include_market_fit_validation": True,
        "output_format": "json",
        "model": "o4-mini",
        "max_tokens": 16000,
        "additional_context": f"Original problem: {original_problem}. Based on analysis of {len(original_ideas)} brainstormed ideas. Concept: {concept_description}",
    }


def extract_feasibility_data_from_market_research(market_research_data: dict) -> dict:
    market_summary = market_research_data.get("market_research_summary", {})
    return {
        "concept_description": market_summary.get("product_concept", ""),
        "include_technical_feasibility": True,
        "include_economic_feasibility": True,
        "include_operational_feasibility": True,
        "budget_constraints": None,
        "timeline_constraints": None,
        "output_format": "json",
        "model": "o4-mini",
        "max_tokens": 16000,
        "additional_context": f"Based on market research with {len(market_summary.get('competitors', []))} competitors identified",
        "source_market_research": market_research_data,
    }


def extract_requirements_data_from_feasibility_assessment(
    feasibility_data: dict,
) -> dict:
    """Extract requirements data from feasibility assessment using full pipeline context."""
    pipeline_context = feasibility_data["pipeline_context"]
    feasibility_summary = feasibility_data["feasibility_assessment_summary"]

    # Get full pipeline context
    brainstorm_results = pipeline_context["brainstorm_results"]
    idea_analysis = pipeline_context["idea_analysis_results"]
    market_research = pipeline_context.get("market_research_results", {})

    # Build comprehensive requirements text from full pipeline
    original_problem = brainstorm_results["problem_statement"]
    original_ideas = brainstorm_results["ideas"]
    concept_description = idea_analysis["concept_description"]

    requirements_text = f"""
PROJECT: {concept_description}

ORIGINAL PROBLEM STATEMENT: {original_problem}

BRAINSTORMED IDEAS:
{chr(10).join([f"- {idea['title']}: {idea['description']}" for idea in original_ideas[:5]])}

FEASIBILITY ASSESSMENT:
- Overall Feasibility: {feasibility_summary['overall_feasibility']}
- Technical Feasibility: {feasibility_summary['technical_feasibility']['technical_score']}
- Economic Feasibility: {feasibility_summary['economic_feasibility']['economic_score']}
- Operational Feasibility: {feasibility_summary['operational_feasibility']['operational_score']}

MARKET CONTEXT:
{market_research.get('market_summary', 'Market research data available in pipeline context')}

Generate detailed requirements specification including user stories, technical requirements, and acceptance criteria.
""".strip()

    return {
        "requirements_text": requirements_text,
        "analysis_type": "comprehensive",
        "output_format": "json",
        "include_user_stories": True,
        "include_acceptance_criteria": True,
        "include_technical_specs": True,
        "model": "o4-mini",
        "max_tokens": 16000,
        "temperature": 0.1,
    }


def save_requirements_results_for_next_step(out, source: str | None) -> str:
    """Save requirements analysis results with cumulative pipeline context."""
    # Extract pipeline context from source data
    source_data = (
        UniversalInputLoader().load_file_by_extension(source) if source else {}
    )
    pipeline_context = source_data.get("pipeline_context", {})

    next_step_data = {
        "current_step": "requirements_analysis",
        "requirements_specification": {
            "project_name": "Python Learning Platform",
            "project_description": f"Requirements analysis from {source or 'unknown source'}",
            "functional_requirements": out.functional_requirements,
            "non_functional_requirements": out.non_functional_requirements,
            "user_stories": out.user_stories,
            "dependencies": out.dependencies,
            "constraints": out.constraints,
            "acceptance_criteria": out.acceptance_criteria,
        },
        "specification_metadata": {
            "generation_time": out.generation_time,
            "model_used": out.model_used,
            "output_files": out.output_files,
            "specification_type": "requirements",
            "timestamp": datetime.now().isoformat(),
        },
        "pipeline_context": {
            **pipeline_context,  # Preserve all previous context
            "requirements_results": {
                "user_stories": out.user_stories,
                "dependencies": out.dependencies,
                "functional_requirements": out.functional_requirements,
                "non_functional_requirements": out.non_functional_requirements,
                "acceptance_criteria": out.acceptance_criteria,
            },
        },
        "next_steps": {
            "recommended_actions": ["architecture-design"],
            "priority": "high",
            "description": "Design system architecture based on requirements specification",
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"requirements_specification_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def save_feasibility_results_for_next_step(out, source: str | None) -> str:
    """Save feasibility assessment results with cumulative pipeline context."""
    # Extract pipeline context from source data
    source_data = (
        UniversalInputLoader().load_file_by_extension(source) if source else {}
    )
    pipeline_context = source_data.get("pipeline_context", {})

    # Extract concept description from pipeline context
    concept_description = ""
    if "idea_analysis_results" in pipeline_context:
        concept_description = pipeline_context["idea_analysis_results"].get(
            "concept_description", ""
        )

    next_step_data = {
        "current_step": "feasibility_assessment",
        "feasibility_assessment_summary": {
            "concept_description": concept_description,
            "overall_feasibility": out.overall_feasibility,
            "technical_feasibility": out.technical_feasibility,
            "economic_feasibility": out.economic_feasibility,
            "operational_feasibility": out.operational_feasibility,
            "recommendations": out.recommendations,
            "risks": out.risks,
        },
        "assessment_metadata": {
            "generation_time": out.generation_time,
            "model_used": out.model_used,
            "output_files": out.output_files,
            "assessment_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
        },
        "pipeline_context": {
            **pipeline_context,  # Preserve all previous context
            "feasibility_results": {
                "overall_feasibility": out.overall_feasibility,
                "technical_score": out.technical_feasibility.get("technical_score", 0),
                "economic_score": out.economic_feasibility.get("economic_score", 0),
                "operational_score": out.operational_feasibility.get(
                    "operational_score", 0
                ),
                "recommendations": out.recommendations,
                "risks": out.risks,
            },
        },
        "next_steps": {
            "recommended_actions": ["requirements-analyze"],
            "priority": "high",
            "description": "Define detailed requirements based on feasibility assessment",
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feasibility_assessment_results_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def group_ideas_by_category(ideas: list[dict]) -> dict:
    grouped = {}
    for idea in ideas:
        category = idea.get("category", "General")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(idea)
    return grouped


def suggest_analysis_focus(ideas: list[dict]) -> dict:
    if not ideas:
        return {"focus": "general", "reason": "No ideas generated"}
    high_impact = len([i for i in ideas if i.get("impact") == "High"])
    high_feasibility = len([i for i in ideas if i.get("feasibility") == "High"])
    categories = {}
    for idea in ideas:
        category = idea.get("category", "General")
        categories[category] = categories.get(category, 0) + 1
    if high_impact >= 3 and high_feasibility >= 3:
        focus = "high_potential"
        reason = f"Found {high_impact} high-impact and {high_feasibility} high-feasibility ideas"
    elif high_impact >= 2:
        focus = "impact_optimization"
        reason = (
            f"Found {high_impact} high-impact ideas - focus on feasibility improvements"
        )
    elif high_feasibility >= 2:
        focus = "feasibility_optimization"
        reason = f"Found {high_feasibility} high-feasibility ideas - focus on impact improvements"
    else:
        focus = "idea_refinement"
        reason = "Ideas need refinement for better impact and feasibility balance"
    return {
        "focus": focus,
        "reason": reason,
        "category_distribution": categories,
        "recommended_approach": get_recommended_approach(focus),
    }


def get_recommended_approach(focus: str) -> str:
    approaches = {
        "high_potential": "Comprehensive analysis with market research and feasibility assessment",
        "impact_optimization": "Focus on technical feasibility and implementation planning",
        "feasibility_optimization": "Focus on market validation and impact enhancement",
        "idea_refinement": "Iterative brainstorming with more specific problem focus",
    }
    return approaches.get(focus, "Standard comprehensive analysis")


def save_assistant_brainstorm_results(ideas_data: dict, source: str | None) -> str:
    next_step_data = {
        "brainstorming_session": {
            "problem_statement": source or "Brainstorming session",
            "generated_ideas": ideas_data.get("ideas", []),
            "categories": ideas_data.get("categories", []),
            "prioritized_ideas": ideas_data.get("prioritized_ideas", []),
            "total_ideas_generated": len(ideas_data.get("ideas", [])),
            "ideas_by_category": group_ideas_by_category(ideas_data.get("ideas", [])),
            "top_ideas": ideas_data.get("prioritized_ideas", [])[:5],
            "conversation_summary": ideas_data.get("summary", ""),
            "recommended_next_steps": ["idea-analyze"],
        },
        "session_metadata": {
            "generation_time": 0.0,
            "model_used": "gpt-4.1",
            "session_type": "assistant_brainstorming",
            "timestamp": datetime.now().isoformat(),
            "quality_metrics": {
                "idea_diversity": len(ideas_data.get("categories", [])),
                "high_impact_ideas": len(
                    [
                        i
                        for i in ideas_data.get("ideas", [])
                        if i.get("impact") == "High"
                    ]
                ),
                "high_feasibility_ideas": len(
                    [
                        i
                        for i in ideas_data.get("ideas", [])
                        if i.get("feasibility") == "High"
                    ]
                ),
            },
        },
        "next_steps": {
            "recommended_actions": ["idea-analyze"],
            "priority": "high",
            "description": "Select and analyze the best ideas from assistant brainstorming",
            "suggested_analysis": suggest_analysis_focus(ideas_data.get("ideas", [])),
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"assistant_brainstorm_results_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def save_text_brainstorm_results(response_content: str, source: str | None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"brainstorm_results_{timestamp}.txt"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        f.write(f"Problem Statement: {source}\n\n")
        f.write("Assistant Response:\n")
        f.write(response_content)
    return str(filepath)


def save_market_research_results_for_next_step(out, source: str | None) -> str:
    """Save market research results with cumulative pipeline context."""
    # Extract pipeline context from source data
    source_data = (
        UniversalInputLoader().load_file_by_extension(source) if source else {}
    )
    pipeline_context = source_data.get("pipeline_context", {})

    # Extract concept description from pipeline context
    concept_description = ""
    if "idea_analysis_results" in pipeline_context:
        concept_description = pipeline_context["idea_analysis_results"].get(
            "concept_description", ""
        )

    next_step_data = {
        "current_step": "market_research",
        "market_research_results": {
            "product_concept": concept_description,
            "target_market": "Programming education market",
            "market_analysis": out.market_analysis,
            "competitor_analysis": out.competitors,
            "demand_assessment": out.demand_assessment,
            "market_fit_validation": out.market_fit_validation,
            "recommended_next_steps": ["feasibility-assess"],
        },
        "research_metadata": {
            "generation_time": out.generation_time,
            "model_used": out.model_used,
            "output_files": out.output_files,
            "research_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
        },
        "pipeline_context": {
            **pipeline_context,  # Preserve all previous context
            "market_research_results": {
                "market_analysis": out.market_analysis,
                "competitors": out.competitors,
                "demand_assessment": out.demand_assessment,
                "market_summary": f"Market research for {concept_description} in Programming education market",
            },
        },
        "next_steps": {
            "recommended_actions": ["feasibility-assess"],
            "priority": "high",
            "description": "Assess technical, economic, and operational feasibility based on market research",
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_research_results_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def save_brainstorm_results_for_next_step(out, source: str | None) -> str:
    next_step_data = {
        "current_step": "brainstorm",
        "brainstorming_session": {
            "problem_statement": source or "Brainstorming session",
            "generated_ideas": out.ideas,
            "categories": out.categories,
            "prioritized_ideas": out.prioritized_ideas,
            "total_ideas_generated": len(out.ideas),
            "ideas_by_category": group_ideas_by_category(out.ideas),
            "top_ideas": out.prioritized_ideas[:5] if out.prioritized_ideas else [],
            "recommended_next_steps": ["idea-analyze"],
        },
        "session_metadata": {
            "generation_time": out.generation_time,
            "model_used": out.model_used,
            "output_files": out.output_files,
            "session_type": "enhanced_brainstorming",
            "timestamp": datetime.now().isoformat(),
            "quality_metrics": {
                "idea_diversity": len(out.categories),
                "high_impact_ideas": len(
                    [i for i in out.ideas if i.get("impact") == "High"]
                ),
                "high_feasibility_ideas": len(
                    [i for i in out.ideas if i.get("feasibility") == "High"]
                ),
            },
        },
        "pipeline_context": {
            "brainstorm_results": {
                "problem_statement": source or "Brainstorming session",
                "ideas": out.ideas,
                "categories": out.categories,
                "prioritized_ideas": out.prioritized_ideas,
            }
        },
        "next_steps": {
            "recommended_actions": ["idea-analyze"],
            "priority": "high",
            "description": "Select and analyze the best ideas from enhanced brainstorming",
            "suggested_analysis": {
                "focus": "general" if len(out.ideas) > 0 else "general",
                "reason": (
                    f"{len(out.ideas)} ideas generated"
                    if len(out.ideas) > 0
                    else "No ideas generated"
                ),
            },
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"brainstorm_results_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def save_analysis_results_for_next_step(out, source) -> str:
    # Extract pipeline context from source if available
    pipeline_context = {}
    if isinstance(source, dict) and "pipeline_context" in source:
        pipeline_context = source["pipeline_context"]
    elif isinstance(source, str):
        # If source is a filename, load it to get the context
        try:
            source_data = UniversalInputLoader().load_file_by_extension(source)
            if "pipeline_context" in source_data:
                pipeline_context = source_data["pipeline_context"]
        except Exception:
            pass  # Continue without context if file can't be loaded

    # Extract concept description from the analysis results
    concept_analysis = out.idea_analysis.get("concept_analysis", {})
    concept_description = concept_analysis.get("concept_summary", "")
    if not concept_description:
        # Try to build from brainstorm context if available
        if pipeline_context and "brainstorm_results" in pipeline_context:
            brainstorm_ideas = pipeline_context["brainstorm_results"]["ideas"][:3]
            concept_descriptions = [
                f"{idea['title']}: {idea['description']}" for idea in brainstorm_ideas
            ]
            concept_description = "\n\n".join(concept_descriptions)

    next_step_data = {
        "current_step": "idea_analysis",
        "idea_analysis_results": {
            "concept_description": concept_description,
            "analysis_type": "comprehensive",
            "idea_analysis": out.idea_analysis,
            "recommended_next_steps": ["market-research", "feasibility-assess"],
        },
        "analysis_metadata": {
            "generation_time": out.generation_time,
            "model_used": out.model_used,
            "output_files": out.output_files,
            "analysis_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
        },
        "pipeline_context": {
            **pipeline_context,  # Preserve all previous context
            "idea_analysis_results": {
                "concept_description": concept_description,
                "analysis_scores": out.idea_analysis,
                "recommendations": out.idea_analysis.get("recommendations", []),
            },
        },
        "next_steps": {
            "recommended_actions": ["market-research"],
            "priority": "high",
            "description": "Conduct market research based on analyzed ideas",
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"idea_analysis_results_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(next_step_data, f, indent=2)
    return str(filepath)


def save_interactive_input(input_data: dict, prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_conversation_input_{timestamp}.json"
    output_dir = _ensure_output_directory()
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(input_data, f, indent=2)
    return str(filepath)
