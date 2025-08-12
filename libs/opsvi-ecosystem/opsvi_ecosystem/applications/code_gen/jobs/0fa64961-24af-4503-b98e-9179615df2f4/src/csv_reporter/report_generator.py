"""
Report Generator module: Formats data processor output to various report formats (text, json).
Supports Jinja2-based templating for extensibility.
"""
import json
from typing import Any

from jinja2 import BaseLoader, Environment

from csv_reporter.config import Config

SUPPORTED_FORMATS = ["text", "json"]

_TEXT_TEMPLATE = """
CSV Analysis Report
===================

{% for column, stats in summary.items() %}
Column: {{ column }}
  Type: {{ stats.type }}
  {% if stats.type == 'numeric' %}
    Count:   {{ stats.count }}
    Missing: {{ stats.missing }}
    Mean:    {{ stats.mean }}
    Std:     {{ stats.std }}
    Min:     {{ stats.min }}
    Max:     {{ stats.max }}
  {% else %}
    Unique values: {{ stats.unique_count }}
    Missing:       {{ stats.missing }}
    {% if stats.top %}
      Top values:
        {%- for v, c in stats.top %}
          - {{ v | string | truncate(40, True, '...') }}: {{ c }}
        {%- endfor %}
    {% endif %}
  {% endif %}

{% endfor %}
"""


class ReportGenerator:
    """
    Formats processed CSV report data to consistent textual or structured output.
    Supports extensible formats (text, json), with pluggable templating.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.env = Environment(loader=BaseLoader())

    def generate_report(self, summary: dict[str, Any], format: str = "text") -> str:
        """
        Generates a formatted report string in the requested format.

        Args:
            summary: Summary dictionary produced by DataProcessor.
            format: 'text' or 'json'
        Returns:
            Formatted report. (str)
        Raises:
            ValueError: For unsupported formats or missing data.
        """
        if format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported report format: {format}")
        if format == "text":
            template = self.env.from_string(_TEXT_TEMPLATE)
            return template.render(summary=summary)
        elif format == "json":
            try:
                return json.dumps(summary, indent=2)
            except Exception as e:
                raise ValueError(f"Unable to serialize to JSON: {e}") from e
