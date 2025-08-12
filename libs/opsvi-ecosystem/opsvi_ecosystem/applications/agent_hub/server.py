import json
import os
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import networkx as nx
from pydantic import BaseModel
import pydot
import yaml

from .db_client import manage, modify, search
from .openai_helper import chat_structured

app = FastAPI(
    title="Agent Hub MCP",
    description="Multi-agent system with Agent Protocol compliance and service discovery",
    version="1.0.0",
)

# Mount static files for dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates for dashboard
templates = Jinja2Templates(directory="templates")

# Initialize agent discovery service
try:
    from agent_discovery import setup_agent_discovery

    discovery_service = setup_agent_discovery(app)
    print("✅ Agent discovery service initialized")
except ImportError as e:
    print(f"⚠️  Agent discovery not available: {e}")
    discovery_service = None


# Utilities
def load_profile(name: str) -> str:
    p = Path(__file__).parent / "agents" / f"{name}.yaml"
    content = yaml.safe_load(p.read_text())
    return content.get("system_prompt", p.read_text())


def load_schema(name: str) -> dict:
    p = Path(__file__).parent / "schemas" / f"{name}.json"
    return json.loads(p.read_text())


def _deprecated_call_openai(
    model: str, system: str, user: str, functions: list[dict] | None = None
):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        functions=functions,
        function_call="auto" if functions else None,
        temperature=0,
    )
    return resp.choices[0].message


def _call(model, sys, user, schema):
    """
    Updated _call function to work with Structured Outputs
    """
    try:
        # Use the new chat_structured function
        response = chat_structured(model, sys, user, schema)

        # Debug logging
        print(f"[DEBUG] Response type: {type(response)}")
        print(f"[DEBUG] Has content: {response.content is not None}")
        print(f"[DEBUG] Has refusal: {response.refusal is not None}")
        print(f"[DEBUG] Has parsed: {response.parsed is not None}")
        if response.content:
            print(f"[DEBUG] Content preview: {response.content[:100]}...")

        # Handle refusals (safety rejections)
        if response.refusal:
            return {
                "error": "Request refused for safety reasons",
                "refusal": response.refusal,
            }

        # Handle structured response (parsed JSON)
        if response.parsed:
            print(
                f"[DEBUG] Returning parsed response with keys: {list(response.parsed.keys())}"
            )
            return response.parsed

        # Handle regular content response (fallback for non-structured calls)
        elif response.content:
            try:
                parsed = json.loads(response.content)
                print(
                    f"[DEBUG] Returning manually parsed response with keys: {list(parsed.keys())}"
                )
                return parsed
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse response as JSON",
                    "raw_content": response.content,
                }
        else:
            print("[DEBUG] Empty response detected")
            return {
                "error": "Empty response from OpenAI",
                "debug_info": {
                    "has_content": response.content is not None,
                    "content": response.content,
                    "has_refusal": response.refusal is not None,
                    "refusal": response.refusal,
                },
            }

    except Exception as e:
        import traceback

        print(f"[DEBUG] Exception in _call: {e}")
        return {
            "error": f"OpenAI call failed: {str(e)}",
            "traceback": traceback.format_exc(),
        }


### Web Dashboard ###
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the Agent Hub web dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


### JSON-RPC plumbing ###
class RPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict | None = None


@app.post("/rpc")
async def rpc(req: RPCRequest):
    method = req.method
    params = req.params or {}
    try:
        if method == "system.listMethods":
            # Return the list of available methods
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": [
                    "dev_agent.generate_feature",
                    "sentinel.audit_patch",
                    "kb_updater.digest_research",
                    "graph_analyst.predict_links",
                    "quality_curator.vector_healthcheck",
                    "context_builder.get_context",
                    "rule_synthesizer.synthesize_rules",
                    "knowledge_onboarding.get_briefing",
                    "memory_manager.store_memory",
                    "memory_manager.retrieve_memories",
                    "preference_tracker.capture_preference",
                    "preference_tracker.get_preferences",
                    "insight_synthesizer.consolidate",
                ],
            }
        if method == "dev_agent.generate_feature":
            result = await dev_generate_feature(**params)
        elif method == "sentinel.audit_patch":
            result = await sentinel_audit_patch(**params)
        elif method == "kb_updater.digest_research":
            result = await kb_digest_research(**params)
        elif method == "graph_analyst.predict_links":
            result = await ga_predict_links(**params)
        elif method == "quality_curator.vector_healthcheck":
            result = await qc_vector_health(**params)
        # AI Assistant Enhancement Agents
        elif method == "context_builder.get_context":
            result = await context_builder_get_context(**params)
        elif method == "rule_synthesizer.synthesize_rules":
            result = await rule_synthesizer_synthesize_rules(**params)
        elif method == "knowledge_onboarding.get_briefing":
            result = await knowledge_onboarding_get_briefing(**params)
        elif method == "memory_manager.store_memory":
            result = await memory_manager_store_memory(**params)
        elif method == "memory_manager.retrieve_memories":
            result = await memory_manager_retrieve_memories(**params)
        elif method == "preference_tracker.capture_preference":
            result = await preference_tracker_capture_preference(**params)
        elif method == "preference_tracker.get_preferences":
            result = await preference_tracker_get_preferences(**params)
        elif method == "insight_synthesizer.consolidate":
            result = await insight_synthesizer_consolidate(**params)
        else:
            raise ValueError(f"Unknown method {method}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"jsonrpc": "2.0", "id": req.id, "result": result}


### Tool handlers ###


async def dev_generate_feature(spec: str, repo_state_hash: str):
    sys = load_profile("dev_agent")
    # fetch development rules
    rule_result = search(
        search_type="tags", collection="rules", tags=["development"], limit=20
    )
    rule_docs = (
        rule_result.get("result", {}).get("results", [])
        if rule_result.get("result", {}).get("success")
        else []
    )
    rule_text = " ".join([r.get("content", "") for r in rule_docs])
    user = f"""Implement the following feature in our codebase.
SPEC: {spec}
REPO_HASH: {repo_state_hash}
Relevant rules:
{rule_text[:4000]}"""
    schema = load_schema("patch_schema")
    bundle = _call("gpt-4o-mini", sys, user, schema)
    # persist docs and rules additions if present
    if bundle.get("rules_added"):
        for r in bundle["rules_added"]:
            modify(
                operation="insert",
                collection="rules",
                document={
                    "content": r,
                    "source": "dev_agent",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            )
    return bundle


async def sentinel_audit_patch(diff: str, rule_ids: list[str]):
    sys = load_profile("sentinel")
    user = f"Audit this diff against rules {rule_ids} and return a compliance_report.  DIFF: {diff}"
    schema = load_schema("compliance_schema")
    msg = _call("gpt-4o-mini", sys, user, schema)
    return msg if isinstance(msg, dict) else {"error": "Invalid response format"}


async def kb_digest_research(doc_ids: list[str]):
    sys = load_profile("kb_updater")
    user = f"Process research documents {doc_ids} and extract heuristics."
    schema = load_schema("heuristic_batch_schema")
    msg = _call("gpt-4o-mini", sys, user, schema)
    return msg if isinstance(msg, dict) else {"error": "Invalid response format"}


async def ga_predict_links(module_ids: list[str]):
    sys = load_profile("graph_analyst")
    user = f"Predict missing depends edges among modules: {module_ids}"
    schema = load_schema("edge_suggestion_schema")
    suggestions = _call("gpt-4o-mini", sys, user, schema)
    # write edges back
    for edge in suggestions.get("edges", []):
        modify(
            operation="insert",
            collection="depends",
            document={
                "_from": f"modules/{edge['from']}",
                "_to": f"modules/{edge['to']}",
            },
        )
    return suggestions


async def qc_vector_health(collection: str = "research_docs", threshold: float = 0.8):
    sys = load_profile("vector_health")
    # find docs needing vectors/confidence < threshold
    docs_result = search(
        search_type="recent", collection=collection, hours=8760, limit=1000
    )
    docs = (
        docs_result.get("result", {}).get("results", [])
        if docs_result.get("result", {}).get("success")
        else []
    )
    missing = [
        d["_key"]
        for d in docs
        if d.get("confidence", 1) < threshold or not d.get("vector")
    ]
    if not missing:
        return {"doc_ids": []}
    user = f"Generate embeddings (768 dim) for documents: {missing[:20]} (only show first 20 ids)."
    schema = load_schema("vector_health_schema")
    resp = _call("gpt-4o-mini", sys, user, schema)
    # Fake vector; in reality call embeddings API
    for key in resp["doc_ids"]:
        modify(
            operation="update",
            collection=collection,
            key=key,
            updates={"vector": [0.0] * 3, "confidence": threshold + 0.05},
        )
    return resp


### AI Assistant Enhancement Agent Handlers ###


async def context_builder_get_context(topic: str, include_collections: list = None):
    """Build comprehensive context for a topic by querying knowledge database"""
    sys = load_profile("context_builder")

    if not include_collections:
        include_collections = ["rules", "heuristics", "memories", "research_docs"]

    # Query each collection for relevant information
    context_data = {}
    for collection in include_collections:
        try:
            result = search(
                search_type="content", collection=collection, content=topic, limit=10
            )
            if result.get("result", {}).get("success"):
                context_data[collection] = result["result"].get("results", [])
            else:
                context_data[collection] = []
        except Exception as e:
            print(f"Error querying {collection}: {e}")
            context_data[collection] = []

    user = f"""Build comprehensive context for: {topic}

Available data from collections:
{json.dumps(context_data, indent=2)}

Synthesize this into a structured context brief that helps an AI assistant understand the full background."""

    schema = load_schema("context_builder_schema")
    result = _call("gpt-4o-mini", sys, user, schema)
    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def rule_synthesizer_synthesize_rules(use_case: str, mode: str = "curated_list"):
    """Synthesize relevant rules for a specific use case"""
    sys = load_profile("rule_synthesizer")

    # Search for all potentially relevant rules
    rules_result = search(
        search_type="content", collection="rules", content=use_case, limit=50
    )

    rules_data = (
        rules_result.get("result", {}).get("results", [])
        if rules_result.get("result", {}).get("success")
        else []
    )

    user = f"""Analyze and synthesize rules for use case: {use_case}

Mode: {mode} (either 'curated_list' or 'custom_rule')

Available rules:
{json.dumps(rules_data, indent=2)}

If mode is 'curated_list': Return the most relevant rules with explanations
If mode is 'custom_rule': Synthesize relevant rules into one comprehensive custom rule"""

    schema = load_schema("rule_synthesizer_schema")
    result = _call("gpt-4o-mini", sys, user, schema)
    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def knowledge_onboarding_get_briefing(scope: str = "comprehensive"):
    """Get comprehensive knowledge briefing for AI assistant onboarding"""
    sys = load_profile("knowledge_onboarding")

    # Query multiple collections for comprehensive briefing
    collections_data = {}

    collections = ["rules", "heuristics", "memories", "research_docs", "metrics"]
    for collection in collections:
        try:
            result = search(
                search_type="recent",
                collection=collection,
                hours=168,  # Last week
                limit=20,
            )
            if result.get("result", {}).get("success"):
                collections_data[collection] = result["result"].get("results", [])
            else:
                collections_data[collection] = []
        except Exception as e:
            print(f"Error querying {collection}: {e}")
            collections_data[collection] = []

    # Get system health
    try:
        health_data = manage(action="health")
        system_health = health_data.get("result", {})
    except Exception as e:
        system_health = {"error": str(e)}

    user = f"""Create comprehensive knowledge briefing for scope: {scope}

Available data from all collections:
{json.dumps(collections_data, indent=2)}

System health data:
{json.dumps(system_health, indent=2)}

Create a dense, informative briefing that gives an AI assistant everything needed to work effectively."""

    schema = load_schema("knowledge_onboarding_schema")
    result = _call("gpt-4o-mini", sys, user, schema)
    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def memory_manager_store_memory(
    content: str, memory_type: str, context: str = "", tags: list = None
):
    """Store a new memory/insight in the knowledge base"""
    sys = load_profile("memory_manager")

    if not tags:
        tags = []

    user = f"""Store this memory in the knowledge base:
Content: {content}
Type: {memory_type}
Context: {context}
Suggested Tags: {tags}

Analyze the content and determine appropriate categorization, additional tags, and storage format."""

    schema = load_schema("memory_manager_schema")
    result = _call("gpt-4o-mini", sys, user, schema)

    # Actually store the memory if successful
    if isinstance(result, dict) and result.get("success"):
        try:
            store_result = modify(
                operation="insert",
                collection="memories",
                document={
                    "content": content,
                    "memory_type": memory_type,
                    "context": context,
                    "tags": tags,
                    "confidence": result.get("stored_memory", {}).get(
                        "confidence", 0.8
                    ),
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "memory_manager",
                },
            )
            if store_result.get("result", {}).get("success"):
                result["stored_memory"]["memory_id"] = store_result["result"].get(
                    "document_key", "unknown"
                )
        except Exception as e:
            result["error"] = f"Failed to store memory: {str(e)}"

    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def memory_manager_retrieve_memories(
    query: str, context: str = "", memory_types: list = None, min_relevance: float = 0.5
):
    """Retrieve relevant memories from the knowledge base"""
    sys = load_profile("memory_manager")

    # Search memories collection
    memories_result = search(
        search_type="content", collection="memories", content=query, limit=20
    )

    memories_data = (
        memories_result.get("result", {}).get("results", [])
        if memories_result.get("result", {}).get("success")
        else []
    )

    # Also search heuristics for additional insights
    heuristics_result = search(
        search_type="content", collection="heuristics", content=query, limit=10
    )

    heuristics_data = (
        heuristics_result.get("result", {}).get("results", [])
        if heuristics_result.get("result", {}).get("success")
        else []
    )

    user = f"""Retrieve and rank memories relevant to: {query}
Context: {context}
Memory Types Filter: {memory_types}
Minimum Relevance: {min_relevance}

Available memories:
{json.dumps(memories_data, indent=2)}

Additional insights from heuristics:
{json.dumps(heuristics_data, indent=2)}

Rank by relevance and provide reasoning for each match."""

    schema = load_schema("memory_manager_schema")
    result = _call("gpt-4o-mini", sys, user, schema)
    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def preference_tracker_capture_preference(
    preference_text: str, context: str, evidence: str = ""
):
    """Capture a user preference"""
    sys = load_profile("preference_tracker")

    user = f"""Capture and analyze this user preference:
Preference: {preference_text}
Context: {context}
Evidence: {evidence}

Determine strength, domain, type, and how to store this preference."""

    schema = load_schema("preference_tracker_schema")
    result = _call("gpt-4o-mini", sys, user, schema)

    # Store captured preferences
    if isinstance(result, dict) and result.get("success"):
        for pref in result.get("captured_preferences", []):
            try:
                modify(
                    operation="insert",
                    collection="preferences",
                    document={
                        "preference_text": pref["preference_text"],
                        "domain": pref["domain"],
                        "strength": pref["strength"],
                        "confidence": pref["confidence"],
                        "evidence": pref["evidence"],
                        "context": context,
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "source": "preference_tracker",
                    },
                )
            except Exception as e:
                print(f"Error storing preference: {e}")

    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def preference_tracker_get_preferences(
    context: str, return_reasoning: bool = True
):
    """Get applicable preferences for a context"""
    sys = load_profile("preference_tracker")

    # Search for relevant preferences
    prefs_result = search(
        search_type="content", collection="preferences", content=context, limit=20
    )

    prefs_data = (
        prefs_result.get("result", {}).get("results", [])
        if prefs_result.get("result", {}).get("success")
        else []
    )

    user = f"""Find preferences applicable to context: {context}
Return Reasoning: {return_reasoning}

Available preferences:
{json.dumps(prefs_data, indent=2)}

Determine which preferences apply and provide recommendations."""

    schema = load_schema("preference_tracker_schema")
    result = _call("gpt-4o-mini", sys, user, schema)
    return result if isinstance(result, dict) else {"error": "Invalid response format"}


async def insight_synthesizer_consolidate(topic: str, merge_threshold: float = 0.8):
    """Consolidate related insights on a topic"""
    sys = load_profile("insight_synthesizer")

    # Find related insights across collections
    collections = ["heuristics", "memories", "research_docs"]
    insights_data = {}

    for collection in collections:
        try:
            result = search(
                search_type="content", collection=collection, content=topic, limit=30
            )
            if result.get("result", {}).get("success"):
                insights_data[collection] = result["result"].get("results", [])
            else:
                insights_data[collection] = []
        except Exception:
            insights_data[collection] = []

    user = f"""Consolidate insights for topic: {topic}
Merge Threshold: {merge_threshold}

Available insights from collections:
{json.dumps(insights_data, indent=2)}

Identify related insights, analyze relationships, and synthesize into unified knowledge."""

    schema = load_schema("insight_synthesizer_schema")
    result = _call("gpt-4o-mini", sys, user, schema)

    # Store synthesized insight if successful
    if (
        isinstance(result, dict)
        and result.get("success")
        and result.get("synthesized_insight")
    ):
        try:
            modify(
                operation="insert",
                collection="heuristics",
                document={
                    "content": result["synthesized_insight"]["content"],
                    "title": result["synthesized_insight"]["title"],
                    "source_insights": result["synthesized_insight"]["source_insights"],
                    "confidence": result["synthesized_insight"]["confidence"],
                    "tags": result["synthesized_insight"]["tags"],
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "insight_synthesizer",
                    "synthesis_method": result["synthesized_insight"][
                        "synthesis_method"
                    ],
                },
            )
        except Exception as e:
            print(f"Error storing synthesized insight: {e}")

    return result if isinstance(result, dict) else {"error": "Invalid response format"}


@app.get("/graph/svg")
async def graph_svg():
    # build depends graph
    modules_result = search(
        search_type="type", collection="modules", document_type="module", limit=1000
    )
    modules = (
        modules_result.get("result", {}).get("results", [])
        if modules_result.get("result", {}).get("success")
        else []
    )

    edges_result = search(
        search_type="type", collection="depends", document_type="edge", limit=5000
    )
    edges = (
        edges_result.get("result", {}).get("results", [])
        if edges_result.get("result", {}).get("success")
        else []
    )

    g = nx.DiGraph()
    for m in modules:
        g.add_node(m["_key"])
    for e in edges:
        g.add_edge(e["_from"].split("/")[1], e["_to"].split("/")[1])
    dot_str = nx.nx_pydot.to_pydot(g).to_string()
    svg_data = pydot.graph_from_dot_data(dot_str)[0].create(format="svg")
    return Response(content=svg_data, media_type="image/svg+xml")


@app.get("/metrics")
async def hub_metrics():
    data = manage(action="health")  # reuse manage tool for quick stats
    data["version"] = "structured_outputs_v2"  # Version indicator
    data["structured_outputs_enabled"] = True
    return JSONResponse(content=data)


@app.get("/health")
async def health_check():
    """Health check endpoint for agent discovery"""
    try:
        # Get database health
        db_health = manage(action="health")
        db_status = db_health.get("result", {}).get("status", "unknown")

        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_health.get("result", {}),
            "agents": {
                "total": 5,
                "available": [
                    "dev_agent",
                    "sentinel",
                    "kb_updater",
                    "graph_analyst",
                    "quality_curator",
                ],
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/discovery/manifest")
async def discovery_manifest():
    """Agent discovery manifest for external agents"""
    return {
        "agent_id": "agent-hub-001",
        "name": "Agent Hub MCP",
        "description": "Multi-agent system with 5 specialized AI agents",
        "provider": "Agent World",
        "version": "1.0.0",
        "protocols": ["agent-protocol", "json-rpc"],
        "endpoints": {
            "base": "http://localhost:8003",
            "rpc": "http://localhost:8003/rpc",
            "agent_protocol": "http://localhost:8003/ap/v1/agent",
            "health": "http://localhost:8003/health",
            "dashboard": "http://localhost:8003/",
        },
        "capabilities": [
            {
                "name": "codeGeneration",
                "description": "Generate code patches with git integration",
                "methods": ["dev_agent.generate_feature"],
                "ans_name": "agent-protocol://codeGeneration.AgentHub.v1.0",
            },
            {
                "name": "securityAudit",
                "description": "Security compliance auditing",
                "methods": ["sentinel.audit_patch"],
                "ans_name": "agent-protocol://securityAudit.AgentHub.v1.0",
            },
            {
                "name": "knowledgeExtraction",
                "description": "Extract insights from research documents",
                "methods": ["kb_updater.digest_research"],
                "ans_name": "agent-protocol://knowledgeExtraction.AgentHub.v1.0",
            },
            {
                "name": "dependencyAnalysis",
                "description": "Analyze module dependencies",
                "methods": ["graph_analyst.predict_links"],
                "ans_name": "agent-protocol://dependencyAnalysis.AgentHub.v1.0",
            },
            {
                "name": "qualityAssurance",
                "description": "Vector health and quality checks",
                "methods": ["quality_curator.vector_healthcheck"],
                "ans_name": "agent-protocol://qualityAssurance.AgentHub.v1.0",
            },
        ],
    }


@app.get("/discovery/capabilities")
async def discovery_capabilities():
    """List available agent capabilities"""
    manifest = await discovery_manifest()
    return manifest["capabilities"]


@app.get("/ans/resolve/{ans_name:path}")
async def resolve_ans_name(ans_name: str):
    """Resolve Agent Name Service (ANS) name to endpoints"""
    manifest = await discovery_manifest()

    for capability in manifest["capabilities"]:
        if capability["ans_name"] == ans_name:
            return {
                "ans_name": ans_name,
                "agent_id": manifest["agent_id"],
                "endpoints": manifest["endpoints"],
                "capabilities": [capability],
                "verified": True,
            }

    raise HTTPException(status_code=404, detail="Agent not found for ANS name")


@app.get("/version")
async def version_info():
    """Version endpoint to confirm server code version"""
    return {
        "version": "structured_outputs_v2",
        "structured_outputs_enabled": True,
        "openai_api_configured": bool(os.environ.get("OPENAI_API_KEY")),
    }
