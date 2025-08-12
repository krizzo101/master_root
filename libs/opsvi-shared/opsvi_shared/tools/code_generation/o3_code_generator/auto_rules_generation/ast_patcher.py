import ast
from pathlib import Path

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class ASTPatcher(ast.NodeTransformer):
    """
    AST-based patcher for Python code. Removes print statements and fixes relative imports.
    Inserts 'pass' if removing the only statement in a block.
    """

    def __init__(self):
        self.logger = get_logger()
        super().__init__()

    def visit_Expr(self, node):
        # Remove print statements (Python 3+)
        if (
            isinstance(node.value, ast.Call)
            and getattr(node.value.func, "id", None) == "print"
        ):
            self.logger.log_info(
                f"Removing print statement at line {getattr(node, 'lineno', '?')}"
            )
            # Check if parent block has only this statement
            if hasattr(node, "_parent") and hasattr(node._parent, "body"):
                siblings = node._parent.body
                if len(siblings) == 1:
                    return ast.Pass(lineno=node.lineno, col_offset=node.col_offset)
            return None
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # Fix relative imports to absolute for o3_code_generator
        if node.module and node.module.startswith("."):
            abs_module = (
                "src.tools.code_generation.o3_code_generator." + node.module.lstrip(".")
            )
            self.logger.log_info(
                f"Fixing relative import '{node.module}' to '{abs_module}' at line {getattr(node, 'lineno', '?')}"
            )
            node.module = abs_module
        return node

    def generic_visit(self, node):
        # Attach parent references for block context
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        item._parent = node
            elif isinstance(value, ast.AST):
                value._parent = node
        node = super().generic_visit(node)
        # After visiting children, patch empty blocks
        if hasattr(node, "body") and isinstance(node.body, list):
            if len(node.body) == 0:
                self.logger.log_info(
                    f"Inserting pass in empty block at line {getattr(node, 'lineno', '?')}"
                )
                node.body.append(
                    ast.Pass(
                        lineno=getattr(node, "lineno", 0),
                        col_offset=getattr(node, "col_offset", 0),
                    )
                )
        # Patch else, orelse, finalbody blocks as well
        for block_attr in ["orelse", "finalbody"]:
            if hasattr(node, block_attr) and isinstance(
                getattr(node, block_attr), list
            ):
                block = getattr(node, block_attr)
                if len(block) == 0:
                    self.logger.log_info(
                        f"Inserting pass in empty {block_attr} at line {getattr(node, 'lineno', '?')}"
                    )
                    block.append(
                        ast.Pass(
                            lineno=getattr(node, "lineno", 0),
                            col_offset=getattr(node, "col_offset", 0),
                        )
                    )
        return node

    @staticmethod
    def patch_file(file_path: Path, output_path: Path | None = None) -> bool:
        logger = get_logger()
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
            patcher = ASTPatcher()
            new_tree = patcher.visit(tree)
            ast.fix_missing_locations(new_tree)
            try:
                # Python 3.9+
                new_code = ast.unparse(new_tree)
            except AttributeError:
                import astor

                new_code = astor.to_source(new_tree)
            # Validate patched code
            ast.parse(new_code)
            out_path = output_path or file_path
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            logger.log_info(f"Patched file written to {out_path}")
            return True
        except Exception as e:
            logger.log_error(f"AST patching failed for {file_path}: {e}")
            return False
