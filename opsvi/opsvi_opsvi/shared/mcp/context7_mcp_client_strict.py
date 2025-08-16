from .context7_mcp_client import (
    CallToolResult,
    Context7MCPClient,
    LibraryInfo,
    TextContent,
)


class StrictContext7MCPClient(Context7MCPClient):
    """
    Strict, OAMAT-compliant Context7 MCP client.
    - Only accepts a valid JSON array of libraries from the LLM.
    - No fallback parsing. If the LLM does not return a valid array, raises an error.
    - Use for workflows that require strict, schema-enforced, no-fallback extraction.
    """

    def _parse_library_results(self, tool_result: CallToolResult) -> list[LibraryInfo]:
        libraries = []
        try:
            if not tool_result.content:
                return libraries
            content = tool_result.content[0]
            if isinstance(content, TextContent):
                blocks = content.text.split("----------")
                for block in blocks:
                    name = None
                    context7_id = None
                    description = None
                    trust_score = None
                    for line in block.splitlines():
                        if line.strip().startswith("- Title:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.strip().startswith(
                            "- Context7-compatible library ID:"
                        ):
                            context7_id = line.split(":", 1)[1].strip()
                        elif line.strip().startswith("- Description:"):
                            description = line.split(":", 1)[1].strip()
                        elif line.strip().startswith("- Trust Score:"):
                            try:
                                trust_score = float(line.split(":", 1)[1].strip())
                            except Exception:
                                trust_score = None
                    if name and context7_id and description and trust_score is not None:
                        libraries.append(
                            {
                                "name": name,
                                "context7_id": context7_id,
                                "description": description,
                                "trust_score": trust_score,
                            }
                        )
                print(f"[DEBUG] Parsed libraries: {libraries}")
                if not libraries:
                    raise ValueError("No libraries found in Context7 MCP output.")
                # Optionally: sort or select best match here
                from src.shared.mcp.context7_mcp_client import LibraryInfo

                library_objs = []
                for lib in libraries:
                    library_objs.append(
                        LibraryInfo(
                            library_id=lib["context7_id"],
                            name=lib["name"],
                            description=lib["description"],
                            trust_score=lib["trust_score"],
                        )
                    )
                print(f"[DEBUG] LibraryInfo objects: {library_objs}")
                if not library_objs:
                    raise ValueError("No libraries found in Context7 MCP output.")
                return library_objs
        except Exception as e:
            import traceback

            print(f"Exception: {e}")
            print(traceback.format_exc())
        return libraries
