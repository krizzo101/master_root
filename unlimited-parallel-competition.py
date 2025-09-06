#!/usr/bin/env python3
"""
UNLIMITED PARALLEL RESEARCH COMPETITION
True 15-agent parallelism test - all agents run simultaneously
Enhanced challenge with no artificial limits
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def create_unlimited_competition():
    """15 agents in true parallel execution - the ultimate orchestration test"""

    # Generate session IDs for tracking
    session_ids = {
        "alpha": str(uuid.uuid4()),
        "beta": str(uuid.uuid4()),
        "gamma": str(uuid.uuid4()),
        "delta": str(uuid.uuid4()),
        "epsilon": str(uuid.uuid4()),
        "competition": str(uuid.uuid4()),
    }

    # Production-grade MCP documentation and patterns
    mcp_docs = f"""
=== PRODUCTION CLAUDE CODE ORCHESTRATION REFERENCE ===

SESSION TRACKING:
Your team session ID: {{team_session}}
Competition ID: {session_ids['competition']}
Monitor: tail -f ~/.claude/projects/*/$SESSION_ID.jsonl

PERFORMANCE-OPTIMIZED MCP TOOLS:
1. mcp__mcp_web_search__brave_web_search(query="AI 2024", count=5)
2. mcp__research_papers__search_papers(query="multi-agent systems", max_results=3)
3. mcp__firecrawl__firecrawl_search(query="coordination algorithms 2024")

PRODUCTION AGENT SPAWNING PATTERNS:
```bash
claude -p \\
  --model opus \\
  --strict-mcp-config --mcp-config ~/.claude_research.json \\
  --permission-mode acceptEdits \\
  --output-format json \\
  --session-id "$(uuidgen)" \\
  --allowed-tools "mcp__mcp_web_search__brave_web_search,mcp__research_papers__search_papers" \\
  "Research task with specified tools"
```

PERFORMANCE TIPS FROM PRODUCTION GUIDE:
- Use selective MCP loading for 3-5x faster startup
- Unique session IDs prevent conflicts
- acceptEdits mode saves 5-15 seconds
- Parallel execution cuts time by 70%
- Model choice: Sonnet for speed, Opus for quality
"""

    # Define the unified research challenge
    unified_challenge = f"""
🎯 UNIFIED RESEARCH CHALLENGE FOR ALL TEAMS:
"Multi-Agent AI Systems 2024-2025: Comprehensive Breakthrough Analysis & Implementation Design"

DELIVERABLE REQUIREMENTS (Deliberately challenging scope):
1. **Research Analysis**: 5 most significant coordination breakthroughs with full academic verification
2. **Comparative Framework**: Quantitative comparison matrix across all breakthroughs
3. **Implementation Design**: Technical architecture for adopting best patterns
4. **Risk Assessment**: Failure modes and mitigation strategies
5. **Strategic Roadmap**: 12-month implementation timeline with resource requirements

⚠️ WARNING: This scope is INTENTIONALLY too large for 6 minutes! Teams must demonstrate:
- **Strategic prioritization** - What do they focus on first?
- **Quality vs quantity decisions** - Do they attempt everything poorly or focus excellently?
- **Time management** - Can they deliver complete sections vs incomplete overview?
"""

    tasks = [
        # Team Alpha - 3 specialists
        AgentTask(
            task_id="alpha_algorithms_lead",
            task_type="research",
            prompt=f"""🧠 ALPHA ALGORITHMS SPECIALIST

SESSION ID: {session_ids['alpha']}-algo
{mcp_docs.format(team_session=session_ids['alpha'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **ALGORITHM ANALYSIS**
Identify the top 2-3 coordination algorithms from 2024-2025. Use mcp__research_papers__search_papers and mcp__mcp_web_search.

DELIVERABLE: For each algorithm:
(1) Paper details with DOI
(2) Core coordination mechanism
(3) Scalability metrics (max agents)
(4) Performance vs baselines
(5) Innovation significance

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Coordinate with your Alpha teammates via shared output directory while competing against Beta/Gamma/Delta/Epsilon teams!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="alpha_systems_lead",
            task_type="research",
            prompt=f"""🧠 ALPHA SYSTEMS SPECIALIST

SESSION ID: {session_ids['alpha']}-sys
{mcp_docs.format(team_session=session_ids['alpha'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **SYSTEMS IMPLEMENTATION**
Identify 2-3 real-world multi-agent system implementations from 2024-2025. Use all MCP research tools.

DELIVERABLE: For each system:
(1) System description with citations
(2) Architecture and coordination approach
(3) Performance metrics achieved
(4) Real-world deployment scale
(5) Impact assessment

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Work with Alpha teammates while outperforming the other 12 agents!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="alpha_impact_lead",
            task_type="research",
            prompt=f"""🧠 ALPHA IMPACT SPECIALIST

SESSION ID: {session_ids['alpha']}-impact
{mcp_docs.format(team_session=session_ids['alpha'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **IMPACT & APPLICATIONS**
Identify 2-3 breakthrough applications where multi-agent AI achieved significant real-world results in 2024-2025.

DELIVERABLE: For each application:
(1) Domain and use case with citations
(2) Multi-agent approach used
(3) Quantified impact vs traditional methods
(4) Scalability demonstrated
(5) Future potential assessment

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Alpha team coordination + individual excellence = victory!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        # Team Beta - 3 specialists
        AgentTask(
            task_id="beta_theory_lead",
            task_type="research",
            prompt=f"""⚡ BETA THEORY SPECIALIST

SESSION ID: {session_ids['beta']}-theory
{mcp_docs.format(team_session=session_ids['beta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **THEORETICAL FOUNDATIONS**
Identify 2-3 theoretical breakthroughs in multi-agent coordination from 2024-2025. Use mcp__research_papers__search_papers and web search.

DELIVERABLE: For each theory:
(1) Paper details with DOI
(2) Theoretical contribution/innovation
(3) Mathematical framework
(4) Experimental validation
(5) Implications for field advancement

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Beta theoretical excellence will dominate the competition!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="beta_engineering_lead",
            task_type="research",
            prompt=f"""⚡ BETA ENGINEERING SPECIALIST

SESSION ID: {session_ids['beta']}-eng
{mcp_docs.format(team_session=session_ids['beta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **ENGINEERING EXCELLENCE**
Identify 2-3 engineering breakthroughs that enable large-scale multi-agent coordination from 2024-2025.

DELIVERABLE: For each breakthrough:
(1) Engineering innovation with citations
(2) Technical architecture
(3) Scalability achievements
(4) Performance benchmarks
(5) Industry adoption potential

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Engineering precision gives Beta the edge!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="beta_competitive_lead",
            task_type="research",
            prompt=f"""⚡ BETA COMPETITIVE INTELLIGENCE SPECIALIST

SESSION ID: {session_ids['beta']}-intel
{mcp_docs.format(team_session=session_ids['beta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **COMPETITIVE ANALYSIS**
Compare top multi-agent systems from 2024-2025 to identify what makes them superior.

DELIVERABLE: For each system:
(1) System details with citations
(2) Competitive advantages identified
(3) Performance superiority metrics
(4) Market/research impact
(5) Strategic implications

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Competitive intelligence ensures Beta victory!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        # Team Gamma - 3 specialists
        AgentTask(
            task_id="gamma_security_lead",
            task_type="research",
            prompt=f"""🛡️ GAMMA SECURITY SPECIALIST

SESSION ID: {session_ids['gamma']}-sec
{mcp_docs.format(team_session=session_ids['gamma'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **SECURITY & ROBUSTNESS**
Research security aspects and robustness of multi-agent coordination systems from 2024-2025.

DELIVERABLE: For each security approach:
(1) Security framework with citations
(2) Threat model and attack vectors
(3) Defense mechanisms
(4) Robustness validation results
(5) Real-world security implications

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Security-first approach gives Gamma the advantage!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="gamma_scalability_lead",
            task_type="research",
            prompt=f"""🛡️ GAMMA SCALABILITY SPECIALIST

SESSION ID: {session_ids['gamma']}-scale
{mcp_docs.format(team_session=session_ids['gamma'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **SCALABILITY & PERFORMANCE**
Research scalability breakthroughs in multi-agent systems from 2024-2025.

DELIVERABLE: For each scalability solution:
(1) Scalability approach with citations
(2) Performance characteristics
(3) Resource utilization patterns
(4) Scaling limits and bottlenecks
(5) Practical deployment considerations

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Scalability expertise drives Gamma success!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="gamma_coordination_lead",
            task_type="research",
            prompt=f"""🛡️ GAMMA COORDINATION SPECIALIST

SESSION ID: {session_ids['gamma']}-coord
{mcp_docs.format(team_session=session_ids['gamma'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **COORDINATION PROTOCOLS**
Research advanced coordination protocols for multi-agent systems from 2024-2025.

DELIVERABLE: For each protocol:
(1) Protocol specification with citations
(2) Communication patterns
(3) Fault tolerance mechanisms
(4) Coordination efficiency metrics
(5) Protocol comparison analysis

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Coordination mastery ensures Gamma dominance!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        # Team Delta - 3 specialists
        AgentTask(
            task_id="delta_learning_lead",
            task_type="research",
            prompt=f"""🎯 DELTA LEARNING SPECIALIST

SESSION ID: {session_ids['delta']}-learn
{mcp_docs.format(team_session=session_ids['delta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **MULTI-AGENT LEARNING**
Research learning algorithms and adaptation mechanisms in multi-agent systems from 2024-2025.

DELIVERABLE: For each learning approach:
(1) Learning algorithm with citations
(2) Adaptation mechanisms
(3) Convergence properties
(4) Performance in dynamic environments
(5) Learning efficiency comparisons

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Learning superiority gives Delta the competitive edge!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="delta_optimization_lead",
            task_type="research",
            prompt=f"""🎯 DELTA OPTIMIZATION SPECIALIST

SESSION ID: {session_ids['delta']}-opt
{mcp_docs.format(team_session=session_ids['delta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **OPTIMIZATION & EFFICIENCY**
Research optimization techniques for multi-agent coordination from 2024-2025.

DELIVERABLE: For each optimization:
(1) Optimization method with citations
(2) Efficiency improvements achieved
(3) Resource utilization benefits
(4) Computational complexity analysis
(5) Practical implementation considerations

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Optimization excellence drives Delta victory!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="delta_deployment_lead",
            task_type="research",
            prompt=f"""🎯 DELTA DEPLOYMENT SPECIALIST

SESSION ID: {session_ids['delta']}-deploy
{mcp_docs.format(team_session=session_ids['delta'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **DEPLOYMENT & OPERATIONS**
Research deployment strategies and operational considerations for multi-agent systems from 2024-2025.

DELIVERABLE: For each deployment approach:
(1) Deployment strategy with citations
(2) Infrastructure requirements
(3) Monitoring and maintenance
(4) Operational challenges solved
(5) Production deployment lessons

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Deployment expertise ensures Delta success!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        # Team Epsilon - 3 specialists
        AgentTask(
            task_id="epsilon_innovation_lead",
            task_type="research",
            prompt=f"""🚀 EPSILON INNOVATION SPECIALIST

SESSION ID: {session_ids['epsilon']}-innov
{mcp_docs.format(team_session=session_ids['epsilon'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **EMERGING INNOVATIONS**
Research the most innovative and cutting-edge multi-agent approaches from 2024-2025.

DELIVERABLE: For each innovation:
(1) Innovation details with citations
(2) Novel approach characteristics
(3) Breakthrough significance
(4) Potential impact assessment
(5) Future research directions

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Innovation leadership gives Epsilon the breakthrough advantage!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="epsilon_integration_lead",
            task_type="research",
            prompt=f"""🚀 EPSILON INTEGRATION SPECIALIST

SESSION ID: {session_ids['epsilon']}-integ
{mcp_docs.format(team_session=session_ids['epsilon'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **SYSTEM INTEGRATION**
Research integration patterns and interoperability in multi-agent systems from 2024-2025.

DELIVERABLE: For each integration approach:
(1) Integration pattern with citations
(2) Interoperability mechanisms
(3) System compatibility
(4) Integration complexity analysis
(5) Successful integration examples

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Integration mastery drives Epsilon dominance!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="epsilon_future_lead",
            task_type="research",
            prompt=f"""🚀 EPSILON FUTURE SPECIALIST

SESSION ID: {session_ids['epsilon']}-future
{mcp_docs.format(team_session=session_ids['epsilon'])}

{unified_challenge}

YOUR SPECIFIC FOCUS: **FUTURE DIRECTIONS**
Research future trends and emerging directions in multi-agent AI from 2024-2025.

DELIVERABLE: For each trend:
(1) Trend analysis with citations
(2) Technology trajectory
(3) Market adoption potential
(4) Research investment patterns
(5) Strategic implications for 2025+

TACTICAL ADVANTAGE: You are ONE OF 15 AGENTS running in TRUE PARALLEL. Future vision ensures Epsilon victory!

EXECUTE RESEARCH MISSION - 6 MINUTE WINDOW!""",
            context={"timeout": 400},
        ),
    ]

    # Create UNLIMITED orchestrator
    orchestrator = GenericOrchestrator(
        max_parallel=15,  # TRUE 15-AGENT PARALLELISM
        output_dir=Path("/tmp/unlimited_parallel_competition"),
    )

    print("🚀 UNLIMITED PARALLEL RESEARCH COMPETITION")
    print("=" * 60)
    print("📋 Competition Structure:")
    print("   • 15 AGENTS IN TRUE PARALLEL EXECUTION")
    print("   • 5 teams × 3 specialists each = 15 simultaneous researchers")
    print("   • Each agent gets unique token from 19-token pool")
    print("   • All tackle same research challenge for direct comparison")
    print("   • Timeline: 6 minutes (impossible scope to test prioritization)")
    print()
    print("🏆 Teams:")
    print("   🧠 Team Alpha: Algorithms + Systems + Impact")
    print("   ⚡ Team Beta: Theory + Engineering + Competitive Intelligence")
    print("   🛡️ Team Gamma: Security + Scalability + Coordination")
    print("   🎯 Team Delta: Learning + Optimization + Deployment")
    print("   🚀 Team Epsilon: Innovation + Integration + Future Trends")
    print()
    print("📊 Victory Conditions:")
    print("   • Research Excellence (25 pts) - Methodology & critical analysis")
    print("   • Citation Excellence (35 pts) - 100% citation goal + elite venues")
    print("   • Strategic Orchestration (25 pts) - Coordination & tool mastery")
    print("   • Actionable Impact (25 pts) - Forward-looking insights")
    print("   • Design Excellence (20 pts) - Architecture & risk assessment")
    print("   • Time Management (15 pts) - Strategic prioritization")
    print("   • MAXIMUM: 145 points")
    print()
    print("🔧 Technical Goals:")
    print("   • Test 19-token pool with 15 parallel agents")
    print("   • Validate true parallelism vs sequential/batched execution")
    print("   • Monitor MCP tool concurrent usage at scale")
    print("   • Assess strategic prioritization under impossible time pressure")
    print()
    print("🚀 INITIATING 15-AGENT UNLIMITED PARALLEL COMPETITION...")

    # Execute unlimited parallel competition
    results = await orchestrator.execute_batch(tasks)

    print("\n🏆 UNLIMITED PARALLEL COMPETITION COMPLETE!")
    print("=" * 60)
    print(
        f"📊 Results: {len([r for r in results if r.get('status') == 'completed'])} agents completed research"
    )
    print("🎖️ True 15-agent parallelism tested!")

    # Enhanced judging with team aggregation
    print("\n🏆 TEAM COMPETITION JUDGING:")
    print("=" * 60)

    team_results = {"Alpha": [], "Beta": [], "Gamma": [], "Delta": [], "Epsilon": []}

    # Group results by team
    for result in results:
        if result.get("status") == "completed":
            task_id = result.get("task_id", "")
            if task_id.startswith("alpha_"):
                team_results["Alpha"].append(result)
            elif task_id.startswith("beta_"):
                team_results["Beta"].append(result)
            elif task_id.startswith("gamma_"):
                team_results["Gamma"].append(result)
            elif task_id.startswith("delta_"):
                team_results["Delta"].append(result)
            elif task_id.startswith("epsilon_"):
                team_results["Epsilon"].append(result)

    team_scores = {}

    for team_name, team_results_list in team_results.items():
        if not team_results_list:
            continue

        # Aggregate team score from all specialists
        total_team_score = 0
        total_citations = 0
        total_elite_venues = 0
        total_tools_used = 0
        total_output = 0

        for result in team_results_list:
            output_text = str(result.get("result", {}).get("content", ""))
            content_lower = output_text.lower()

            # Apply same scoring logic as refined competition
            score = 0

            # Research Excellence (25 pts)
            methodology_indicators = [
                "methodology",
                "approach",
                "framework",
                "systematic",
                "rigorous",
            ]
            score += min(
                sum(3 for term in methodology_indicators if term in content_lower), 15
            )

            if any(
                term in content_lower
                for term in [
                    "compared to",
                    "vs",
                    "versus",
                    "outperforms",
                    "better than",
                ]
            ):
                score += 10

            # Citation Excellence (35 pts)
            claim_indicators = [
                "found",
                "shows",
                "demonstrates",
                "achieves",
                "reports",
                "states",
            ]
            total_claims = sum(
                1 for indicator in claim_indicators if indicator in content_lower
            )

            doi_count = output_text.count("doi:") + output_text.count("DOI")
            arxiv_count = output_text.count("arxiv:") + output_text.count("arXiv")
            url_citations = output_text.count("http") - output_text.count("mcp__")
            citations = doi_count + arxiv_count + url_citations

            if total_claims > 0:
                citation_percentage = min(citations / total_claims, 1.0)
                score += int(citation_percentage * 15)

            elite_venues = ["nature", "science", "cell", "nejm"]
            elite_count = sum(1 for venue in elite_venues if venue in content_lower)
            score += min(elite_count * 5, 15)

            # Strategic Orchestration (25 pts)
            strategy_indicators = [
                "strategy",
                "coordination",
                "orchestration",
                "parallel",
                "specialized",
            ]
            score += min(
                sum(3 for term in strategy_indicators if term in content_lower), 15
            )

            if "mcp__" in output_text:
                score += 10

            # Actionable Impact (25 pts)
            impact_indicators = [
                "implications",
                "impact",
                "significance",
                "applications",
                "future",
                "enables",
            ]
            score += min(
                sum(2 for term in impact_indicators if term in content_lower), 12
            )

            quant_indicators = [
                "%",
                "accuracy",
                "improvement",
                "reduction",
                "faster",
                "efficiency",
            ]
            score += min(
                sum(2 for term in quant_indicators if term in content_lower), 8
            )

            recent_focus = output_text.count("2024") + output_text.count("2025")
            score += min(recent_focus, 5)

            # Design Excellence (20 pts)
            architecture_terms = [
                "architecture",
                "framework",
                "design",
                "system",
                "implementation",
            ]
            score += min(
                sum(2 for term in architecture_terms if term in content_lower), 8
            )

            if "risk" in content_lower or "mitigation" in content_lower:
                score += 4
            if "roadmap" in content_lower or "timeline" in content_lower:
                score += 4
            if "requirements" in content_lower or "resource" in content_lower:
                score += 4

            # Time Management (15 pts)
            priority_indicators = [
                "focus",
                "priority",
                "first",
                "most important",
                "key",
            ]
            score += min(
                sum(2 for term in priority_indicators if term in content_lower), 8
            )

            section_depth = 0
            if "conclusion" in content_lower or "summary" in content_lower:
                section_depth += 3
            if (
                "analysis" in content_lower
                and len(
                    [
                        m
                        for m in ["detailed", "comprehensive", "thorough"]
                        if m in content_lower
                    ]
                )
                > 0
            ):
                section_depth += 4
            score += section_depth

            # Aggregate team metrics
            total_team_score += score
            total_citations += citations
            total_elite_venues += elite_count
            total_tools_used += 1 if "mcp__" in output_text else 0
            total_output += len(output_text)

        # Calculate team averages
        num_specialists = len(team_results_list)
        avg_score = total_team_score / num_specialists if num_specialists > 0 else 0

        team_scores[team_name] = {
            "total_score": total_team_score,
            "avg_score": avg_score,
            "specialists_completed": num_specialists,
            "total_citations": total_citations,
            "total_elite_venues": total_elite_venues,
            "tools_usage_rate": total_tools_used / num_specialists
            if num_specialists > 0
            else 0,
            "total_output": total_output,
        }

        print(
            f"🎯 Team {team_name}: {total_team_score:.1f} total points ({avg_score:.1f} avg)"
        )
        print(f"   👥 Specialists: {num_specialists}/3 completed")
        print(f"   📚 Citations: {total_citations} across all specialists")
        print(f"   🏆 Elite venues: {total_elite_venues} total")
        print(
            f"   🔧 Tool usage: {total_tools_used}/{num_specialists} specialists used MCP"
        )
        print(f"   📝 Research depth: {total_output:,} chars total output")
        print()

    # Determine winner
    if team_scores:
        winner = max(team_scores.items(), key=lambda x: x[1]["total_score"])
        print(
            f"🏆 WINNER: Team {winner[0]} with {winner[1]['total_score']:.1f} total points!"
        )
        print(
            f"🎖️ Victory achieved through: {winner[1]['specialists_completed']}/3 specialists completing comprehensive research"
        )

        # Show top 3 teams
        sorted_teams = sorted(
            team_scores.items(), key=lambda x: x[1]["total_score"], reverse=True
        )
        print(f"\n🏅 FINAL STANDINGS:")
        for i, (team, stats) in enumerate(sorted_teams[:3], 1):
            print(
                f"   {i}. Team {team}: {stats['total_score']:.1f} points ({stats['avg_score']:.1f} avg)"
            )

    # Write competition metadata for analysis
    competition_meta = {
        "competition_id": session_ids["competition"],
        "session_ids": session_ids,
        "tasks": [task.task_id for task in tasks],
        "start_time": datetime.now().isoformat(),
        "results": results,
        "team_scores": team_scores,
    }

    meta_file = (
        Path("/tmp/unlimited_parallel_competition") / "competition_metadata.json"
    )
    meta_file.parent.mkdir(exist_ok=True)
    with open(meta_file, "w") as f:
        json.dump(competition_meta, f, indent=2)

    print(f"\n📝 Competition metadata saved: {meta_file}")

    return results


if __name__ == "__main__":
    asyncio.run(create_unlimited_competition())
