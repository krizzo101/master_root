# ACCF Integrations Directory Tree (Planned Scope)

This file maps full-scope capabilities to concrete directories/files under each library/package. It is a planning artifact to guide adapter scaffolding and implementation.

```
libs/
├── opsvi-llm/
│   ├── README.md
│   ├── pyproject.toml              # extras: [openai, anthropic, google, cohere, mistral, together, groq, nvidia, azure, vertex, xai, deepseek, perplexity, bedrock, gateways]
│   └── opsvi_llm/
│       ├── providers/
│       │   ├── interfaces.py       # LLMProvider, EmbeddingsProvider contracts
│       │   ├── openai_provider.py
│       │   ├── anthropic_provider.py
│       │   ├── google_gemini_provider.py
│       │   ├── cohere_provider.py
│       │   ├── mistral_provider.py
│       │   ├── together_provider.py
│       │   ├── groq_provider.py
│       │   ├── nvidia_nim_provider.py
│       │   ├── azure_openai_provider.py
│       │   ├── vertex_ai_provider.py
│       │   ├── xai_grok_provider.py
│       │   ├── deepseek_provider.py
│       │   ├── perplexity_provider.py
│       │   └── bedrock_provider.py
│       ├── gateways/
│       │   ├── openrouter_gateway.py
│       │   ├   litellm_gateway.py
│       │   └── portkey_gateway.py
│       ├── embeddings/
│       │   ├── openai_embeddings.py
│       │   ├── cohere_embeddings.py
│       │   ├── voyage_embeddings.py
│       │   ├── jina_embeddings.py
│       │   ├── bge_embeddings.py
│       │   └── nv_embed.py
│       ├── rerankers/
│       │   ├── cohere_rerank.py
│       │   ├── jina_rerank.py
│       │   ├── voyage_rerank.py
│       │   └── colbert_v2.py
│       ├── policies/
│       │   ├── rate_limit.py       # backoff, 429 handling
│       │   └── budget_policy.py    # token/cost budgets
│       ├── prompts/
│       └── schemas/
│
├── opsvi-rag/
│   ├── README.md
│   ├── pyproject.toml              # extras: [pinecone, weaviate, qdrant, milvus, vespa, faiss, chroma, pgvector, opensearch, lancedb]
│   └── opsvi_rag/
│       ├── vectorstores/
│       │   ├── interfaces.py       # VectorStore contract
│       │   ├── pinecone_adapter.py
│       │   ├── weaviate_adapter.py
│       │   ├── qdrant_adapter.py
│       │   ├── milvus_adapter.py
│       │   ├── vespa_adapter.py
│       │   ├── faiss_adapter.py
│       │   ├── chroma_adapter.py
│       │   ├── pgvector_adapter.py
│       │   ├── opensearch_adapter.py
│       │   └── lancedb_adapter.py
│       ├── retrievers/
│       │   └── hybrid_retriever.py # vector + lexical signals
│       ├── embeddings/
│       │   └── providers_proxy.py  # reuse opsvi-llm embeddings
│       ├── rerankers/
│       │   └── providers_proxy.py  # reuse opsvi-llm rerankers
│       ├── ingestors/
│       │   ├── unstructured_ingestor.py
│       │   ├── tika_ingestor.py
│       │   ├── playwright_crawler.py
│       │   ├── firecrawl_ingestor.py
│       │   └── arxiv_ingestor.py
│       ├── chunkers/
│       │   ├── recursive_chunker.py
│       │   ├── semantic_chunker.py
│       │   └── code_aware_chunker.py
│       ├── configs/
│       │   └── vector_settings.py
│       └── pipelines/
│           └── ingest.py
│
├── opsvi-data/
│   ├── README.md
│   ├── pyproject.toml              # extras: [postgres, mysql, sqlite, duckdb, bigquery, snowflake, redshift, clickhouse, neo4j, memgraph, neptune, janusgraph, tigergraph, arangodb, rdf]
│   └── opsvi_data/
│       ├── providers/
│       │   ├── sql/
│       │   │   ├── postgres_adapter.py
│       │   │   ├── mysql_adapter.py
│       │   │   ├── sqlite_adapter.py
│       │   │   ├── duckdb_adapter.py
│       │   │   ├── bigquery_adapter.py
│       │   │   ├── snowflake_adapter.py
│       │   │   ├── redshift_adapter.py
│       │   │   └── clickhouse_adapter.py
│       │   ├── graph/
│       │   │   ├── interfaces.py    # GraphStore contract
│       │   │   ├── neo4j_adapter.py
│       │   │   ├── memgraph_adapter.py
│       │   │   ├── neptune_adapter.py
│       │   │   ├── janusgraph_adapter.py
│       │   │   ├── tigergraph_adapter.py
│       │   │   ├── arangodb_adapter.py
│       │   │   └── rdf_sparql_adapter.py
│       │   └── featurestores/
│       │       └── feast_adapter.py
│       ├── lineage/
│       │   └── openlineage_adapter.py
│       └── config/
│           └── graph_settings.py
│
├── opsvi-orchestration/
│   ├── README.md
│   ├── pyproject.toml              # extras: [crewai, metagpt, autogen, langgraph, assistants]
│   └── opsvi_orchestration/
│       ├── integrations/
│       │   ├── agent_runners/
│       │   │   ├── crewai_runner.py
│       │   │   ├── metagpt_runner.py
│       │   │   ├── autogen_runner.py
│       │   │   ├── langgraph_runner.py
│       │   │   └── assistants_v2_runner.py
│       │   ├── research_tools/
│       │   │   ├── firecrawl_tool.py
│       │   │   ├── brave_search_tool.py
│       │   │   ├── serpapi_tool.py
│       │   │   ├── tavily_tool.py
│       │   │   └── apify_tool.py
│       │   └── chains/
│       │       └── langchain_runner.py
│       └── tools/
│           ├── web_browser.py
│           ├── bash_tool.py
│           └── code_execution.py
│
├── gatekeeper/
│   ├── README.md
│   └── gatekeeper/
│       ├── contracts/
│       │   ├── request.schema.json
│       │   ├── response.schema.json
│       │   └── policy.schema.json
│       ├── adapters/
│       │   ├── context_resolver.py     # .proj-intel, opsvi-rag, FS
│       │   └── llm_analyzer.py         # opsvi-llm provider
│       └── policies/
│           ├── safety.yaml
│           └── cost_caps.yaml
│
├── opsvi-monitoring/
│   ├── README.md
│   └── opsvi_monitoring/
│       ├── tracing/
│       │   ├── langfuse_exporter.py
│       │   └── otel_exporter.py
│       ├── eval/
│       │   ├── ragas_runner.py
│       │   ├── deepeval_runner.py
│       │   └── promptfoo_runner.py
│       └── dashboards/
│           └── grafana/
│               └── dashboards.json
│
├── opsvi-security/
│   ├── README.md
│   └── opsvi_security/
│       ├── scanners/
│       │   ├── bandit_runner.py
│       │   ├── safety_runner.py
│       │   ├── gitleaks_runner.py
│       │   └── trivy_runner.py
│       ├── policy/
│       │   ├── opa_adapter.py
│       │   └── cedar_policy.py
│       └── secrets/
│           ├── vault_adapter.py
│           ├── aws_secrets_adapter.py
│           └── gcp_secret_manager_adapter.py
│
├── opsvi-gateway/
│   ├── README.md
│   └── opsvi_gateway/
│       ├── adapters/
│       │   ├── kong_adapter.py
│       │   ├── envoy_adapter.py
│       │   ├── tyk_adapter.py
│       │   └── nginx_adapter.py
│       └── middlewares/
│           ├── auth_middleware.py      # auth0, keycloak, ory
│           └── rate_limit_middleware.py
│
├── opsvi-http/
│   ├── README.md
│   └── opsvi_http/
│       ├── openapi.yaml
│       └── middlewares/
│           ├── auth/
│           ├── logging/
│           └── cors/
│
├── opsvi-pipeline/
│   ├── README.md
│   └── opsvi_pipeline/
│       ├── jobs/
│       │   └── etl_job_template.py
│       ├── streaming/
│       │   ├── kafka_consumer.py
│       │   ├── redpanda_consumer.py
│       │   ├── pulsar_consumer.py
│       │   └── nats_consumer.py
│       └── dq/
│           └── great_expectations_runner.py
│
└── opsvi-deploy/
    ├── README.md
    └── opsvi_deploy/
        ├── k8s/
        │   └── helm/
        │       └── charts/
        ├── serverless/
        │   ├── aws_lambda_templates/
        │   └── gcp_cloud_run/
        └── edge/
            └── cloudflare_worker_template/
```

Notes:
- Each adapter lives behind an interface; providers are optional dependencies via pyproject extras.
- Health checks, retries, timeouts, structured logs, and tests are implied for each adapter.
- Reuse opsvi-llm embeddings/rerankers via thin proxies in opsvi-rag to avoid duplication.
- Gatekeeper consumes `.proj-intel/`, vector RAG, and opsvi-llm for preflight analyses.
