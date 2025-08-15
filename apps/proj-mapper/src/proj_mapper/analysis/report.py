"""Analysis reports for Project Mapper.

This module derives a basic import graph from the project map and computes
useful metrics for action: hubs, orphans, cycles, and package coupling.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import os
import json


@dataclass(frozen=True)
class Graph:
    nodes: List[str]
    edges: List[Tuple[str, str]]  # (source, target)


def _derive_module_name(relative_path: str) -> str:
    rel = relative_path
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.lstrip("./")
    return rel.replace(os.sep, ".")


def _extract_imports(py_path: str) -> List[str]:
    imports: List[str] = []
    try:
        with open(py_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("import "):
                    rest = s[len("import "):]
                    parts = [p.strip() for p in rest.split(",")]
                    for p in parts:
                        root = p.split(" as ")[0].strip()
                        if root:
                            imports.append(root)
                elif s.startswith("from ") and " import " in s:
                    root = s[len("from "):].split(" import ")[0].strip()
                    if root:
                        imports.append(root)
    except Exception:
        pass
    return imports


def build_import_graph(map_data: Dict[str, Any]) -> Graph:
    files = map_data.get("files") or []
    module_to_node: Dict[str, str] = {}
    node_ids: List[str] = []

    for f in files:
        if f.get("file_type") != "python":
            continue
        rel = f.get("relative_path") or f.get("path")
        if not rel:
            continue
        mod = _derive_module_name(rel)
        module_to_node[mod] = rel
        node_ids.append(rel)

    edges: List[Tuple[str, str]] = []
    for f in files:
        if f.get("file_type") != "python":
            continue
        rel = f.get("relative_path") or f.get("path")
        path = f.get("path")
        if not rel or not path:
            continue
        imported = _extract_imports(path)
        for imp in imported:
            targets = [module_to_node[k] for k in module_to_node if k == imp or k.startswith(imp + ".")]
            for tgt in targets:
                if tgt != rel:
                    edges.append((rel, tgt))

    return Graph(nodes=node_ids, edges=edges)


def compute_hubs(graph: Graph, top_n: int = 15) -> List[Dict[str, Any]]:
    in_deg: Dict[str, int] = {n: 0 for n in graph.nodes}
    out_deg: Dict[str, int] = {n: 0 for n in graph.nodes}
    for s, t in graph.edges:
        out_deg[s] = out_deg.get(s, 0) + 1
        in_deg[t] = in_deg.get(t, 0) + 1
    scores = [
        {
            "node": n,
            "in": in_deg.get(n, 0),
            "out": out_deg.get(n, 0),
            "degree": in_deg.get(n, 0) + out_deg.get(n, 0),
        }
        for n in graph.nodes
    ]
    scores.sort(key=lambda x: (x["degree"], x["in"]), reverse=True)
    return scores[:top_n]


def compute_orphans(graph: Graph) -> List[str]:
    has_edge: Dict[str, bool] = {n: False for n in graph.nodes}
    for s, t in graph.edges:
        has_edge[s] = True
        has_edge[t] = True
    return [n for n, flag in has_edge.items() if not flag]


def _adjacency(graph: Graph) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    out_adj: Dict[str, List[str]] = {n: [] for n in graph.nodes}
    in_adj: Dict[str, List[str]] = {n: [] for n in graph.nodes}
    for s, t in graph.edges:
        out_adj.setdefault(s, []).append(t)
        in_adj.setdefault(t, []).append(s)
    return out_adj, in_adj


def compute_scc(graph: Graph) -> List[List[str]]:
    # Tarjan's algorithm for strongly connected components
    out_adj, _ = _adjacency(graph)
    index = 0
    indices: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Dict[str, bool] = {}
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack[v] = True
        for w in out_adj.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w):
                lowlink[v] = min(lowlink[v], indices[w])
        # If v is a root node, pop the stack and output an SCC
        if lowlink[v] == indices[v]:
            comp: List[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in graph.nodes:
        if v not in indices:
            strongconnect(v)

    return sccs


def compute_cycles(graph: Graph, max_list: int = 10) -> Dict[str, Any]:
    sccs = compute_scc(graph)
    cyc = [comp for comp in sccs if len(comp) > 1]
    result = {
        "count": len(cyc),
        "components": cyc[:max_list],
    }
    return result


def _pkg_of(node: str, depth: int = 2) -> str:
    parts = node.split("/")
    return "/".join(parts[:depth]) if len(parts) >= depth else node


def compute_package_coupling(graph: Graph, depth: int = 2, top_n: int = 20) -> List[Dict[str, Any]]:
    counts: Dict[Tuple[str, str], int] = {}
    for s, t in graph.edges:
        sp = _pkg_of(s, depth)
        tp = _pkg_of(t, depth)
        if sp == tp:
            continue
        key = (sp, tp)
        counts[key] = counts.get(key, 0) + 1
    pairs = [
        {"source": k[0], "target": k[1], "edges": v}
        for k, v in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return pairs[:top_n]


def make_report(map_data: Dict[str, Any], top_n: int = 15) -> Dict[str, Any]:
    graph = build_import_graph(map_data)
    hubs = compute_hubs(graph, top_n=top_n)
    orphans = compute_orphans(graph)
    cycles = compute_cycles(graph, max_list=top_n)
    coupling = compute_package_coupling(graph, depth=2, top_n=top_n)
    return {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "top_hubs": hubs,
        "orphans": orphans,
        "cycles": cycles,
        "package_coupling": coupling,
    }


def print_report_text(report: Dict[str, Any]) -> None:
    print(f"Nodes: {report['nodes']}  Edges: {report['edges']}")
    print("\nTop hubs (degree,in,out):")
    for h in report["top_hubs"]:
        print(f"  {h['node']}  {h['degree']} ({h['in']},{h['out']})")
    print("\nOrphans (no edges):")
    for n in report["orphans"][:30]:
        print(f"  {n}")
    if len(report["orphans"]) > 30:
        print(f"  ... (+{len(report['orphans'])-30} more)")
    print("\nCycles (SCCs with >1 node): count=", report["cycles"]["count"])
    for comp in report["cycles"]["components"]:
        print("  - ", " -> ".join(comp))
    print("\nTop package coupling (edges):")
    for p in report["package_coupling"]:
        print(f"  {p['source']} -> {p['target']}: {p['edges']}")
