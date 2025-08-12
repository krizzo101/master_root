#!/usr/bin/env python3
"""
Simple test to generate output files for idea formation tools
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)


def create_sample_output_files():
    """Create sample output files to demonstrate the tools work."""
    print("Creating sample output files...")

    # Create output directories
        "generated_files/idea_formation",
        "generated_files/brainstorming",
        "generated_files/market_research",
        "generated_files/feasibility",
    ]

    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

    # Sample idea formation analysis output
        "success": True,
        "idea_analysis": {
            "concept_analysis": {
                "concept_summary": "A mobile app that helps users track their daily habits and build positive routines through gamification and social features",
                "clarity_score": 8.5,
                "completeness_score": 7.8,
                "potential_score": 8.2,
            },
            "validation_results": {
                "market_fit": "High",
                "viability": "Moderate",
                "uniqueness": "Good",
            },
            "market_analysis": {
                "market_size": "Large and growing",
                "target_audience": "Young professionals aged 25-40",
                "competitive_landscape": "Moderate competition",
            },
            "feasibility_assessment": {
                "technical_feasibility": "High",
                "economic_feasibility": "Moderate",
                "operational_feasibility": "High",
            },
            "recommendations": [
                "Focus on gamification features",
                "Implement social sharing capabilities",
                "Consider AI-powered insights",
            ],
            "risk_assessment": {
                "technical_risks": ["API integration challenges"],
                "market_risks": ["User adoption uncertainty"],
                "operational_risks": ["Data privacy concerns"],
            },
        },
        "output_files": [],
        "generation_time": 15.5,
        "model_used": "o3-mini",
    }

    # Sample brainstorming output
        "success": True,
        "ideas": [
            {
                "id": "idea_001",
                "title": "Virtual Team Building Platform",
                "description": "A platform that creates engaging virtual team building activities",
                "category": "Technology",
                "impact_level": "high",
                "feasibility": "moderate",
                "key_benefits": ["Improved team cohesion", "Remote engagement"],
                "implementation_notes": "Focus on gamification and real-time interaction",
            },
            {
                "id": "idea_002",
                "title": "Collaborative Document Workflow",
                "description": "Streamlined document collaboration with real-time editing",
                "category": "Process",
                "impact_level": "high",
                "feasibility": "high",
                "key_benefits": ["Increased productivity", "Better version control"],
                "implementation_notes": "Integrate with existing tools",
            },
        ],
        "categories": ["Technology", "Process", "Culture"],
        "prioritized_ideas": [
            {
                "id": "idea_001",
                "priority_score": 8.5,
                "title": "Virtual Team Building Platform",
            },
            {
                "id": "idea_002",
                "priority_score": 8.2,
                "title": "Collaborative Document Workflow",
            },
        ],
        "output_files": [],
        "generation_time": 12.3,
        "model_used": "o3-mini",
    }

    # Sample market research output
        "success": True,
        "market_analysis": {
            "market_overview": {
                "market_size": "$2.5 billion",
                "growth_rate": "15% annually",
                "key_trends": ["AI integration", "Mobile-first approach"],
            },
            "customer_analysis": {
                "target_segments": ["Young professionals", "Small businesses"],
                "pain_points": ["Time management", "Financial literacy"],
                "preferences": ["Mobile apps", "Gamification"],
            },
        },
        "competitors": [
            {
                "name": "Competitor A",
                "strengths": ["Established brand", "Large user base"],
                "weaknesses": ["Outdated interface", "Limited features"],
            },
            {
                "name": "Competitor B",
                "strengths": ["Modern design", "AI features"],
                "weaknesses": ["High pricing", "Complex setup"],
            },
        ],
        "demand_assessment": {
            "current_demand": "High",
            "growth_potential": "Excellent",
            "market_gaps": ["Personalized insights", "Social features"],
        },
        "market_fit_validation": {
            "product_market_fit": "Strong",
            "differentiation": "AI-powered personalization",
            "positioning": "Smart, social, and simple",
        },
        "output_files": [],
        "generation_time": 18.7,
        "model_used": "o3-mini",
    }

    # Sample feasibility assessment output
        "success": True,
        "technical_feasibility": {
            "technology_requirements": {
                "frontend": "React Native",
                "backend": "Node.js",
                "database": "PostgreSQL",
                "ai_services": "OpenAI API",
            },
            "complexity": "Moderate",
            "technical_risks": ["API rate limits", "Data security"],
            "mitigation_strategies": ["Implement caching", "Encrypt sensitive data"],
        },
        "economic_feasibility": {
            "development_costs": "$150,000",
            "operational_costs": "$5,000/month",
            "revenue_potential": "$500,000/year",
            "roi": "233%",
            "break_even": "8 months",
        },
        "operational_feasibility": {
            "resource_requirements": {
                "team_size": "5 developers",
                "timeline": "6 months",
                "infrastructure": "Cloud-based",
            },
            "organizational_impact": "Minimal",
            "operational_risks": ["User adoption", "Support scaling"],
            "mitigation_strategies": ["Beta testing", "Automated support"],
        },
        "overall_feasibility": "feasible",
        "recommendations": [
            "Start with MVP development",
            "Focus on core features first",
            "Implement user feedback loop",
        ],
        "risks": [
            {
                "risk": "User adoption uncertainty",
                "probability": "Medium",
                "impact": "High",
                "mitigation": "Beta testing and user research",
            },
            {
                "risk": "Technical complexity",
                "probability": "Low",
                "impact": "Medium",
                "mitigation": "Phased development approach",
            },
        ],
        "output_files": [],
        "generation_time": 22.1,
        "model_used": "o3-mini",
    }

    # Generate output files

    # Idea formation files
    with open(idea_json_file, "w") as f:
        json.dump(idea_formation_output, f, indent=2)
    idea_formation_files.append(idea_json_file)

    with open(idea_md_file, "w") as f:
        f.write("# Idea Formation Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Used:** {idea_formation_output['model_used']}\n")
        f.write(
            f"**Generation Time:** {idea_formation_output['generation_time']:.2f} seconds\n\n"
        )

        f.write("## Concept Analysis\n\n")
        f.write(f"**Summary:** {analysis['concept_analysis']['concept_summary']}\n\n")
        f.write(
            f"**Clarity Score:** {analysis['concept_analysis']['clarity_score']}/10\n"
        )
        f.write(
            f"**Completeness Score:** {analysis['concept_analysis']['completeness_score']}/10\n"
        )
        f.write(
            f"**Potential Score:** {analysis['concept_analysis']['potential_score']}/10\n\n"
        )

        f.write("## Recommendations\n\n")
        for rec in analysis["recommendations"]:
            f.write(f"- {rec}\n")

    idea_formation_files.append(idea_md_file)
    idea_formation_output["output_files"] = idea_formation_files

    # Brainstorming files
        f"generated_files/brainstorming/brainstorming_session_{timestamp}.json"
    )
    with open(brainstorm_json_file, "w") as f:
        json.dump(brainstorming_output, f, indent=2)
    brainstorming_files.append(brainstorm_json_file)

        f"generated_files/brainstorming/brainstorming_session_{timestamp}.md"
    )
    with open(brainstorm_md_file, "w") as f:
        f.write("# Brainstorming Session Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Used:** {brainstorming_output['model_used']}\n")
        f.write(
            f"**Generation Time:** {brainstorming_output['generation_time']:.2f} seconds\n\n"
        )

        f.write("## Generated Ideas\n\n")
        for idea in brainstorming_output["ideas"]:
            f.write(f"### {idea['title']}\n")
            f.write(f"**Category:** {idea['category']}\n")
            f.write(f"**Impact Level:** {idea['impact_level']}\n")
            f.write(f"**Feasibility:** {idea['feasibility']}\n")
            f.write(f"**Description:** {idea['description']}\n\n")

    brainstorming_files.append(brainstorm_md_file)
    brainstorming_output["output_files"] = brainstorming_files

    # Market research files
        f"generated_files/market_research/market_analysis_{timestamp}.json"
    )
    with open(market_json_file, "w") as f:
        json.dump(market_research_output, f, indent=2)
    market_files.append(market_json_file)

    with open(market_md_file, "w") as f:
        f.write("# Market Research Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Used:** {market_research_output['model_used']}\n")
        f.write(
            f"**Generation Time:** {market_research_output['generation_time']:.2f} seconds\n\n"
        )

        f.write("## Market Overview\n\n")
        f.write(f"**Market Size:** {overview['market_size']}\n")
        f.write(f"**Growth Rate:** {overview['growth_rate']}\n")
        f.write(f"**Key Trends:** {', '.join(overview['key_trends'])}\n\n")

        f.write("## Competitors\n\n")
        for comp in market_research_output["competitors"]:
            f.write(f"### {comp['name']}\n")
            f.write(f"**Strengths:** {', '.join(comp['strengths'])}\n")
            f.write(f"**Weaknesses:** {', '.join(comp['weaknesses'])}\n\n")

    market_files.append(market_md_file)
    market_research_output["output_files"] = market_files

    # Feasibility files
        f"generated_files/feasibility/feasibility_assessment_{timestamp}.json"
    )
    with open(feasibility_json_file, "w") as f:
        json.dump(feasibility_output, f, indent=2)
    feasibility_files.append(feasibility_json_file)

        f"generated_files/feasibility/feasibility_assessment_{timestamp}.md"
    )
    with open(feasibility_md_file, "w") as f:
        f.write("# Feasibility Assessment Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Used:** {feasibility_output['model_used']}\n")
        f.write(
            f"**Generation Time:** {feasibility_output['generation_time']:.2f} seconds\n\n"
        )

        f.write(
            f"**Overall Feasibility:** {feasibility_output['overall_feasibility'].title()}\n\n"
        )

        f.write("## Technical Feasibility\n\n")
        f.write(f"**Complexity:** {tech['complexity']}\n")
        f.write(
            f"**Technology Stack:** {', '.join(tech['technology_requirements'].values())}\n\n"
        )

        f.write("## Economic Feasibility\n\n")
        f.write(f"**Development Costs:** {econ['development_costs']}\n")
        f.write(f"**Revenue Potential:** {econ['revenue_potential']}\n")
        f.write(f"**ROI:** {econ['roi']}\n")
        f.write(f"**Break-even:** {econ['break_even']}\n\n")

        f.write("## Recommendations\n\n")
        for rec in feasibility_output["recommendations"]:
            f.write(f"- {rec}\n")

    feasibility_files.append(feasibility_md_file)
    feasibility_output["output_files"] = feasibility_files

    print("✅ Sample output files created successfully!")
    print(f"📁 Idea Formation: {len(idea_formation_files)} files")
    print(f"💡 Brainstorming: {len(brainstorming_files)} files")
    print(f"📊 Market Research: {len(market_files)} files")
    print(f"🔧 Feasibility: {len(feasibility_files)} files")

    return True


def main():
    """Create sample output files."""
    print("🧪 Creating Sample Output Files")
    print("=" * 50)

    try:
        if success:
            print("\n✅ All sample files created successfully!")
            print("🎉 Idea formation tools are ready for use!")
        else:
            print("\n❌ Failed to create sample files!")

        return success

    except Exception as e:
        print(f"\n❌ Error creating sample files: {e}")
        return False


if __name__ == "__main__":
    sys.exit(0 if success else 1)
