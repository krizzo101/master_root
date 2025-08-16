"""
Task Agent for Multi-Agent Orchestration

A specialized agent focused on data processing, task execution, and
computational operations within multi-agent workflows.
"""

import asyncio
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..common.types import AgentCapability, Task, TaskResult
from ..tools.data_processor_tool import DataProcessorTool
from .base_agent import BaseAgent


class TaskAgent(BaseAgent):
    """
    Specialized agent for task execution and data processing.

    This agent is designed to handle computational tasks, data transformations,
    file operations, and other processing-intensive operations within
    multi-agent workflows.

    Key Capabilities:
    - Data processing and transformation
    - File I/O operations
    - Computational tasks
    - Batch processing
    - Data validation and cleaning
    """

    def __init__(
        self,
        agent_id: str = "task_agent",
        name: str = "Task Agent",
        description: str = "Agent for data processing, computation, and automation",
        logger: logging.Logger | None = None,
        work_directory: str | Path | None = None,
    ):
        """
        Initialize the task agent.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            description: Agent description
            logger: Optional logger instance
            work_directory: Optional working directory for file operations
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            logger=logger,
        )

        # Task-specific configuration
        if work_directory is not None:
            self.work_directory = Path(work_directory)
        else:
            self.work_directory = Path.cwd()
        self.work_directory.mkdir(exist_ok=True)

        # Processing capabilities
        self.supported_formats = {"json", "csv", "txt", "xml", "yaml", "yml"}

        # Task execution metrics
        self.task_metrics = {
            "data_processing_tasks": 0,
            "file_operations": 0,
            "computational_tasks": 0,
            "validation_tasks": 0,
            "transformation_tasks": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
        }

        # Register specialized tools
        self._register_tools()

        self.logger.info(f"TaskAgent initialized: {self.agent_id}")

    def _register_tools(self) -> None:
        """Register task-specific tools."""
        # Data processing tool
        data_processor = DataProcessorTool()
        self.add_tool(data_processor)

        self.logger.info("Task-specific tools registered")

    async def _execute_task_logic(self, task: dict[str, Any]) -> TaskResult:
        """
        Execute task-specific logic.

        Args:
            task: Task definition containing type and data

        Returns:
            Task execution result
        """
        task_type = task.get("task_type", "")
        task_data = task.get("task_data", {})

        start_time = datetime.now()

        try:
            # Route to appropriate handler based on task type
            if task_type == "data_processing":
                result = await self._handle_data_processing(task_data)
                self.task_metrics["data_processing_tasks"] += 1

            elif task_type == "file_operation":
                result = await self._handle_file_operation(task_data)
                self.task_metrics["file_operations"] += 1

            elif task_type == "computation":
                result = await self._handle_computation(task_data)
                self.task_metrics["computational_tasks"] += 1

            elif task_type == "data_validation":
                result = await self._handle_data_validation(task_data)
                self.task_metrics["validation_tasks"] += 1

            elif task_type == "data_transformation":
                result = await self._handle_data_transformation(task_data)
                self.task_metrics["transformation_tasks"] += 1

            elif task_type == "batch_processing":
                result = await self._handle_batch_processing(task_data)
                self.task_metrics["data_processing_tasks"] += 1

            else:
                # Try to handle with registered tools
                result = await self._handle_with_tools(task_type, task_data)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.task_metrics["total_processing_time"] += processing_time

            total_tasks = sum(
                [
                    self.task_metrics["data_processing_tasks"],
                    self.task_metrics["file_operations"],
                    self.task_metrics["computational_tasks"],
                    self.task_metrics["validation_tasks"],
                    self.task_metrics["transformation_tasks"],
                ]
            )

            if total_tasks > 0:
                self.task_metrics["average_processing_time"] = (
                    self.task_metrics["total_processing_time"] / total_tasks
                )

            return TaskResult(
                success=True,
                result=result,
                metadata={
                    "task_type": task_type,
                    "processing_time": processing_time,
                    "agent_id": self.agent_id,
                },
            )

        except Exception as e:
            self.logger.error(f"Task execution failed: {task_type}, Error: {e}")
            return TaskResult(
                success=False,
                error=str(e),
                metadata={"task_type": task_type, "agent_id": self.agent_id},
            )

    async def _handle_data_processing(self, task_data: dict[str, Any]) -> Any:
        """Handle data processing tasks."""
        operation = task_data.get("operation", "")
        data = task_data.get("data", [])
        options = task_data.get("options", {})

        if operation == "filter":
            # Filter data based on criteria
            criteria = options.get("criteria", {})
            return self._filter_data(data, criteria)

        elif operation == "aggregate":
            # Aggregate data
            group_by = options.get("group_by", [])
            aggregations = options.get("aggregations", {})
            return self._aggregate_data(data, group_by, aggregations)

        elif operation == "sort":
            # Sort data
            sort_key = options.get("key", "")
            reverse = options.get("reverse", False)
            return self._sort_data(data, sort_key, reverse)

        elif operation == "merge":
            # Merge datasets
            other_data = task_data.get("other_data", [])
            merge_key = options.get("merge_key", "")
            return self._merge_data(data, other_data, merge_key)

        else:
            raise ValueError(f"Unsupported data processing operation: {operation}")

    async def _handle_file_operation(self, task_data: dict[str, Any]) -> Any:
        """Handle file operations."""
        operation = task_data.get("operation", "")
        file_path = task_data.get("file_path", "")

        if operation == "read":
            return await self._read_file(file_path, task_data.get("format", "auto"))

        elif operation == "write":
            data = task_data.get("data", "")
            format_type = task_data.get("format", "txt")
            return await self._write_file(file_path, data, format_type)

        elif operation == "copy":
            destination = task_data.get("destination", "")
            return await self._copy_file(file_path, destination)

        elif operation == "delete":
            return await self._delete_file(file_path)

        elif operation == "list":
            pattern = task_data.get("pattern", "*")
            return await self._list_files(file_path, pattern)

        else:
            raise ValueError(f"Unsupported file operation: {operation}")

    async def _handle_computation(self, task_data: dict[str, Any]) -> Any:
        """Handle computational tasks."""
        operation = task_data.get("operation", "")
        data = task_data.get("data", [])

        if operation == "statistics":
            return self._calculate_statistics(data)

        elif operation == "math":
            expression = task_data.get("expression", "")
            variables = task_data.get("variables", {})
            return self._evaluate_expression(expression, variables)

        elif operation == "hash":
            algorithm = task_data.get("algorithm", "sha256")
            return self._calculate_hash(data, algorithm)

        elif operation == "encode":
            encoding = task_data.get("encoding", "base64")
            return self._encode_data(data, encoding)

        elif operation == "decode":
            encoding = task_data.get("encoding", "base64")
            return self._decode_data(data, encoding)

        else:
            raise ValueError(f"Unsupported computation operation: {operation}")

    async def _handle_data_validation(self, task_data: dict[str, Any]) -> Any:
        """Handle data validation tasks."""
        data = task_data.get("data", [])
        schema = task_data.get("schema", {})
        rules = task_data.get("rules", [])

        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        # Schema validation
        if schema:
            schema_errors = self._validate_against_schema(data, schema)
            validation_results["errors"].extend(schema_errors)

        # Rule-based validation
        if rules:
            rule_errors = self._validate_against_rules(data, rules)
            validation_results["errors"].extend(rule_errors)

        # Data quality checks
        quality_issues = self._check_data_quality(data)
        validation_results["warnings"].extend(quality_issues)

        # Calculate statistics
        validation_results["statistics"] = self._calculate_validation_statistics(data)

        validation_results["valid"] = len(validation_results["errors"]) == 0

        return validation_results

    async def _handle_data_transformation(self, task_data: dict[str, Any]) -> Any:
        """Handle data transformation tasks."""
        data = task_data.get("data", [])
        transformations = task_data.get("transformations", [])

        transformed_data = data

        for transformation in transformations:
            transform_type = transformation.get("type", "")
            params = transformation.get("params", {})

            if transform_type == "map":
                # Apply mapping function
                mapping = params.get("mapping", {})
                transformed_data = self._map_data(transformed_data, mapping)

            elif transform_type == "normalize":
                # Normalize data
                method = params.get("method", "min_max")
                transformed_data = self._normalize_data(transformed_data, method)

            elif transform_type == "pivot":
                # Pivot data
                index = params.get("index", "")
                columns = params.get("columns", "")
                values = params.get("values", "")
                transformed_data = self._pivot_data(
                    transformed_data, index, columns, values
                )

            elif transform_type == "flatten":
                # Flatten nested data
                transformed_data = self._flatten_data(transformed_data)

            elif transform_type == "group":
                # Group data
                group_by = params.get("group_by", [])
                transformed_data = self._group_data(transformed_data, group_by)

        return transformed_data

    async def _handle_batch_processing(self, task_data: dict[str, Any]) -> Any:
        """Handle batch processing tasks."""
        batch_size = task_data.get("batch_size", 100)
        data = task_data.get("data", [])
        operation = task_data.get("operation", {})

        results = []

        # Process data in batches
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]

            # Apply operation to batch
            if operation.get("type") == "data_processing":
                batch_result = await self._handle_data_processing(
                    {**operation, "data": batch}
                )
            elif operation.get("type") == "computation":
                batch_result = await self._handle_computation(
                    {**operation, "data": batch}
                )
            else:
                batch_result = batch

            results.extend(
                batch_result if isinstance(batch_result, list) else [batch_result]
            )

            # Allow other tasks to run
            await asyncio.sleep(0)

        return results

    async def _handle_with_tools(
        self, task_type: str, task_data: dict[str, Any]
    ) -> Any:
        """Handle tasks using registered tools."""
        for tool in self.tools.values():
            if hasattr(tool, "can_handle") and tool.can_handle(task_type):
                return await tool.execute(task_data)

        raise ValueError(f"No tool available for task type: {task_type}")

    # Data processing helper methods

    def _filter_data(self, data: list[dict], criteria: dict[str, Any]) -> list[dict]:
        """Filter data based on criteria."""
        filtered = []
        for item in data:
            if all(item.get(key) == value for key, value in criteria.items()):
                filtered.append(item)
        return filtered

    def _aggregate_data(
        self, data: list[dict], group_by: list[str], aggregations: dict[str, str]
    ) -> list[dict]:
        """Aggregate data by groups."""
        from collections import defaultdict

        groups = defaultdict(list)

        # Group data
        for item in data:
            key = tuple(item.get(field, "") for field in group_by)
            groups[key].append(item)

        # Aggregate each group
        results = []
        for key, group_items in groups.items():
            result = dict(zip(group_by, key, strict=False))

            for field, agg_func in aggregations.items():
                values = [
                    item.get(field, 0)
                    for item in group_items
                    if item.get(field) is not None
                ]

                if agg_func == "sum":
                    result[f"{field}_sum"] = sum(values)
                elif agg_func == "avg":
                    result[f"{field}_avg"] = sum(values) / len(values) if values else 0
                elif agg_func == "count":
                    result[f"{field}_count"] = len(values)
                elif agg_func == "min":
                    result[f"{field}_min"] = min(values) if values else None
                elif agg_func == "max":
                    result[f"{field}_max"] = max(values) if values else None

            results.append(result)

        return results

    def _sort_data(
        self, data: list[dict], sort_key: str, reverse: bool = False
    ) -> list[dict]:
        """Sort data by key."""
        return sorted(data, key=lambda x: x.get(sort_key, ""), reverse=reverse)

    def _merge_data(
        self, data1: list[dict], data2: list[dict], merge_key: str
    ) -> list[dict]:
        """Merge two datasets on a key."""
        # Create lookup for data2
        lookup = {item.get(merge_key): item for item in data2}

        merged = []
        for item in data1:
            key_value = item.get(merge_key)
            if key_value in lookup:
                merged_item = {**item, **lookup[key_value]}
                merged.append(merged_item)
            else:
                merged.append(item)

        return merged

    # File operation helper methods

    async def _read_file(self, file_path: str, format_type: str = "auto") -> Any:
        """Read file content."""
        path = self.work_directory / file_path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect format
        if format_type == "auto":
            format_type = path.suffix.lower().lstrip(".")

        if format_type == "json":
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        elif format_type == "csv":
            with open(path, encoding="utf-8") as f:
                return list(csv.DictReader(f))
        else:
            with open(path, encoding="utf-8") as f:
                return f.read()

    async def _write_file(
        self, file_path: str, data: Any, format_type: str = "txt"
    ) -> bool:
        """Write data to file."""
        path = self.work_directory / file_path
        path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            if isinstance(data, list) and data and isinstance(data[0], dict):
                with open(path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                raise ValueError("CSV format requires list of dictionaries")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))

        return True

    async def _copy_file(self, source: str, destination: str) -> bool:
        """Copy file."""
        import shutil

        source_path = self.work_directory / source
        dest_path = self.work_directory / destination

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return True

    async def _delete_file(self, file_path: str) -> bool:
        """Delete file."""
        path = self.work_directory / file_path
        if path.exists():
            path.unlink()
            return True
        return False

    async def _list_files(self, directory: str, pattern: str = "*") -> list[str]:
        """List files in directory."""
        import glob

        path = self.work_directory / directory
        files = glob.glob(str(path / pattern))
        return [str(Path(f).relative_to(self.work_directory)) for f in files]

    # Computation helper methods

    def _calculate_statistics(self, data: list[int | float]) -> dict[str, float]:
        """Calculate basic statistics."""
        if not data:
            return {}

        import statistics

        return {
            "count": len(data),
            "sum": sum(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "mode": statistics.mode(data) if len(set(data)) < len(data) else None,
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "variance": statistics.variance(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
        }

    def _evaluate_expression(self, expression: str, variables: dict[str, Any]) -> Any:
        """Safely evaluate mathematical expression."""
        # Simple expression evaluation - can be extended with more sophisticated parser
        import ast
        import operator

        # Safe evaluation of mathematical expressions
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def eval_node(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                return variables.get(node.id, 0)
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                return allowed_operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                return allowed_operators[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")

        tree = ast.parse(expression, mode="eval")
        return eval_node(tree.body)

    def _calculate_hash(self, data: Any, algorithm: str = "sha256") -> str:
        """Calculate hash of data."""
        import hashlib

        # Convert data to string
        data_str = (
            json.dumps(data, sort_keys=True) if not isinstance(data, str) else data
        )
        data_bytes = data_str.encode("utf-8")

        if algorithm == "md5":
            return hashlib.md5(data_bytes).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(data_bytes).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(data_bytes).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def _encode_data(self, data: Any, encoding: str = "base64") -> str:
        """Encode data."""
        import base64

        data_str = json.dumps(data) if not isinstance(data, str) else data
        data_bytes = data_str.encode("utf-8")

        if encoding == "base64":
            return base64.b64encode(data_bytes).decode("utf-8")
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")

    def _decode_data(self, data: str, encoding: str = "base64") -> str:
        """Decode data."""
        import base64

        if encoding == "base64":
            return base64.b64decode(data.encode("utf-8")).decode("utf-8")
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")

    # Validation helper methods

    def _validate_against_schema(
        self, data: list[dict], schema: dict[str, Any]
    ) -> list[str]:
        """Validate data against schema."""
        errors = []
        required_fields = schema.get("required", [])
        field_types = schema.get("types", {})

        for i, item in enumerate(data):
            # Check required fields
            for field in required_fields:
                if field not in item:
                    errors.append(f"Row {i}: Missing required field '{field}'")

            # Check field types
            for field, expected_type in field_types.items():
                if field in item:
                    actual_type = type(item[field]).__name__
                    if actual_type != expected_type:
                        errors.append(
                            f"Row {i}, Field '{field}': Expected {expected_type}, got {actual_type}"
                        )

        return errors

    def _validate_against_rules(self, data: list[dict], rules: list[dict]) -> list[str]:
        """Validate data against custom rules."""
        errors = []

        for i, item in enumerate(data):
            for rule in rules:
                rule_type = rule.get("type", "")
                field = rule.get("field", "")

                if rule_type == "range":
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    value = item.get(field)

                    if value is not None:
                        if min_val is not None and value < min_val:
                            errors.append(
                                f"Row {i}, Field '{field}': Value {value} below minimum {min_val}"
                            )
                        if max_val is not None and value > max_val:
                            errors.append(
                                f"Row {i}, Field '{field}': Value {value} above maximum {max_val}"
                            )

                elif rule_type == "pattern":
                    import re

                    pattern = rule.get("pattern", "")
                    value = item.get(field, "")

                    if not re.match(pattern, str(value)):
                        errors.append(
                            f"Row {i}, Field '{field}': Value '{value}' doesn't match pattern '{pattern}'"
                        )

        return errors

    def _check_data_quality(self, data: list[dict]) -> list[str]:
        """Check data quality issues."""
        warnings = []

        if not data:
            warnings.append("Dataset is empty")
            return warnings

        # Check for missing values
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())

        for field in all_fields:
            missing_count = sum(
                1 for item in data if item.get(field) is None or item.get(field) == ""
            )
            if missing_count > 0:
                percentage = (missing_count / len(data)) * 100
                warnings.append(
                    f"Field '{field}': {missing_count} missing values ({percentage:.1f}%)"
                )

        # Check for duplicates
        seen = set()
        duplicates = 0
        for item in data:
            item_hash = hash(json.dumps(item, sort_keys=True))
            if item_hash in seen:
                duplicates += 1
            else:
                seen.add(item_hash)

        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate records")

        return warnings

    def _calculate_validation_statistics(self, data: list[dict]) -> dict[str, Any]:
        """Calculate validation statistics."""
        if not data:
            return {}

        stats = {
            "total_records": len(data),
            "total_fields": len(set().union(*(item.keys() for item in data))),
            "field_coverage": {},
        }

        # Calculate field coverage
        all_fields = set().union(*(item.keys() for item in data))
        for field in all_fields:
            non_null_count = sum(
                1
                for item in data
                if item.get(field) is not None and item.get(field) != ""
            )
            stats["field_coverage"][field] = (non_null_count / len(data)) * 100

        return stats

    # Transformation helper methods

    def _map_data(self, data: list[dict], mapping: dict[str, str]) -> list[dict]:
        """Apply field mapping to data."""
        mapped_data = []
        for item in data:
            mapped_item = {}
            for old_field, new_field in mapping.items():
                if old_field in item:
                    mapped_item[new_field] = item[old_field]
            mapped_data.append(mapped_item)
        return mapped_data

    def _normalize_data(self, data: list[dict], method: str = "min_max") -> list[dict]:
        """Normalize numerical data."""
        if not data:
            return data

        # Find numerical fields
        numerical_fields = []
        for field in data[0].keys():
            if all(
                isinstance(item.get(field), (int, float))
                for item in data
                if item.get(field) is not None
            ):
                numerical_fields.append(field)

        normalized_data = []

        for field in numerical_fields:
            values = [item.get(field) for item in data if item.get(field) is not None]

            if method == "min_max":
                min_val = min(values)
                max_val = max(values)
                range_val = max_val - min_val

                if range_val == 0:
                    continue

                for item in data:
                    if item.get(field) is not None:
                        item[f"{field}_normalized"] = (
                            item[field] - min_val
                        ) / range_val

        return data

    def _pivot_data(
        self, data: list[dict], index: str, columns: str, values: str
    ) -> list[dict]:
        """Pivot data (simplified implementation)."""
        from collections import defaultdict

        pivot_dict = defaultdict(dict)

        for item in data:
            idx = item.get(index)
            col = item.get(columns)
            val = item.get(values)

            if idx and col and val is not None:
                pivot_dict[idx][col] = val

        # Convert to list of dictionaries
        pivoted = []
        for idx, cols in pivot_dict.items():
            row = {index: idx}
            row.update(cols)
            pivoted.append(row)

        return pivoted

    def _flatten_data(
        self, data: Any, parent_key: str = "", sep: str = "."
    ) -> dict[str, Any]:
        """Flatten nested data structure."""

        def _flatten_dict(d, parent_key="", sep="."):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        if isinstance(data, dict):
            return _flatten_dict(data, parent_key, sep)
        elif isinstance(data, list):
            return [
                _flatten_dict(item, parent_key, sep) if isinstance(item, dict) else item
                for item in data
            ]
        else:
            return data

    def _group_data(
        self, data: list[dict], group_by: list[str]
    ) -> dict[str, list[dict]]:
        """Group data by specified fields."""
        from collections import defaultdict

        groups = defaultdict(list)

        for item in data:
            key = tuple(item.get(field, "") for field in group_by)
            groups[str(key)].append(item)

        return dict(groups)

    def get_task_metrics(self) -> dict[str, Any]:
        """Get task execution metrics."""
        return self.task_metrics.copy()

    def get_capabilities(self) -> list[AgentCapability]:
        """
        Get the agent's capabilities as a list of AgentCapability objects.
        """
        return [
            AgentCapability(
                name="data_processing",
                description="Process and transform data",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="file_operation",
                description="Perform file I/O operations",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="computation",
                description="Perform computational tasks",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="data_validation",
                description="Validate and clean data",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="data_transformation",
                description="Transform data formats and structures",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="batch_processing",
                description="Process data in batches",
                input_schema={},
                output_schema={},
                tools_required=["data_processor"],
            ),
        ]

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        Execute a task using the agent's processing logic.

        Args:
            task: Task to execute

        Returns:
            Task execution results as a dictionary
        """
        try:
            self.logger.info(f"TaskAgent executing task: {task.name}")
            # Route to internal logic (expects dict, so pass task.parameters)
            result = await self._execute_task_logic(
                {
                    "task_type": task.parameters.get("task_type", ""),
                    "task_data": task.parameters.get("task_data", {}),
                }
            )
            # Convert TaskResult to dict if needed
            if hasattr(result, "__dict__"):
                return dict(result.__dict__)
            return result
        except Exception as e:
            self.logger.error(f"TaskAgent task execution failed: {e}")
            return {"success": False, "error": str(e)}
