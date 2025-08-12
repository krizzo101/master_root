"""
Module: output_formatter.py

Path: src/tools/code_generation/o3_code_generator/utils/output_formatter.py

Purpose: Centralized output formatting for analysis results.

This module provides the OutputFormatter class, which supports conversion of
analysis data to markdown, HTML, JSON, and YAML formats. It includes methods
for creating summary tables, timelines, and uses structured logging.

Classes:
    OutputFormatter: Provides formatting methods for various output types.

Usage:
    from src.tools.code_generation.o3_code_generator.utils.output_formatter import OutputFormatter

    formatter = OutputFormatter()
    markdown = formatter.to_markdown(data, "Title")
"""

from datetime import datetime
import json
from typing import Any

import yaml

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class OutputFormatter:
    """
    Centralized output formatting for analysis results.

    Attributes:
        logger: O3Logger instance for structured logging.
        timestamp: Timestamp string for output documents.
        default_markdown_template: Default template for markdown output.
        default_html_template: Default template for HTML output.
    """

    def __init__(self) -> None:
        """
        Initialize the OutputFormatter.

        Sets up default timestamp and templates, and initializes structured logging.
        """
        self.logger = get_logger()
        self.logger.log_info("Initializing OutputFormatter")
        self.timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.default_markdown_template: str = self._get_default_markdown_template()
        self.default_html_template: str = self._get_default_html_template()

    def to_markdown(
        self, data: dict[str, Any], title: str, template: str | None = None
    ) -> str:
        """
        Convert data to standardized markdown format.

        Args:
            data: Dictionary containing the data to format.
            title: Title for the markdown document.
            template: Optional custom template. If None, uses default template.

        Returns:
            Formatted markdown string.

        Raises:
            ValueError: If data is not a dictionary or title is empty.
            KeyError: If the template is missing required keys.
            RuntimeError: For unexpected formatting errors.
        """
        if not isinstance(data, dict):
            self.logger.log_error("Data must be a dictionary for markdown formatting")
            raise ValueError("Data must be a dictionary")
        else:
            pass
        if not title.strip():
            self.logger.log_error("Title cannot be empty for markdown formatting")
            raise ValueError("Title cannot be empty")
        else:
            pass
        tpl = template or self.default_markdown_template
        summary_table = self.create_summary_table(data)
        detailed_content = self._format_markdown_content(data)
        try:
            content = tpl.format(
                title=title,
                timestamp=self.timestamp,
                summary_table=summary_table,
                detailed_content=detailed_content,
            )
            self.logger.log_debug(f"Generated markdown content for '{title}'")
            return content
        except KeyError as e:
            self.logger.log_error(f"Template formatting missing key: {e}")
            raise KeyError(f"Template missing key: {e}") from e
        except Exception as e:
            self.logger.log_error(f"Unexpected error during markdown formatting: {e}")
            raise RuntimeError("Markdown formatting failed") from e
        else:
            pass
        finally:
            pass

    def to_html(
        self, data: dict[str, Any], title: str, template: str | None = None
    ) -> str:
        """
        Convert data to standardized HTML format.

        Args:
            data: Dictionary containing the data to format.
            title: Title for the HTML document.
            template: Optional custom template. If None, uses default template.

        Returns:
            Formatted HTML string with high-contrast accessibility features.

        Raises:
            ValueError: If data is not a dictionary or title is empty.
            KeyError: If the template is missing required keys.
            RuntimeError: For unexpected formatting errors.
        """
        if not isinstance(data, dict):
            self.logger.log_error("Data must be a dictionary for HTML formatting")
            raise ValueError("Data must be a dictionary")
        else:
            pass
        if not title.strip():
            self.logger.log_error("Title cannot be empty for HTML formatting")
            raise ValueError("Title cannot be empty")
        else:
            pass
        tpl = template or self.default_html_template
        summary_table = self._create_html_summary_table(data)
        detailed_content = self._format_html_content(data)
        try:
            content = tpl.format(
                title=title,
                timestamp=self.timestamp,
                summary_table=summary_table,
                detailed_content=detailed_content,
            )
            self.logger.log_debug(f"Generated HTML content for '{title}'")
            return content
        except KeyError as e:
            self.logger.log_error(f"Template formatting missing key: {e}")
            raise KeyError(f"Template missing key: {e}") from e
        except Exception as e:
            self.logger.log_error(f"Unexpected error during HTML formatting: {e}")
            raise RuntimeError("HTML formatting failed") from e
        else:
            pass
        finally:
            pass

    def to_json(self, data: dict[str, Any], pretty: bool = True) -> str:
        """
        Convert data to formatted JSON.

        Args:
            data: Dictionary containing the data to format.
            pretty: Whether to format with indentation for readability.

        Returns:
            Formatted JSON string.

        Raises:
            ValueError: If data is not a dictionary or serialization fails.
            RuntimeError: For unexpected formatting errors.
        """
        if not isinstance(data, dict):
            self.logger.log_error("Data must be a dictionary for JSON formatting")
            raise ValueError("Data must be a dictionary")
        else:
            pass
        try:
            result = (
                json.dumps(data, indent=2, ensure_ascii=False)
                if pretty
                else json.dumps(data, ensure_ascii=False)
            )
            self.logger.log_debug("Generated JSON content")
            return result
        except (TypeError, ValueError) as e:
            self.logger.log_error(f"JSON serialization error: {e}")
            raise ValueError("JSON serialization failed") from e
        except Exception as e:
            self.logger.log_error(f"Unexpected error during JSON formatting: {e}")
            raise RuntimeError("JSON formatting failed") from e
        else:
            pass
        finally:
            pass

    def to_yaml(self, data: dict[str, Any]) -> str:
        """
        Convert data to YAML format.

        Args:
            data: Dictionary containing the data to format.

        Returns:
            Formatted YAML string.

        Raises:
            ValueError: If data is not a dictionary or serialization fails.
            RuntimeError: For unexpected formatting errors.
        """
        if not isinstance(data, dict):
            self.logger.log_error("Data must be a dictionary for YAML formatting")
            raise ValueError("Data must be a dictionary")
        else:
            pass
        try:
            result = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            self.logger.log_debug("Generated YAML content")
            return result
        except yaml.YAMLError as e:
            self.logger.log_error(f"YAML serialization error: {e}")
            raise ValueError("YAML serialization failed") from e
        except Exception as e:
            self.logger.log_error(f"Unexpected error during YAML formatting: {e}")
            raise RuntimeError("YAML formatting failed") from e
        else:
            pass
        finally:
            pass

    def create_summary_table(self, data: dict[str, Any]) -> str:
        """
        Create summary table in markdown format.

        Args:
            data: Dictionary containing the data to summarize.

        Returns:
            Markdown table string.

        Raises:
            ValueError: If data is not a dictionary.
            RuntimeError: For unexpected errors during table creation.
        """
        if not isinstance(data, dict):
            self.logger.log_error(
                "Data must be a dictionary for summary table creation"
            )
            raise ValueError("Data must be a dictionary")
        else:
            pass
        try:
            rows: list[str] = ["| Field | Value |", "|-------|-------|"]
            for key, value in data.items():
                if isinstance(value, dict):
                    display_value = f"Dictionary ({len(value)} items)"
                elif isinstance(value, list):
                    display_value = f"List ({len(value)} items)"
                else:
                    display_value = str(value)[:100]
                key_escaped = str(key).replace("|", "\\|")
                val_escaped = display_value.replace("|", "\\|")
                rows.append(f"| {key_escaped} | {val_escaped} |")
            else:
                pass
            table = "\n".join(rows)
            self.logger.log_debug("Created markdown summary table")
            return table
        except Exception as e:
            self.logger.log_error(
                f"Unexpected error during summary table creation: {e}"
            )
            raise RuntimeError("Summary table creation failed") from e
        else:
            pass
        finally:
            pass

    def create_timeline(self, events: list[dict[str, Any]]) -> str:
        """
        Create timeline visualization in markdown format.

        Args:
            events: List of event dictionaries with 'timestamp' and 'description' keys.

        Returns:
            Markdown timeline string.

        Raises:
            ValueError: If events is not a list.
            RuntimeError: For unexpected errors during timeline creation.
        """
        if not isinstance(events, list):
            self.logger.log_error("Events must be a list for timeline creation")
            raise ValueError("Events must be a list")
        else:
            pass
        try:
            lines: list[str] = ["## Timeline", ""]
            sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
            for index, event in enumerate(sorted_events, start=1):
                ts = event.get("timestamp", "Unknown time")
                desc = event.get("description", "No description")
                lines.append(f"{index}. **{ts}** - {desc}")
            else:
                pass
            timeline = "\n".join(lines)
            self.logger.log_debug("Created markdown timeline")
            return timeline
        except Exception as e:
            self.logger.log_error(f"Unexpected error during timeline creation: {e}")
            raise RuntimeError("Timeline creation failed") from e
        else:
            pass
        finally:
            pass

    def _format_markdown_content(self, data: dict[str, Any]) -> str:
        """
        Recursively format data as markdown content.

        Args:
            data: Dictionary containing the data to format.

        Returns:
            Formatted markdown content string.
        """
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"### {key}")
                lines.append(self._format_markdown_content(value))
            elif isinstance(value, list):
                lines.append(f"### {key}")
                for idx, item in enumerate(value, start=1):
                    if isinstance(item, dict):
                        lines.append(f"#### Item {idx}")
                        lines.append(self._format_markdown_content(item))
                    else:
                        lines.append(f"- {item}")
                else:
                    pass
            else:
                lines.append(f"**{key}:** {value}")
        else:
            pass
        return "\n\n".join(lines)

    def _format_html_content(self, data: dict[str, Any]) -> str:
        """
        Recursively format data as HTML content.

        Args:
            data: Dictionary containing the data to format.

        Returns:
            Formatted HTML content string.
        """
        parts: list[str] = []
        for key, value in data.items():
            if isinstance(value, dict):
                parts.append(f'<h3 style="color: #ffffff;">{key}</h3>')
                parts.append(self._format_html_content(value))
            elif isinstance(value, list):
                parts.append(f'<h3 style="color: #ffffff;">{key}</h3><ul>')
                for item in value:
                    if isinstance(item, dict):
                        parts.append(f"<li>{self._format_html_content(item)}</li>")
                    else:
                        parts.append(f'<li style="color: #ffffff;">{item}</li>')
                else:
                    pass
                parts.append("</ul>")
            else:
                parts.append(
                    f'<p><strong style="color: #ffffff;">{key}:</strong> <span style="color: #ffffff;">{value}</span></p>'
                )
        else:
            pass
        return "\n".join(parts)

    def _create_html_summary_table(self, data: dict[str, Any]) -> str:
        """
        Create summary table in HTML format.

        Args:
            data: Dictionary containing the data to summarize.

        Returns:
            HTML table string with high-contrast styling.

        Raises:
            ValueError: If data is not a dictionary.
            RuntimeError: For unexpected errors during HTML table creation.
        """
        if not isinstance(data, dict):
            self.logger.log_error(
                "Data must be a dictionary for HTML summary table creation"
            )
            raise ValueError("Data must be a dictionary")
        else:
            pass
        try:
            html: list[str] = [
                '<table style="border-collapse: collapse; width: 100%; margin: 20px 0;">',
                "<thead>",
                '<tr style="background-color: #2c3e50;">',
                '<th style="border: 1px solid #ffffff; padding: 12px; text-align: left; color: #ffffff;">Field</th>',
                '<th style="border: 1px solid #ffffff; padding: 12px; text-align: left; color: #ffffff;">Value</th>',
                "</tr>",
                "</thead>",
                "<tbody>",
            ]
            for key, value in data.items():
                if isinstance(value, dict):
                    display = f"Dictionary ({len(value)} items)"
                elif isinstance(value, list):
                    display = f"List ({len(value)} items)"
                else:
                    display = str(value)[:100]
                html.extend(
                    [
                        '<tr style="background-color: #34495e;">',
                        f'<td style="border: 1px solid #ffffff; padding: 12px; color: #ffffff;">{key}</td>',
                        f'<td style="border: 1px solid #ffffff; padding: 12px; color: #ffffff;">{display}</td>',
                        "</tr>",
                    ]
                )
            else:
                pass
            html.extend(["</tbody>", "</table>"])
            table_html = "\n".join(html)
            self.logger.log_debug("Created HTML summary table")
            return table_html
        except Exception as e:
            self.logger.log_error(
                f"Unexpected error during HTML summary table creation: {e}"
            )
            raise RuntimeError("HTML summary table creation failed") from e
        else:
            pass
        finally:
            pass

    def _get_default_markdown_template(self) -> str:
        """
        Return the default markdown template.

        Returns:
            Default markdown template string.
        """
        return "# {title}\n\n**Generated:** {timestamp}\n\n## Summary\n\n{summary_table}\n\n## Detailed Analysis\n\n{detailed_content}\n\n---\n*Generated by O3 Code Generator*"

    def _get_default_html_template(self) -> str:
        """
        Return the default HTML template with high-contrast accessibility.

        Returns:
            Default HTML template string.
        """
        return '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{title}</title>\n    <style>\n        body {{ font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; background-color: #000000; color: #ffffff; margin: 0; padding: 20px; line-height: 1.6; }}\n        .container {{ max-width: 1200px; margin: 0 auto; background-color: #1a1a1a; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(255, 255, 255, 0.1); }}\n        h1 {{ color: #ffffff; border-bottom: 2px solid #ffffff; padding-bottom: 10px; }}\n        h2, h3 {{ color: #ffffff; margin-top: 30px; }}\n        .timestamp {{ color: #cccccc; font-style: italic; margin-bottom: 30px; }}\n        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ffffff; color: #cccccc; font-size: 0.9em; }}\n    </style>\n</head>\n<body>\n    <div class="container">\n        <h1>{title}</h1>\n        <div class="timestamp">Generated: {timestamp}</div>\n\n        <h2>Summary</h2>\n        {summary_table}\n\n        <h2>Detailed Analysis</h2>\n        {detailed_content}\n\n        <div class="footer">\n            Generated by O3 Code Generator\n        </div>\n    </div>\n</body>\n</html>'
