"""
main.py
CLI entry point for the GraphRAG AI application.
Now supports semantic search over markdown directories.
"""

import argparse

from .graph_loader import (
    ingest_markdown_dir_with_progress,
    load_graph_from_csv,
    load_graph_from_json,
)
from .graph_query import (
    semantic_search,
    shortest_path,
)
from .llm_augment import augment_with_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="GraphRAG AI CLI")
    parser.add_argument("--csv", type=str, help="Path to edge list CSV file")
    parser.add_argument("--json", type=str, help="Path to adjacency list JSON file")
    parser.add_argument("--source", type=str, help="Source node for query")
    parser.add_argument("--target", type=str, help="Target node for query")
    parser.add_argument("--semantic-search", type=str, help="Semantic search query")
    parser.add_argument(
        "--md-dir", type=str, help="Directory of markdown files to ingest"
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of semantic search results"
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="text-embedding-3-large",
        help="OpenAI embedding model",
    )
    parser.add_argument(
        "--embedding-dim", type=int, default=1536, help="Embedding vector dimension"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=300, help="Chunk size in tokens"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=50, help="Token overlap between chunks"
    )
    parser.add_argument(
        "--llm-augment",
        action="store_true",
        default=True,
        help="Use LLM to synthesize answer from top-k results",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4.1-2025-04-14",
        help="OpenAI LLM model for answer synthesis (default: gpt-4.1-2025-04-14)",
    )
    parser.add_argument(
        "--arango-host", type=str, default=None, help="ArangoDB host URL"
    )
    parser.add_argument(
        "--arango-db", type=str, default=None, help="ArangoDB database name"
    )
    parser.add_argument(
        "--arango-user", type=str, default=None, help="ArangoDB username"
    )
    parser.add_argument(
        "--arango-pass", type=str, default=None, help="ArangoDB password"
    )
    parser.add_argument(
        "--arango-backend",
        action="store_true",
        default=False,
        help="Use ArangoDB for semantic search and retrieval",
    )
    args = parser.parse_args()

    if args.semantic_search and args.md_dir:
        print(f"Ingesting markdowns from {args.md_dir} and running semantic search...")
        G = ingest_markdown_dir_with_progress(
            args.md_dir,
            args.embedding_model,
            args.embedding_dim,
            args.chunk_size,
            args.chunk_overlap,
            arango_host=args.arango_host,
            arango_db=args.arango_db,
            arango_user=args.arango_user,
            arango_pass=args.arango_pass,
        )
        if args.arango_backend:
            from .graph_query import arango_semantic_search

            print("Running semantic search (ArangoDB backend)...")
            results = arango_semantic_search(
                args.semantic_search,
                top_k=args.top_k,
                model=args.embedding_model,
                dimensions=args.embedding_dim,
                arango_host=args.arango_host,
                arango_db=args.arango_db,
                arango_user=args.arango_user,
                arango_pass=args.arango_pass,
            )
            for r in results:
                print(
                    f"Score: {r['score']:.4f}\nFile: {r['file']} Chunk: {r['chunk_index']}\nText: {r['text'][:200]}\nArangoID: {r['arango_id']}\n{'-'*40}"
                )
            if args.llm_augment:
                print("\nSynthesizing answer with GPT-4.1...")
                context = "\n\n".join(r["text"] for r in results)
                answer = augment_with_graph(
                    args.semantic_search, context, model=args.llm_model
                )
                print(f"\nLLM-augmented answer:\n{answer}")
            return
        # ... existing in-memory search ...
        print("Running semantic search...")
        results = semantic_search(
            G, args.semantic_search, top_k=args.top_k, model=args.embedding_model
        )
        for node, score in results:
            data = G.nodes[node]
            print(
                f"Node: {node}\nScore: {score:.4f}\nFile: {data.get('file')} Chunk: {data.get('chunk_index')}\nText: {data.get('text')[:200]}\n{'-'*40}"
            )
        if args.llm_augment:
            print("\nSynthesizing answer with GPT-4.1...")
            context = "\n\n".join(G.nodes[node]["text"] for node, _ in results)
            answer = augment_with_graph(
                args.semantic_search, context, model=args.llm_model
            )
            print(f"\nLLM-augmented answer:\n{answer}")
        return

    if args.csv:
        G = load_graph_from_csv(args.csv)
    elif args.json:
        G = load_graph_from_json(args.json)
    else:
        print("Please provide a graph file with --csv or --json.")
        return

    if not args.source or not args.target:
        print("Please provide --source and --target nodes for the query.")
        return

    path = shortest_path(G, args.source, args.target)
    print(f"Shortest path: {path}")
    graph_info = f"Shortest path from {args.source} to {args.target}: {path}"
    answer = augment_with_graph(
        f"What is the shortest path from {args.source} to {args.target}?",
        graph_info,
    )
    print(f"LLM-augmented answer: {answer}")


if __name__ == "__main__":
    main()
