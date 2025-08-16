"""TransformAgent - Data mapping and transformation."""

from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import structlog
from copy import deepcopy

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult


logger = structlog.get_logger()


class TransformType(Enum):
    """Types of transformations."""
    MAP = "map"
    FILTER = "filter"
    REDUCE = "reduce"
    AGGREGATE = "aggregate"
    FLATTEN = "flatten"
    PIVOT = "pivot"
    NORMALIZE = "normalize"
    DENORMALIZE = "denormalize"
    MERGE = "merge"
    SPLIT = "split"
    CONVERT = "convert"
    VALIDATE = "validate"


@dataclass
class TransformRule:
    """Transformation rule."""
    id: str
    type: TransformType
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    operation: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[Callable] = None
    description: str = ""
    
    def apply(self, data: Any) -> Any:
        """Apply transformation rule."""
        if self.condition and not self.condition(data):
            return data
        
        if self.operation:
            return self.operation(data, **self.parameters)
        
        return data


@dataclass
class TransformPipeline:
    """Transformation pipeline."""
    id: str
    name: str
    rules: List[TransformRule]
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def execute(self, data: Any) -> Any:
        """Execute transformation pipeline."""
        result = data
        for rule in self.rules:
            result = rule.apply(result)
        return result
    
    def validate_input(self, data: Any) -> bool:
        """Validate input against schema."""
        if not self.input_schema:
            return True
        return self._validate_schema(data, self.input_schema)
    
    def validate_output(self, data: Any) -> bool:
        """Validate output against schema."""
        if not self.output_schema:
            return True
        return self._validate_schema(data, self.output_schema)
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against schema."""
        # Simplified schema validation
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(data, dict):
                return False
            elif expected_type == "array" and not isinstance(data, list):
                return False
            elif expected_type == "string" and not isinstance(data, str):
                return False
            elif expected_type == "number" and not isinstance(data, (int, float)):
                return False
        
        if "required" in schema and isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    return False
        
        return True


class TransformAgent(BaseAgent):
    """Data mapping, filtering, and transformation agent."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize transform agent."""
        super().__init__(config or AgentConfig(
            name="TransformAgent",
            description="Data mapping and transformation",
            capabilities=["map", "filter", "aggregate", "convert", "normalize"],
            max_retries=2,
            timeout=60
        ))
        self.pipelines: Dict[str, TransformPipeline] = {}
        self.transforms: Dict[str, Callable] = {}
        self._pipeline_counter = 0
        self._rule_counter = 0
        self._register_builtin_transforms()
    
    def initialize(self) -> bool:
        """Initialize the transform agent."""
        logger.info("transform_agent_initialized", agent=self.config.name)
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transform task."""
        action = task.get("action", "transform")
        
        if action == "transform":
            return self._transform_data(task)
        elif action == "map":
            return self._map_data(task)
        elif action == "filter":
            return self._filter_data(task)
        elif action == "aggregate":
            return self._aggregate_data(task)
        elif action == "normalize":
            return self._normalize_data(task)
        elif action == "convert":
            return self._convert_data(task)
        elif action == "pipeline":
            return self._execute_pipeline(task)
        elif action == "create_pipeline":
            return self._create_pipeline(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def transform(self, data: Any, transform_type: str, **kwargs) -> Any:
        """Transform data using specified transformation."""
        result = self.execute({
            "action": "transform",
            "data": data,
            "transform_type": transform_type,
            **kwargs
        })
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        return result["transformed"]
    
    def _register_builtin_transforms(self):
        """Register built-in transformation functions."""
        self.transforms.update({
            "uppercase": lambda x: x.upper() if isinstance(x, str) else x,
            "lowercase": lambda x: x.lower() if isinstance(x, str) else x,
            "trim": lambda x: x.strip() if isinstance(x, str) else x,
            "reverse": lambda x: x[::-1] if isinstance(x, (str, list)) else x,
            "sort": lambda x: sorted(x) if isinstance(x, list) else x,
            "unique": lambda x: list(set(x)) if isinstance(x, list) else x,
            "flatten": self._flatten_nested,
            "compact": lambda x: [i for i in x if i] if isinstance(x, list) else x,
            "keys": lambda x: list(x.keys()) if isinstance(x, dict) else [],
            "values": lambda x: list(x.values()) if isinstance(x, dict) else [],
            "sum": lambda x: sum(x) if isinstance(x, list) and all(isinstance(i, (int, float)) for i in x) else 0,
            "mean": lambda x: sum(x) / len(x) if isinstance(x, list) and x and all(isinstance(i, (int, float)) for i in x) else 0,
            "min": lambda x: min(x) if isinstance(x, list) and x else None,
            "max": lambda x: max(x) if isinstance(x, list) and x else None
        })
    
    def _transform_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation to data."""
        data = task.get("data")
        transform_type = task.get("transform_type", "")
        parameters = task.get("parameters", {})
        
        if data is None:
            return {"error": "Data is required"}
        
        if not transform_type:
            return {"error": "Transform type is required"}
        
        # Apply transformation
        if transform_type in self.transforms:
            transform_func = self.transforms[transform_type]
            try:
                transformed = transform_func(data)
            except Exception as e:
                return {"error": f"Transformation failed: {str(e)}"}
        else:
            # Try to interpret as custom transformation
            transformed = self._apply_custom_transform(data, transform_type, parameters)
        
        return {
            "transformed": transformed,
            "original_type": type(data).__name__,
            "transformed_type": type(transformed).__name__
        }
    
    def _map_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Map data using function."""
        data = task.get("data")
        mapper = task.get("mapper")
        field = task.get("field")
        
        if data is None:
            return {"error": "Data is required"}
        
        if isinstance(data, list):
            if mapper and mapper in self.transforms:
                mapped = [self.transforms[mapper](item) for item in data]
            elif field and isinstance(data[0], dict):
                mapped = [item.get(field) for item in data]
            else:
                mapped = data
        elif isinstance(data, dict):
            if mapper and mapper in self.transforms:
                mapped = {k: self.transforms[mapper](v) for k, v in data.items()}
            elif field:
                mapped = data.get(field)
            else:
                mapped = data
        else:
            mapped = data
        
        return {
            "mapped": mapped,
            "count": len(mapped) if isinstance(mapped, (list, dict)) else 1
        }
    
    def _filter_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data based on condition."""
        data = task.get("data")
        condition = task.get("condition", {})
        
        if data is None:
            return {"error": "Data is required"}
        
        filtered = []
        
        if isinstance(data, list):
            for item in data:
                if self._evaluate_condition(item, condition):
                    filtered.append(item)
        elif isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if self._evaluate_condition(value, condition):
                    filtered[key] = value
        else:
            filtered = data if self._evaluate_condition(data, condition) else None
        
        return {
            "filtered": filtered,
            "original_count": len(data) if isinstance(data, (list, dict)) else 1,
            "filtered_count": len(filtered) if isinstance(filtered, (list, dict)) else (1 if filtered else 0)
        }
    
    def _aggregate_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data."""
        data = task.get("data")
        group_by = task.get("group_by")
        aggregations = task.get("aggregations", {})
        
        if data is None:
            return {"error": "Data is required"}
        
        if not isinstance(data, list):
            return {"error": "Data must be a list for aggregation"}
        
        if group_by:
            # Group data
            groups = {}
            for item in data:
                if isinstance(item, dict) and group_by in item:
                    key = item[group_by]
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(item)
            
            # Apply aggregations to each group
            result = {}
            for key, group in groups.items():
                result[key] = self._apply_aggregations(group, aggregations)
        else:
            # Apply aggregations to entire dataset
            result = self._apply_aggregations(data, aggregations)
        
        return {"aggregated": result}
    
    def _normalize_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure."""
        data = task.get("data")
        schema = task.get("schema", {})
        
        if data is None:
            return {"error": "Data is required"}
        
        normalized = self._normalize_structure(data, schema)
        
        return {
            "normalized": normalized,
            "changes": self._compare_structures(data, normalized)
        }
    
    def _convert_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data format."""
        data = task.get("data")
        from_format = task.get("from_format", "auto")
        to_format = task.get("to_format", "json")
        
        if data is None:
            return {"error": "Data is required"}
        
        # Auto-detect format if needed
        if from_format == "auto":
            from_format = self._detect_format(data)
        
        # Parse input if string
        if isinstance(data, str):
            if from_format == "json":
                try:
                    parsed = json.loads(data)
                except json.JSONDecodeError as e:
                    return {"error": f"Invalid JSON: {str(e)}"}
            elif from_format == "csv":
                parsed = self._parse_csv(data)
            elif from_format == "xml":
                parsed = self._parse_xml(data)
            else:
                parsed = data
        else:
            parsed = data
        
        # Convert to target format
        if to_format == "json":
            if isinstance(parsed, str):
                converted = json.dumps({"data": parsed})
            else:
                converted = json.dumps(parsed, indent=2)
        elif to_format == "csv":
            converted = self._to_csv(parsed)
        elif to_format == "xml":
            converted = self._to_xml(parsed)
        elif to_format == "yaml":
            converted = self._to_yaml(parsed)
        else:
            converted = str(parsed)
        
        return {
            "converted": converted,
            "from_format": from_format,
            "to_format": to_format
        }
    
    def _execute_pipeline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transformation pipeline."""
        pipeline_id = task.get("pipeline_id")
        data = task.get("data")
        
        if not pipeline_id or pipeline_id not in self.pipelines:
            return {"error": f"Pipeline {pipeline_id} not found"}
        
        if data is None:
            return {"error": "Data is required"}
        
        pipeline = self.pipelines[pipeline_id]
        
        # Validate input
        if not pipeline.validate_input(data):
            return {"error": "Input validation failed"}
        
        # Execute pipeline
        try:
            result = pipeline.execute(data)
        except Exception as e:
            return {"error": f"Pipeline execution failed: {str(e)}"}
        
        # Validate output
        if not pipeline.validate_output(result):
            return {"error": "Output validation failed"}
        
        return {
            "result": result,
            "pipeline": pipeline_id,
            "rules_applied": len(pipeline.rules)
        }
    
    def _create_pipeline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create transformation pipeline."""
        name = task.get("name", "Unnamed Pipeline")
        rules_data = task.get("rules", [])
        input_schema = task.get("input_schema")
        output_schema = task.get("output_schema")
        
        if not rules_data:
            return {"error": "Rules are required"}
        
        # Create rules
        rules = []
        for rule_data in rules_data:
            self._rule_counter += 1
            rule = TransformRule(
                id=f"rule_{self._rule_counter}",
                type=TransformType[rule_data.get("type", "MAP").upper()],
                source_field=rule_data.get("source_field"),
                target_field=rule_data.get("target_field"),
                parameters=rule_data.get("parameters", {}),
                description=rule_data.get("description", "")
            )
            
            # Set operation based on type
            if rule.type == TransformType.MAP:
                rule.operation = self._create_map_operation(rule.parameters)
            elif rule.type == TransformType.FILTER:
                rule.operation = self._create_filter_operation(rule.parameters)
            elif rule.type == TransformType.AGGREGATE:
                rule.operation = self._create_aggregate_operation(rule.parameters)
            
            rules.append(rule)
        
        # Create pipeline
        self._pipeline_counter += 1
        pipeline_id = f"pipeline_{self._pipeline_counter}"
        
        pipeline = TransformPipeline(
            id=pipeline_id,
            name=name,
            rules=rules,
            input_schema=input_schema,
            output_schema=output_schema
        )
        
        self.pipelines[pipeline_id] = pipeline
        
        logger.info(
            "pipeline_created",
            pipeline_id=pipeline_id,
            name=name,
            rules_count=len(rules)
        )
        
        return {
            "pipeline_id": pipeline_id,
            "name": name,
            "rules_count": len(rules)
        }
    
    def _apply_custom_transform(self, data: Any, transform_type: str, 
                               parameters: Dict[str, Any]) -> Any:
        """Apply custom transformation."""
        # Handle common custom transformations
        if transform_type == "extract":
            if isinstance(data, dict) and "field" in parameters:
                return data.get(parameters["field"])
            elif isinstance(data, list) and "index" in parameters:
                idx = parameters["index"]
                return data[idx] if 0 <= idx < len(data) else None
        
        elif transform_type == "replace":
            if isinstance(data, str):
                return data.replace(
                    parameters.get("find", ""),
                    parameters.get("replace", "")
                )
        
        elif transform_type == "split":
            if isinstance(data, str):
                return data.split(parameters.get("delimiter", ","))
        
        elif transform_type == "join":
            if isinstance(data, list):
                return parameters.get("delimiter", "").join(str(x) for x in data)
        
        elif transform_type == "cast":
            target_type = parameters.get("to", "str")
            if target_type == "int":
                return int(data)
            elif target_type == "float":
                return float(data)
            elif target_type == "str":
                return str(data)
            elif target_type == "bool":
                return bool(data)
            elif target_type == "list":
                return list(data) if hasattr(data, '__iter__') else [data]
            elif target_type == "dict":
                return dict(data) if isinstance(data, dict) else {"value": data}
        
        return data
    
    def _evaluate_condition(self, item: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate filter condition."""
        if not condition:
            return True
        
        # Simple condition evaluation
        if "equals" in condition:
            if isinstance(item, dict):
                field = condition.get("field", "")
                return item.get(field) == condition["equals"]
            else:
                return item == condition["equals"]
        
        if "greater_than" in condition:
            if isinstance(item, dict):
                field = condition.get("field", "")
                value = item.get(field)
            else:
                value = item
            return isinstance(value, (int, float)) and value > condition["greater_than"]
        
        if "less_than" in condition:
            if isinstance(item, dict):
                field = condition.get("field", "")
                value = item.get(field)
            else:
                value = item
            return isinstance(value, (int, float)) and value < condition["less_than"]
        
        if "contains" in condition:
            if isinstance(item, dict):
                field = condition.get("field", "")
                value = str(item.get(field, ""))
            else:
                value = str(item)
            return condition["contains"] in value
        
        if "not_null" in condition:
            if isinstance(item, dict):
                field = condition["not_null"]
                return field in item and item[field] is not None
            else:
                return item is not None
        
        return True
    
    def _apply_aggregations(self, data: List[Any], aggregations: Dict[str, str]) -> Dict[str, Any]:
        """Apply aggregation functions."""
        result = {}
        
        for field, func in aggregations.items():
            if func == "count":
                result[field] = len(data)
            elif func == "sum":
                values = [item.get(field, 0) if isinstance(item, dict) else item 
                         for item in data]
                result[field] = sum(v for v in values if isinstance(v, (int, float)))
            elif func == "mean":
                values = [item.get(field, 0) if isinstance(item, dict) else item 
                         for item in data]
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                result[field] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
            elif func == "min":
                values = [item.get(field) if isinstance(item, dict) else item 
                         for item in data]
                result[field] = min(v for v in values if v is not None)
            elif func == "max":
                values = [item.get(field) if isinstance(item, dict) else item 
                         for item in data]
                result[field] = max(v for v in values if v is not None)
            elif func == "first":
                result[field] = data[0].get(field) if data and isinstance(data[0], dict) else (data[0] if data else None)
            elif func == "last":
                result[field] = data[-1].get(field) if data and isinstance(data[-1], dict) else (data[-1] if data else None)
        
        return result
    
    def _normalize_structure(self, data: Any, schema: Dict[str, Any]) -> Any:
        """Normalize data structure according to schema."""
        if not schema:
            return data
        
        if isinstance(data, dict):
            normalized = {}
            
            # Add required fields
            if "required" in schema:
                for field in schema["required"]:
                    if field in data:
                        normalized[field] = data[field]
                    else:
                        # Add default value
                        normalized[field] = schema.get("defaults", {}).get(field)
            
            # Add optional fields
            if "optional" in schema:
                for field in schema["optional"]:
                    if field in data:
                        normalized[field] = data[field]
            
            # Rename fields
            if "rename" in schema:
                for old_name, new_name in schema["rename"].items():
                    if old_name in data:
                        normalized[new_name] = data[old_name]
            
            return normalized
        
        elif isinstance(data, list):
            # Normalize each item
            return [self._normalize_structure(item, schema) for item in data]
        
        return data
    
    def _compare_structures(self, original: Any, normalized: Any) -> Dict[str, Any]:
        """Compare original and normalized structures."""
        changes = {
            "added_fields": [],
            "removed_fields": [],
            "renamed_fields": [],
            "type_changes": []
        }
        
        if isinstance(original, dict) and isinstance(normalized, dict):
            original_keys = set(original.keys())
            normalized_keys = set(normalized.keys())
            
            changes["added_fields"] = list(normalized_keys - original_keys)
            changes["removed_fields"] = list(original_keys - normalized_keys)
            
            # Check for type changes
            for key in original_keys & normalized_keys:
                if type(original[key]) != type(normalized[key]):
                    changes["type_changes"].append({
                        "field": key,
                        "from": type(original[key]).__name__,
                        "to": type(normalized[key]).__name__
                    })
        
        return changes
    
    def _detect_format(self, data: Any) -> str:
        """Detect data format."""
        if isinstance(data, str):
            data = data.strip()
            if data.startswith("{") or data.startswith("["):
                return "json"
            elif data.startswith("<"):
                return "xml"
            elif "," in data or "\n" in data:
                return "csv"
            else:
                return "text"
        return "object"
    
    def _flatten_nested(self, data: Any, max_depth: int = -1) -> Any:
        """Flatten nested structure."""
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, list) and max_depth != 0:
                    result.extend(self._flatten_nested(item, max_depth - 1))
                else:
                    result.append(item)
            return result
        return data
    
    def _parse_csv(self, data: str) -> List[Dict[str, Any]]:
        """Parse CSV data."""
        lines = data.strip().split('\n')
        if not lines:
            return []
        
        headers = lines[0].split(',')
        result = []
        
        for line in lines[1:]:
            values = line.split(',')
            row = dict(zip(headers, values))
            result.append(row)
        
        return result
    
    def _parse_xml(self, data: str) -> Dict[str, Any]:
        """Parse XML data (simplified)."""
        # Very simplified XML parsing
        return {"xml_content": data}
    
    def _to_csv(self, data: Any) -> str:
        """Convert to CSV format."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            lines = [",".join(headers)]
            
            for item in data:
                values = [str(item.get(h, "")) for h in headers]
                lines.append(",".join(values))
            
            return "\n".join(lines)
        
        return str(data)
    
    def _to_xml(self, data: Any) -> str:
        """Convert to XML format (simplified)."""
        if isinstance(data, dict):
            xml = ["<root>"]
            for key, value in data.items():
                xml.append(f"  <{key}>{value}</{key}>")
            xml.append("</root>")
            return "\n".join(xml)
        
        return f"<root>{data}</root>"
    
    def _to_yaml(self, data: Any) -> str:
        """Convert to YAML format (simplified)."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
                elif isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        
        return str(data)
    
    def _create_map_operation(self, parameters: Dict[str, Any]) -> Callable:
        """Create map operation function."""
        def map_op(data: Any, **kwargs) -> Any:
            if "transform" in parameters and parameters["transform"] in self.transforms:
                return self.transforms[parameters["transform"]](data)
            return data
        return map_op
    
    def _create_filter_operation(self, parameters: Dict[str, Any]) -> Callable:
        """Create filter operation function."""
        def filter_op(data: Any, **kwargs) -> Any:
            if isinstance(data, list):
                return [item for item in data if self._evaluate_condition(item, parameters)]
            return data
        return filter_op
    
    def _create_aggregate_operation(self, parameters: Dict[str, Any]) -> Callable:
        """Create aggregate operation function."""
        def aggregate_op(data: Any, **kwargs) -> Any:
            if isinstance(data, list):
                return self._apply_aggregations(data, parameters.get("aggregations", {}))
            return data
        return aggregate_op
    
    def shutdown(self) -> bool:
        """Shutdown the transform agent."""
        logger.info("transform_agent_shutdown", 
                   pipelines_count=len(self.pipelines))
        self.pipelines.clear()
        self.transforms.clear()
        return True