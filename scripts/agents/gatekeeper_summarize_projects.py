#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any

ROOT = Path("/home/opsvi/master_root")
CUSTOM = ROOT / "intake" / "custom"


def load_pi(project_dir: Path) -> dict[str, Any] | None:
    pi = project_dir / ".proj-intel" / "project_analysis.pretty.json"
    if not pi.exists():
        return None
    try:
        return json.loads(pi.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_collector(data: dict[str, Any], name: str) -> dict[str, Any]:
    for c in data.get("collectors", []):
        if c.get("collector") == name:
            return c.get("data", {})
    return {}


def top_techs(deps: dict[str, Any], limit: int = 20) -> list[str]:
    techs: list[str] = []
    for key in ("python_imports", "external_dependencies", "requirements"):
        v = deps.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    techs.append(item)
                elif isinstance(item, dict):
                    n = item.get("name")
                    if n:
                        techs.append(n)
    # normalize and limit
    norm = []
    for t in techs:
        tt = str(t).strip()
        if tt:
            norm.append(tt)
    seen = set()
    ordered: list[str] = []
    for t in norm:
        tl = t.lower()
        if tl not in seen:
            ordered.append(t)
            seen.add(tl)
        if len(ordered) >= limit:
            break
    return ordered


def synthesize_summary(project_dir: Path, data: dict[str, Any]) -> str:
    name = project_dir.name
    purpose = get_collector(data, "ProjectPurposeCollector")
    deps = get_collector(data, "DependenciesCollector")
    files = get_collector(data, "FileElementsCollector")
    apis = get_collector(data, "ApiEndpointsCollector")
    agents = get_collector(data, "AgentArchitectureCollector")

    file_count = deps.get("file_count") or files.get("total_files") or 0
    endpoints = apis.get("endpoints") or []
    has_agents = bool(agents.get("has_agents", False))

    techs = top_techs(deps)

    lines: list[str] = []
    lines.append(f"# {name} — Agent Gatekeeper Summary\n")
    if purpose:
        desc = purpose.get("summary") or purpose.get("description") or ""
        if desc:
            lines.append(f"**Purpose**: {desc}\n")
    lines.append(f"**Files**: {file_count}\n")
    lines.append(f"**Agents**: {'yes' if has_agents else 'no'}\n")
    if techs:
        lines.append("**Technologies (detected)**: " + ", ".join(techs) + "\n")
    if endpoints:
        lines.append("**API Endpoints (sample)**:")
        for e in endpoints[:10]:
            if isinstance(e, dict):
                method = e.get("method", "GET")
                path = e.get("path", "/")
                lines.append(f"- {method} {path}")
        lines.append("")

    # Suggested actions
    suggested: list[str] = []
    joined_techs = ",".join([t.lower() for t in techs])
    if has_agents:
        suggested.append(
            "Extract agent base classes to libs/opsvi-agents and import here"
        )
    if "neo4j" in joined_techs:
        suggested.append(
            "Use libs/opsvi-data.graph.neo4j_client for DB access and queries"
        )
    if "chroma" in joined_techs:
        suggested.append(
            "Use libs/opsvi-data.vector.chroma_client for vector store APIs"
        )
    if endpoints:
        suggested.append("Document REST surface in docs/api.md and add OpenAPI schema")
    if isinstance(file_count, int) and file_count > 200:
        suggested.append("Split into apps/ + libs/ per the platform structure")

    if suggested:
        lines.append("**Suggested next steps**:")
        for s in suggested:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def synthesize_diagram(project_dir: Path, data: dict[str, Any]) -> str:
    name = project_dir.name.replace("-", "_")
    deps = get_collector(data, "DependenciesCollector")
    apis = get_collector(data, "ApiEndpointsCollector")
    agents = get_collector(data, "AgentArchitectureCollector")

    has_agents = bool(agents.get("has_agents", False))
    techs = top_techs(deps, limit=8)

    # Build a simple LR diagram
    lines: list[str] = []
    lines.append("graph LR")
    lines.append(f'  Main["{name}"]')
    if has_agents:
        lines.append('  Agents["Agents"]')
        lines.append("  Main --> Agents")
    if apis.get("endpoints"):
        lines.append('  API["API"]')
        lines.append("  Main --> API")
    if techs:
        lines.append('  subgraph Tech["Technologies"]')
        for i, t in enumerate(techs):
            node = f"T{i}"
            safe = str(t).replace('"', "'")
            lines.append(f'    {node}["{safe}"]')
            lines.append(f"    Main --> {node}")
        lines.append("  end")
    return "\n".join(lines)


def main() -> None:
    out_root = CUSTOM / "visualizations"
    out_root.mkdir(exist_ok=True)

    index_lines: list[str] = ["# Agent Gatekeeper Project Summaries\n"]

    projects = [
        p
        for p in CUSTOM.iterdir()
        if p.is_dir() and p.name not in {".proj-intel", "visualizations"}
    ]
    for proj in sorted(projects, key=lambda p: p.name.lower()):
        data = load_pi(proj)
        if not data:
            continue
        summary = synthesize_summary(proj, data)
        diagram = synthesize_diagram(proj, data)

        proj_out = proj / ".proj-intel"
        proj_out.mkdir(exist_ok=True)

        (proj_out / "AGENT_SUMMARY.md").write_text(summary, encoding="utf-8")
        (proj_out / "AGENT_DIAGRAM.md").write_text(
            f"```mermaid\n{diagram}\n```\n", encoding="utf-8"
        )

        rel = proj_out.relative_to(CUSTOM)
        index_lines.append(f"- **{proj.name}**: see `{rel}/AGENT_SUMMARY.md`")

    (out_root / "AGENT_GATEKEEPER_INDEX.md").write_text(
        "\n".join(index_lines), encoding="utf-8"
    )
    print("✅ Agent summaries and diagrams generated.")


if __name__ == "__main__":
    main()
