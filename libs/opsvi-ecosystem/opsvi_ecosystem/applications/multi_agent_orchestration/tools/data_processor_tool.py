"""
Data processor tool implementation.

Provides data processing capabilities including text analysis,
data transformation, and basic analytics operations.
"""

import asyncio
import json
import logging
import re
from collections import Counter
from typing import Any

from ..common.types import ToolError, ToolSchema
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class DataProcessorTool(BaseTool):
    """
    Data processing tool for various data manipulation tasks.

    Supports text processing, data analysis, format conversion,
    and basic statistical operations.
    """

    def __init__(self):
        """Initialize the data processor tool."""
        super().__init__(
            name="data_processor",
            description="Process and analyze data including text analysis, format conversion, and statistics",
        )

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Execute data processing with the given parameters.

        Args:
            parameters: Processing parameters containing 'operation', 'data', and operation-specific params

        Returns:
            Dictionary containing processing results

        Raises:
            ToolError: If processing fails
        """
        try:
            operation = parameters.get("operation", "")
            data = parameters.get("data")

            if not operation:
                raise ToolError("Operation type must be specified")

            if data is None:
                raise ToolError("Data to process must be provided")

            logger.info(f"Processing data with operation: {operation}")

            # Route to appropriate processing method
            if operation == "text_analysis":
                result = await self._analyze_text(data, parameters)
            elif operation == "format_conversion":
                result = await self._convert_format(data, parameters)
            elif operation == "statistics":
                result = await self._calculate_statistics(data, parameters)
            elif operation == "filter_data":
                result = await self._filter_data(data, parameters)
            elif operation == "aggregate_data":
                result = await self._aggregate_data(data, parameters)
            else:
                raise ToolError(f"Unknown operation: {operation}")

            return {
                "operation": operation,
                "result": result,
                "data_size": len(str(data)),
                "processing_successful": True,
            }

        except Exception as e:
            logger.error(f"Data processing failed for operation '{operation}': {e}")
            raise ToolError(f"Data processing failed: {str(e)}")

    def get_schema(self) -> ToolSchema:
        """
        Get the data processor tool schema.

        Returns:
            ToolSchema defining input/output format
        """
        return ToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Type of processing operation",
                        "enum": [
                            "text_analysis",
                            "format_conversion",
                            "statistics",
                            "filter_data",
                            "aggregate_data",
                        ],
                    },
                    "data": {"description": "Data to process (text, list, dict, etc.)"},
                    "options": {
                        "type": "object",
                        "description": "Operation-specific options",
                        "properties": {
                            "target_format": {"type": "string"},
                            "filter_criteria": {"type": "object"},
                            "aggregation_key": {"type": "string"},
                            "include_sentiment": {"type": "boolean"},
                            "include_keywords": {"type": "boolean"},
                        },
                    },
                },
                "required": ["operation", "data"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "result": {"description": "Processing results"},
                    "data_size": {"type": "integer"},
                    "processing_successful": {"type": "boolean"},
                },
            },
            required_params=["operation", "data"],
        )

    async def _analyze_text(
        self, text: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze text for various metrics and insights.

        Args:
            text: Text to analyze
            parameters: Analysis parameters

        Returns:
            Text analysis results
        """
        if not isinstance(text, str):
            raise ToolError("Text analysis requires string input")

        # Simulate processing delay
        await asyncio.sleep(0.1)

        options = parameters.get("options", {})

        # Basic text metrics
        words = text.split()
        sentences = re.split(r"[.!?]+", text)
        paragraphs = text.split("\n\n")

        result = {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "character_count": len(text),
            "average_word_length": (
                sum(len(word) for word in words) / len(words) if words else 0
            ),
        }

        # Optional keyword extraction
        if options.get("include_keywords", False):
            # Simple keyword extraction (most common words excluding stop words)
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
            }
            words_lower = [word.lower().strip('.,!?";') for word in words]
            filtered_words = [
                word for word in words_lower if word not in stop_words and len(word) > 2
            ]
            word_freq = Counter(filtered_words)
            result["top_keywords"] = word_freq.most_common(10)

        # Optional sentiment analysis (simplified)
        if options.get("include_sentiment", False):
            positive_words = [
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "fantastic",
                "love",
                "like",
                "best",
                "perfect",
            ]
            negative_words = [
                "bad",
                "terrible",
                "awful",
                "hate",
                "worst",
                "horrible",
                "disgusting",
                "disappointing",
                "poor",
                "fail",
            ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            result["sentiment"] = {
                "overall": sentiment,
                "positive_indicators": positive_count,
                "negative_indicators": negative_count,
            }

        return result

    async def _convert_format(
        self, data: Any, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Convert data between different formats.

        Args:
            data: Data to convert
            parameters: Conversion parameters

        Returns:
            Format conversion results
        """
        options = parameters.get("options", {})
        target_format = options.get("target_format", "json")

        # Simulate processing delay
        await asyncio.sleep(0.1)

        try:
            if target_format == "json":
                if isinstance(data, str):
                    # Try to parse as JSON first, otherwise wrap in JSON
                    try:
                        parsed = json.loads(data)
                        converted = json.dumps(parsed, indent=2)
                    except json.JSONDecodeError:
                        converted = json.dumps({"text": data}, indent=2)
                else:
                    converted = json.dumps(data, indent=2, default=str)

            elif target_format == "csv":
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    # Convert list of dicts to CSV format
                    headers = list(data[0].keys())
                    csv_lines = [",".join(headers)]
                    for item in data:
                        row = [str(item.get(header, "")) for header in headers]
                        csv_lines.append(",".join(row))
                    converted = "\n".join(csv_lines)
                else:
                    raise ToolError("CSV conversion requires list of dictionaries")

            elif target_format == "text":
                if isinstance(data, dict):
                    converted = "\n".join(f"{k}: {v}" for k, v in data.items())
                elif isinstance(data, list):
                    converted = "\n".join(str(item) for item in data)
                else:
                    converted = str(data)

            else:
                raise ToolError(f"Unsupported target format: {target_format}")

            return {
                "original_format": type(data).__name__,
                "target_format": target_format,
                "converted_data": converted,
                "conversion_successful": True,
            }

        except Exception as e:
            raise ToolError(f"Format conversion failed: {str(e)}")

    async def _calculate_statistics(
        self, data: list | dict, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate basic statistics on numerical data.

        Args:
            data: Numerical data to analyze
            parameters: Statistics parameters

        Returns:
            Statistical analysis results
        """
        # Simulate processing delay
        await asyncio.sleep(0.1)

        try:
            # Extract numerical values
            if isinstance(data, list):
                numbers = [x for x in data if isinstance(x, (int, float))]
            elif isinstance(data, dict):
                numbers = [v for v in data.values() if isinstance(v, (int, float))]
            else:
                raise ToolError("Statistics require list or dictionary input")

            if not numbers:
                raise ToolError("No numerical data found for statistics")

            numbers.sort()
            n = len(numbers)

            result = {
                "count": n,
                "sum": sum(numbers),
                "mean": sum(numbers) / n,
                "median": (
                    numbers[n // 2]
                    if n % 2 == 1
                    else (numbers[n // 2 - 1] + numbers[n // 2]) / 2
                ),
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers),
            }

            # Calculate standard deviation
            mean = result["mean"]
            variance = sum((x - mean) ** 2 for x in numbers) / n
            result["variance"] = variance
            result["std_deviation"] = variance**0.5

            return result

        except Exception as e:
            raise ToolError(f"Statistics calculation failed: {str(e)}")

    async def _filter_data(
        self, data: list | dict, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Filter data based on specified criteria.

        Args:
            data: Data to filter
            parameters: Filter parameters

        Returns:
            Filtered data results
        """
        options = parameters.get("options", {})
        filter_criteria = options.get("filter_criteria", {})

        # Simulate processing delay
        await asyncio.sleep(0.1)

        try:
            if isinstance(data, list):
                filtered_data = []
                for item in data:
                    if self._matches_criteria(item, filter_criteria):
                        filtered_data.append(item)
            elif isinstance(data, dict):
                filtered_data = {
                    k: v
                    for k, v in data.items()
                    if self._matches_criteria(v, filter_criteria)
                }
            else:
                raise ToolError("Filter requires list or dictionary input")

            return {
                "original_count": len(data),
                "filtered_count": len(filtered_data),
                "filtered_data": filtered_data,
                "filter_criteria": filter_criteria,
            }

        except Exception as e:
            raise ToolError(f"Data filtering failed: {str(e)}")

    async def _aggregate_data(
        self, data: list[dict], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Aggregate data by specified key.

        Args:
            data: List of dictionaries to aggregate
            parameters: Aggregation parameters

        Returns:
            Aggregated data results
        """
        options = parameters.get("options", {})
        aggregation_key = options.get("aggregation_key")

        if not aggregation_key:
            raise ToolError("Aggregation key must be specified")

        # Simulate processing delay
        await asyncio.sleep(0.1)

        try:
            if not isinstance(data, list) or not all(
                isinstance(item, dict) for item in data
            ):
                raise ToolError("Aggregation requires list of dictionaries")

            aggregated = {}
            for item in data:
                if aggregation_key in item:
                    key_value = item[aggregation_key]
                    if key_value not in aggregated:
                        aggregated[key_value] = []
                    aggregated[key_value].append(item)

            # Calculate aggregation statistics
            result = {}
            for key, items in aggregated.items():
                result[key] = {"count": len(items), "items": items}

                # If items have numerical values, calculate statistics
                numerical_fields = {}
                for item in items:
                    for field, value in item.items():
                        if isinstance(value, (int, float)) and field != aggregation_key:
                            if field not in numerical_fields:
                                numerical_fields[field] = []
                            numerical_fields[field].append(value)

                for field, values in numerical_fields.items():
                    if values:
                        result[key][f"{field}_sum"] = sum(values)
                        result[key][f"{field}_avg"] = sum(values) / len(values)
                        result[key][f"{field}_min"] = min(values)
                        result[key][f"{field}_max"] = max(values)

            return {
                "aggregation_key": aggregation_key,
                "groups_count": len(result),
                "aggregated_data": result,
            }

        except Exception as e:
            raise ToolError(f"Data aggregation failed: {str(e)}")

    def _matches_criteria(self, item: Any, criteria: dict[str, Any]) -> bool:
        """
        Check if an item matches the filter criteria.

        Args:
            item: Item to check
            criteria: Filter criteria

        Returns:
            True if item matches criteria, False otherwise
        """
        if not criteria:
            return True

        for key, expected_value in criteria.items():
            if isinstance(item, dict):
                actual_value = item.get(key)
            else:
                # For non-dict items, treat the key as an attribute or direct comparison
                if key == "value":
                    actual_value = item
                else:
                    actual_value = getattr(item, key, None)

            # Simple equality check (could be extended for more complex operations)
            if actual_value != expected_value:
                return False

        return True
