#!/usr/bin/env python3
"""
Semantic Code Analyzer - Understands code structure, not just text
Extracts real relationships: CALLS, IMPLEMENTS, EXTENDS, HANDLES, IMPORTS
This is what I ACTUALLY need to understand code properly
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    """Represents a code entity (function, class, etc.)"""

    entity_type: str  # 'function', 'class', 'method'
    name: str
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None


@dataclass
class CodeRelationship:
    """Represents a relationship between code entities"""

    from_entity: str  # Full qualified name
    to_entity: str
    relationship_type: str  # CALLS, EXTENDS, IMPLEMENTS, HANDLES, IMPORTS, RETURNS, USES
    file_path: str
    line_number: int
    context: Optional[str] = None  # Additional context


class SemanticCodeAnalyzer(ast.NodeVisitor):
    """
    Analyzes Python code to extract semantic relationships
    This gives me actual code intelligence, not just text matching
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_class = None
        self.current_function = None
        self.entities: List[CodeEntity] = []
        self.relationships: List[CodeRelationship] = []
        self.imports: Dict[str, str] = {}  # alias -> full module path

    def visit_Import(self, node: ast.Import) -> None:
        """Track imports"""
        for alias in node.names:
            import_name = alias.name
            import_alias = alias.asname or alias.name
            self.imports[import_alias] = import_name

            self.relationships.append(
                CodeRelationship(
                    from_entity=self.file_path,
                    to_entity=import_name,
                    relationship_type="IMPORTS",
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports"""
        module = node.module or ""
        for alias in node.names:
            import_name = f"{module}.{alias.name}"
            import_alias = alias.asname or alias.name
            self.imports[import_alias] = import_name

            self.relationships.append(
                CodeRelationship(
                    from_entity=self.file_path,
                    to_entity=import_name,
                    relationship_type="IMPORTS",
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class definitions and inheritance"""

        # Get base classes (inheritance)
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
                self.relationships.append(
                    CodeRelationship(
                        from_entity=node.name,
                        to_entity=base.id,
                        relationship_type="EXTENDS",
                        file_path=self.file_path,
                        line_number=node.lineno,
                    )
                )
            elif isinstance(base, ast.Attribute):
                base_name = self._get_full_name(base)
                bases.append(base_name)
                self.relationships.append(
                    CodeRelationship(
                        from_entity=node.name,
                        to_entity=base_name,
                        relationship_type="EXTENDS",
                        file_path=self.file_path,
                        line_number=node.lineno,
                    )
                )

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        self.entities.append(
            CodeEntity(
                entity_type="class",
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                docstring=docstring,
                decorators=decorators,
            )
        )

        # Track current class for methods
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function/method definitions"""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Extract async function/method definitions"""
        self._visit_function(node)

    def _visit_function(self, node) -> None:
        """Common function processing for sync and async"""

        # Determine if it's a method or function
        entity_type = "method" if self.current_class else "function"
        full_name = (
            f"{self.current_class}.{node.name}" if self.current_class else node.name
        )

        # Get parameters
        params = []
        for arg in node.args.args:
            params.append(arg.arg)

        # Get return type if annotated
        returns = None
        if node.returns:
            returns = self._get_annotation_name(node.returns)

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Check if async
        if isinstance(node, ast.AsyncFunctionDef):
            decorators.append("async")

        # Get docstring
        docstring = ast.get_docstring(node)

        self.entities.append(
            CodeEntity(
                entity_type=entity_type,
                name=full_name,
                file_path=self.file_path,
                line_number=node.lineno,
                docstring=docstring,
                parameters=params,
                returns=returns,
                decorators=decorators,
                parent_class=self.current_class,
            )
        )

        # Track current function for calls
        old_function = self.current_function
        self.current_function = full_name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node: ast.Call) -> None:
        """Track function calls"""
        if self.current_function:
            called_name = self._get_call_name(node.func)
            if called_name:
                self.relationships.append(
                    CodeRelationship(
                        from_entity=self.current_function,
                        to_entity=called_name,
                        relationship_type="CALLS",
                        file_path=self.file_path,
                        line_number=node.lineno,
                    )
                )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Track exception handling"""
        if self.current_function:
            for handler in node.handlers:
                if handler.type:
                    exc_type = self._get_exception_name(handler.type)
                    self.relationships.append(
                        CodeRelationship(
                            from_entity=self.current_function,
                            to_entity=exc_type,
                            relationship_type="HANDLES",
                            file_path=self.file_path,
                            line_number=handler.lineno,
                            context=f"Exception handler in {self.current_function}",
                        )
                    )
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        """Track exceptions raised"""
        if self.current_function and node.exc:
            if isinstance(node.exc, ast.Call):
                exc_type = self._get_call_name(node.exc.func)
            elif isinstance(node.exc, ast.Name):
                exc_type = node.exc.id
            else:
                exc_type = "Exception"

            self.relationships.append(
                CodeRelationship(
                    from_entity=self.current_function,
                    to_entity=exc_type,
                    relationship_type="RAISES",
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def _get_full_name(self, node) -> str:
        """Get full qualified name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_full_name(node.value)
            return f"{value}.{node.attr}"
        return "unknown"

    def _get_call_name(self, node) -> Optional[str]:
        """Get the name being called"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_full_name(node)
        return None

    def _get_decorator_name(self, node) -> str:
        """Get decorator name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_full_name(node)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return "decorator"

    def _get_annotation_name(self, node) -> str:
        """Get type annotation name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "Any"

    def _get_exception_name(self, node) -> str:
        """Get exception type name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_full_name(node)
        return "Exception"


class CodeIntelligenceBuilder:
    """
    Builds semantic code intelligence in Neo4j
    This is what transforms text search into code understanding
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_auth: tuple = ("neo4j", "password"),
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

    def analyze_file(
        self, file_path: str, content: str
    ) -> Tuple[List[CodeEntity], List[CodeRelationship]]:
        """Analyze a Python file and extract semantic information"""

        try:
            tree = ast.parse(content)
            analyzer = SemanticCodeAnalyzer(file_path)
            analyzer.visit(tree)
            return analyzer.entities, analyzer.relationships
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return [], []

    def store_code_intelligence(
        self,
        file_path: str,
        entities: List[CodeEntity],
        relationships: List[CodeRelationship],
    ) -> int:
        """Store code intelligence in Neo4j"""

        stored_count = 0

        with self.driver.session() as session:
            # Store entities as nodes
            for entity in entities:
                query = """
                    MERGE (e:CodeEntity {
                        name: $name,
                        file_path: $file_path
                    })
                    SET e.entity_type = $entity_type,
                        e.line_number = $line_number,
                        e.docstring = $docstring,
                        e.param_list = $param_list,
                        e.returns = $returns,
                        e.decorators = $decorators,
                        e.parent_class = $parent_class
                    RETURN e
                """

                result = session.run(
                    query,
                    name=entity.name,
                    file_path=entity.file_path,
                    entity_type=entity.entity_type,
                    line_number=entity.line_number,
                    docstring=entity.docstring,
                    param_list=entity.parameters,  # Changed from parameters to param_list
                    returns=entity.returns,
                    decorators=entity.decorators,
                    parent_class=entity.parent_class,
                )
                stored_count += 1

            # Store relationships
            for rel in relationships:
                # Create appropriate relationship based on type
                if rel.relationship_type == "CALLS":
                    query = """
                        MERGE (from:CodeEntity {name: $from_entity})
                        MERGE (to:CodeEntity {name: $to_entity})
                        MERGE (from)-[r:CALLS {
                            file_path: $file_path,
                            line_number: $line_number
                        }]->(to)
                    """
                elif rel.relationship_type == "EXTENDS":
                    query = """
                        MERGE (from:CodeEntity {name: $from_entity})
                        MERGE (to:CodeEntity {name: $to_entity})
                        MERGE (from)-[r:EXTENDS {
                            file_path: $file_path,
                            line_number: $line_number
                        }]->(to)
                    """
                elif rel.relationship_type == "HANDLES":
                    query = """
                        MERGE (from:CodeEntity {name: $from_entity})
                        MERGE (exc:Exception {name: $to_entity})
                        MERGE (from)-[r:HANDLES {
                            file_path: $file_path,
                            line_number: $line_number,
                            context: $context
                        }]->(exc)
                    """
                elif rel.relationship_type == "RAISES":
                    query = """
                        MERGE (from:CodeEntity {name: $from_entity})
                        MERGE (exc:Exception {name: $to_entity})
                        MERGE (from)-[r:RAISES {
                            file_path: $file_path,
                            line_number: $line_number
                        }]->(exc)
                    """
                elif rel.relationship_type == "IMPORTS":
                    query = """
                        MERGE (from:SourceFile {path: $from_entity})
                        MERGE (module:Module {name: $to_entity})
                        MERGE (from)-[r:IMPORTS {
                            line_number: $line_number
                        }]->(module)
                    """
                else:
                    continue

                session.run(
                    query,
                    from_entity=rel.from_entity,
                    to_entity=rel.to_entity,
                    file_path=rel.file_path,
                    line_number=rel.line_number,
                    context=rel.context,
                )

        return stored_count

    def find_callers(self, function_name: str) -> List[str]:
        """Find all functions that call a given function"""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (caller:CodeEntity)-[:CALLS]->(callee:CodeEntity)
                WHERE callee.name = $function_name
                RETURN DISTINCT caller.name as caller, caller.file_path as file
            """,
                function_name=function_name,
            )

            return [(record["caller"], record["file"]) for record in result]

    def find_implementations(self, base_class: str) -> List[str]:
        """Find all classes that extend a base class"""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (child:CodeEntity)-[:EXTENDS]->(parent:CodeEntity)
                WHERE parent.name = $base_class
                RETURN DISTINCT child.name as implementation, child.file_path as file
            """,
                base_class=base_class,
            )

            return [(record["implementation"], record["file"]) for record in result]

    def find_error_handlers(self, exception_type: str) -> List[Dict]:
        """Find all code that handles a specific exception"""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (handler:CodeEntity)-[r:HANDLES]->(exc:Exception)
                WHERE exc.name = $exception_type
                RETURN handler.name as handler,
                       handler.file_path as file,
                       r.context as context
            """,
                exception_type=exception_type,
            )

            handlers = []
            for record in result:
                handlers.append(
                    {
                        "handler": record["handler"],
                        "file": record["file"],
                        "context": record["context"],
                    }
                )

            return handlers

    def get_function_graph(self, function_name: str, depth: int = 2) -> Dict:
        """Get the call graph for a function"""

        with self.driver.session() as session:
            # Get what this function calls
            calls_result = session.run(
                f"""
                MATCH path = (func:CodeEntity {{name: $function_name}})-[:CALLS*1..{depth}]->(called:CodeEntity)
                RETURN DISTINCT called.name as name, length(path) as distance
                ORDER BY distance
            """,
                function_name=function_name,
            )

            calls = [(record["name"], record["distance"]) for record in calls_result]

            # Get what calls this function
            called_by_result = session.run(
                f"""
                MATCH path = (caller:CodeEntity)-[:CALLS*1..{depth}]->(func:CodeEntity {{name: $function_name}})
                RETURN DISTINCT caller.name as name, length(path) as distance
                ORDER BY distance
            """,
                function_name=function_name,
            )

            called_by = [
                (record["name"], record["distance"]) for record in called_by_result
            ]

            return {"function": function_name, "calls": calls, "called_by": called_by}

    def close(self):
        """Clean up"""
        self.driver.close()


# Example usage
if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/home/opsvi/master_root")

    # Test with a real Python file
    test_file = "/home/opsvi/.reference/openai-python/examples/streaming.py"

    if Path(test_file).exists():
        content = Path(test_file).read_text()

        builder = CodeIntelligenceBuilder()
        entities, relationships = builder.analyze_file(test_file, content)

        print(f"Analyzing: {test_file}")
        print("=" * 60)
        print(f"Found {len(entities)} entities:")
        for entity in entities[:5]:
            print(f"  {entity.entity_type}: {entity.name}")
            if entity.docstring:
                print(f"    Doc: {entity.docstring[:50]}...")

        print(f"\nFound {len(relationships)} relationships:")
        rel_types = {}
        for rel in relationships:
            rel_types[rel.relationship_type] = (
                rel_types.get(rel.relationship_type, 0) + 1
            )

        for rel_type, count in rel_types.items():
            print(f"  {rel_type}: {count}")

        # Store in Neo4j
        stored = builder.store_code_intelligence(test_file, entities, relationships)
        print(f"\nStored {stored} entities in Neo4j")

        # Test queries
        print("\nTesting semantic queries:")

        # Find what calls a function
        if entities:
            first_func = next(
                (e for e in entities if e.entity_type == "function"), None
            )
            if first_func:
                callers = builder.find_callers(first_func.name)
                print(f"\nFunctions that call {first_func.name}: {callers}")

        builder.close()
    else:
        print(f"Test file not found: {test_file}")
