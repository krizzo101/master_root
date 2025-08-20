"""ReporterAgent - Reporting and documentation."""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class ReportFormat(Enum):
    """Report output formats."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"


class ReportType(Enum):
    """Types of reports."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    AUDIT = "audit"
    PROGRESS = "progress"
    PERFORMANCE = "performance"
    ERROR = "error"
    CUSTOM = "custom"


class DocumentType(Enum):
    """Types of documentation."""

    API = "api"
    USER_GUIDE = "user_guide"
    TECHNICAL = "technical"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    CHANGELOG = "changelog"
    README = "readme"


@dataclass
class Section:
    """Report section."""

    id: str
    title: str
    content: Any
    level: int = 1
    subsections: List["Section"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "subsections": [s.to_dict() for s in self.subsections],
            "metadata": self.metadata,
        }

    def to_markdown(self, base_level: int = 1) -> str:
        """Convert to markdown."""
        level = base_level + self.level - 1
        header = "#" * level
        lines = [f"{header} {self.title}\n"]

        if isinstance(self.content, str):
            lines.append(self.content)
        elif isinstance(self.content, list):
            for item in self.content:
                lines.append(f"- {item}")
        elif isinstance(self.content, dict):
            for key, value in self.content.items():
                lines.append(f"**{key}**: {value}")

        for subsection in self.subsections:
            lines.append("\n" + subsection.to_markdown(base_level + 1))

        return "\n".join(lines)


@dataclass
class Report:
    """Generated report."""

    id: str
    title: str
    type: ReportType
    format: ReportFormat
    sections: List[Section] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def add_section(self, section: Section):
        """Add a section to the report."""
        self.sections.append(section)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "format": self.format.value,
            "sections": [s.to_dict() for s in self.sections],
            "summary": self.summary,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    def render(self) -> str:
        """Render report in specified format."""
        if self.format == ReportFormat.MARKDOWN:
            return self._render_markdown()
        elif self.format == ReportFormat.HTML:
            return self._render_html()
        elif self.format == ReportFormat.JSON:
            return self._render_json()
        elif self.format == ReportFormat.CSV:
            return self._render_csv()
        else:
            return self._render_text()

    def _render_text(self) -> str:
        """Render as plain text."""
        lines = [f"{self.title}", "=" * len(self.title), "", self.summary, ""]

        for section in self.sections:
            lines.append(section.title)
            lines.append("-" * len(section.title))

            if isinstance(section.content, str):
                lines.append(section.content)
            else:
                lines.append(str(section.content))

            lines.append("")

        return "\n".join(lines)

    def _render_markdown(self) -> str:
        """Render as markdown."""
        lines = [
            f"# {self.title}\n",
            f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.created_at))}*\n",
            "## Summary\n",
            self.summary,
            "",
        ]

        for section in self.sections:
            lines.append(section.to_markdown())
            lines.append("")

        return "\n".join(lines)

    def _render_html(self) -> str:
        """Render as HTML."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; }",
            ".summary { background: #f0f0f0; padding: 15px; border-radius: 5px; }",
            ".section { margin: 20px 0; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{self.title}</h1>",
            f'<div class="summary">{self.summary}</div>',
        ]

        for section in self.sections:
            html.append(f'<div class="section">')
            html.append(f"<h2>{section.title}</h2>")

            if isinstance(section.content, str):
                html.append(f"<p>{section.content}</p>")
            elif isinstance(section.content, list):
                html.append("<ul>")
                for item in section.content:
                    html.append(f"<li>{item}</li>")
                html.append("</ul>")
            elif isinstance(section.content, dict):
                html.append("<dl>")
                for key, value in section.content.items():
                    html.append(f"<dt><strong>{key}</strong></dt>")
                    html.append(f"<dd>{value}</dd>")
                html.append("</dl>")

            html.append("</div>")

        html.extend(["</body>", "</html>"])
        return "\n".join(html)

    def _render_json(self) -> str:
        """Render as JSON."""
        return json.dumps(self.to_dict(), indent=2)

    def _render_csv(self) -> str:
        """Render as CSV (simplified)."""
        lines = [
            "Section,Content",
            f'"Title","{self.title}"',
            f'"Summary","{self.summary}"',
        ]

        for section in self.sections:
            content_str = str(section.content).replace('"', '""')
            lines.append(f'"{section.title}","{content_str}"')

        return "\n".join(lines)


@dataclass
class Documentation:
    """Documentation structure."""

    id: str
    title: str
    type: DocumentType
    content: str
    version: str = "1.0"
    author: str = ""
    sections: List[Section] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "content": self.content,
            "version": self.version,
            "author": self.author,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
        }


class ReporterAgent(BaseAgent):
    """Generates reports and documentation."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize reporter agent."""
        super().__init__(
            config
            or AgentConfig(
                name="ReporterAgent",
                description="Reporting and documentation",
                capabilities=["report", "document", "summarize", "format", "export"],
                max_retries=2,
                timeout=60,
            )
        )
        self.reports: Dict[str, Report] = {}
        self.documentation: Dict[str, Documentation] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._report_counter = 0
        self._section_counter = 0
        self._doc_counter = 0
        self._register_templates()

    def initialize(self) -> bool:
        """Initialize the reporter agent."""
        logger.info("reporter_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reporting task."""
        action = task.get("action", "report")

        if action == "report":
            return self._generate_report(task)
        elif action == "document":
            return self._generate_documentation(task)
        elif action == "summarize":
            return self._summarize_data(task)
        elif action == "format":
            return self._format_content(task)
        elif action == "export":
            return self._export_report(task)
        elif action == "create_section":
            return self._create_section(task)
        elif action == "compile":
            return self._compile_reports(task)
        elif action == "template":
            return self._apply_template(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def generate_report(
        self,
        title: str,
        data: Any,
        report_type: ReportType = ReportType.SUMMARY,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> Report:
        """Generate a report."""
        result = self.execute(
            {
                "action": "report",
                "title": title,
                "data": data,
                "report_type": report_type.value,
                "format": format.value,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["report"]

    def _register_templates(self):
        """Register report templates."""
        # Executive summary template
        self.templates["executive"] = {
            "sections": [
                {"title": "Executive Summary", "key": "summary"},
                {"title": "Key Findings", "key": "findings"},
                {"title": "Recommendations", "key": "recommendations"},
                {"title": "Next Steps", "key": "next_steps"},
            ]
        }

        # Technical report template
        self.templates["technical"] = {
            "sections": [
                {"title": "Overview", "key": "overview"},
                {"title": "Methodology", "key": "methodology"},
                {"title": "Results", "key": "results"},
                {"title": "Analysis", "key": "analysis"},
                {"title": "Conclusion", "key": "conclusion"},
            ]
        }

        # Progress report template
        self.templates["progress"] = {
            "sections": [
                {"title": "Status", "key": "status"},
                {"title": "Completed Tasks", "key": "completed"},
                {"title": "In Progress", "key": "in_progress"},
                {"title": "Blocked Items", "key": "blocked"},
                {"title": "Timeline", "key": "timeline"},
            ]
        }

    def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report from data."""
        title = task.get("title", "Untitled Report")
        data = task.get("data")
        report_type = task.get("report_type", "summary")
        format_type = task.get("format", "markdown")

        if data is None:
            return {"error": "Data is required"}

        # Create report
        self._report_counter += 1
        report = Report(
            id=f"report_{self._report_counter}",
            title=title,
            type=ReportType[report_type.upper()],
            format=ReportFormat[format_type.upper()],
        )

        # Generate sections based on report type
        if report.type == ReportType.SUMMARY:
            sections = self._create_summary_sections(data)
        elif report.type == ReportType.DETAILED:
            sections = self._create_detailed_sections(data)
        elif report.type == ReportType.EXECUTIVE:
            sections = self._create_executive_sections(data)
        elif report.type == ReportType.TECHNICAL:
            sections = self._create_technical_sections(data)
        else:
            sections = self._create_generic_sections(data)

        for section in sections:
            report.add_section(section)

        # Generate summary
        report.summary = self._generate_summary(data, report.type)

        # Store report
        self.reports[report.id] = report

        # Render report
        rendered = report.render()

        logger.info(
            "report_generated",
            report_id=report.id,
            type=report_type,
            format=format_type,
            sections_count=len(report.sections),
        )

        return {"report": report, "rendered": rendered, "report_id": report.id}

    def _create_summary_sections(self, data: Any) -> List[Section]:
        """Create summary report sections."""
        sections = []

        # Overview section
        self._section_counter += 1
        overview = Section(
            id=f"section_{self._section_counter}",
            title="Overview",
            content=self._create_overview(data),
        )
        sections.append(overview)

        # Key points section
        if isinstance(data, dict):
            self._section_counter += 1
            key_points = Section(
                id=f"section_{self._section_counter}",
                title="Key Points",
                content=list(data.keys())[:10],
            )
            sections.append(key_points)

        # Statistics section
        self._section_counter += 1
        stats = Section(
            id=f"section_{self._section_counter}",
            title="Statistics",
            content=self._calculate_statistics(data),
        )
        sections.append(stats)

        return sections

    def _create_detailed_sections(self, data: Any) -> List[Section]:
        """Create detailed report sections."""
        sections = []

        # Start with summary sections
        sections.extend(self._create_summary_sections(data))

        # Add detailed data sections
        if isinstance(data, dict):
            for key, value in data.items():
                self._section_counter += 1
                section = Section(
                    id=f"section_{self._section_counter}",
                    title=str(key).replace("_", " ").title(),
                    content=self._format_value(value),
                    level=2,
                )
                sections.append(section)
        elif isinstance(data, list):
            for i, item in enumerate(data[:20]):  # Limit to first 20 items
                self._section_counter += 1
                section = Section(
                    id=f"section_{self._section_counter}",
                    title=f"Item {i+1}",
                    content=self._format_value(item),
                    level=2,
                )
                sections.append(section)

        return sections

    def _create_executive_sections(self, data: Any) -> List[Section]:
        """Create executive report sections."""
        sections = []
        template = self.templates["executive"]

        for section_def in template["sections"]:
            self._section_counter += 1

            # Extract content from data
            if isinstance(data, dict):
                content = data.get(section_def["key"], "No data available")
            else:
                content = self._generate_executive_content(data, section_def["key"])

            section = Section(
                id=f"section_{self._section_counter}",
                title=section_def["title"],
                content=content,
            )
            sections.append(section)

        return sections

    def _create_technical_sections(self, data: Any) -> List[Section]:
        """Create technical report sections."""
        sections = []
        template = self.templates["technical"]

        for section_def in template["sections"]:
            self._section_counter += 1

            # Extract content from data
            if isinstance(data, dict):
                content = data.get(
                    section_def["key"],
                    self._generate_technical_content(data, section_def["key"]),
                )
            else:
                content = self._generate_technical_content(data, section_def["key"])

            section = Section(
                id=f"section_{self._section_counter}",
                title=section_def["title"],
                content=content,
            )
            sections.append(section)

        return sections

    def _create_generic_sections(self, data: Any) -> List[Section]:
        """Create generic report sections."""
        sections = []

        # Data section
        self._section_counter += 1
        data_section = Section(
            id=f"section_{self._section_counter}",
            title="Data",
            content=self._format_value(data),
        )
        sections.append(data_section)

        # Metadata section
        self._section_counter += 1
        metadata = Section(
            id=f"section_{self._section_counter}",
            title="Metadata",
            content={
                "Type": type(data).__name__,
                "Size": len(str(data)),
                "Generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        sections.append(metadata)

        return sections

    def _generate_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation."""
        title = task.get("title", "Documentation")
        content = task.get("content", "")
        doc_type = task.get("doc_type", "technical")
        version = task.get("version", "1.0")

        # Create documentation
        self._doc_counter += 1
        doc = Documentation(
            id=f"doc_{self._doc_counter}",
            title=title,
            type=DocumentType[doc_type.upper()],
            content=content,
            version=version,
        )

        # Add sections if provided
        sections_data = task.get("sections", [])
        for section_data in sections_data:
            self._section_counter += 1
            section = Section(
                id=f"section_{self._section_counter}",
                title=section_data.get("title", "Section"),
                content=section_data.get("content", ""),
            )
            doc.sections.append(section)

        # Store documentation
        self.documentation[doc.id] = doc

        return {"documentation": doc.to_dict(), "doc_id": doc.id}

    def _summarize_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize data."""
        data = task.get("data")
        max_length = task.get("max_length", 500)

        if data is None:
            return {"error": "Data is required"}

        summary = self._create_summary(data, max_length)

        return {
            "summary": summary,
            "original_length": len(str(data)),
            "summary_length": len(summary),
        }

    def _format_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format content for output."""
        content = task.get("content")
        format_type = task.get("format", "text")

        if content is None:
            return {"error": "Content is required"}

        formatted = self._apply_format(content, format_type)

        return {"formatted": formatted, "format": format_type}

    def _export_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Export report to file."""
        report_id = task.get("report_id")
        file_path = task.get("file_path")

        if not report_id or report_id not in self.reports:
            return {"error": f"Report {report_id} not found"}

        report = self.reports[report_id]
        content = report.render()

        # In real implementation, would write to file
        # For now, just return the content

        return {"exported": True, "file_path": file_path, "size": len(content)}

    def _create_section(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a report section."""
        title = task.get("title", "Section")
        content = task.get("content", "")
        level = task.get("level", 1)

        self._section_counter += 1
        section = Section(
            id=f"section_{self._section_counter}",
            title=title,
            content=content,
            level=level,
        )

        return {"section": section.to_dict(), "section_id": section.id}

    def _compile_reports(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Compile multiple reports."""
        report_ids = task.get("report_ids", [])
        title = task.get("title", "Compiled Report")

        if not report_ids:
            return {"error": "Report IDs are required"}

        # Create compiled report
        self._report_counter += 1
        compiled = Report(
            id=f"report_{self._report_counter}",
            title=title,
            type=ReportType.DETAILED,
            format=ReportFormat.MARKDOWN,
        )

        # Add sections from each report
        for report_id in report_ids:
            if report_id in self.reports:
                report = self.reports[report_id]

                # Add report as section
                self._section_counter += 1
                report_section = Section(
                    id=f"section_{self._section_counter}",
                    title=report.title,
                    content=report.summary,
                    subsections=report.sections,
                )
                compiled.add_section(report_section)

        # Store compiled report
        self.reports[compiled.id] = compiled

        return {
            "compiled_report": compiled.to_dict(),
            "report_id": compiled.id,
            "reports_included": len(report_ids),
        }

    def _apply_template(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply template to data."""
        data = task.get("data")
        template_name = task.get("template", "executive")

        if data is None:
            return {"error": "Data is required"}

        if template_name not in self.templates:
            return {"error": f"Template {template_name} not found"}

        template = self.templates[template_name]
        sections = []

        for section_def in template["sections"]:
            self._section_counter += 1

            # Extract content based on key
            if isinstance(data, dict):
                content = data.get(section_def["key"], "No data")
            else:
                content = f"Data: {str(data)[:200]}"

            section = Section(
                id=f"section_{self._section_counter}",
                title=section_def["title"],
                content=content,
            )
            sections.append(section)

        return {
            "sections": [s.to_dict() for s in sections],
            "template_applied": template_name,
        }

    # Helper methods
    def _create_overview(self, data: Any) -> str:
        """Create data overview."""
        if isinstance(data, dict):
            return f"Dictionary with {len(data)} keys"
        elif isinstance(data, list):
            return f"List with {len(data)} items"
        elif isinstance(data, str):
            return f"String with {len(data)} characters"
        else:
            return f"Data of type {type(data).__name__}"

    def _calculate_statistics(self, data: Any) -> Dict[str, Any]:
        """Calculate basic statistics."""
        stats = {"Type": type(data).__name__, "Size": len(str(data))}

        if isinstance(data, (list, dict)):
            stats["Length"] = len(data)

        if isinstance(data, str):
            stats["Lines"] = data.count("\n") + 1
            stats["Words"] = len(data.split())

        return stats

    def _format_value(self, value: Any) -> Any:
        """Format value for display."""
        if isinstance(value, (dict, list)):
            return (
                json.dumps(value, indent=2)
                if len(str(value)) < 1000
                else str(value)[:1000] + "..."
            )
        elif isinstance(value, str) and len(value) > 500:
            return value[:500] + "..."
        else:
            return value

    def _generate_summary(self, data: Any, report_type: ReportType) -> str:
        """Generate report summary."""
        if report_type == ReportType.EXECUTIVE:
            return "Executive summary providing high-level overview and key decisions."
        elif report_type == ReportType.TECHNICAL:
            return "Technical analysis with detailed findings and methodologies."
        elif report_type == ReportType.PROGRESS:
            return "Progress update on current status and timeline."
        else:
            return self._create_summary(data, 200)

    def _create_summary(self, data: Any, max_length: int) -> str:
        """Create data summary."""
        summary = str(data)
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."
        return summary

    def _generate_executive_content(self, data: Any, key: str) -> str:
        """Generate executive report content."""
        if key == "summary":
            return self._create_summary(data, 300)
        elif key == "findings":
            return "Key findings from analysis"
        elif key == "recommendations":
            return "Strategic recommendations based on findings"
        elif key == "next_steps":
            return "Proposed action items"
        else:
            return "Content pending"

    def _generate_technical_content(self, data: Any, key: str) -> str:
        """Generate technical report content."""
        if key == "overview":
            return self._create_overview(data)
        elif key == "methodology":
            return "Analysis methodology and approach"
        elif key == "results":
            return f"Results: {self._format_value(data)}"
        elif key == "analysis":
            return "Detailed technical analysis"
        elif key == "conclusion":
            return "Technical conclusions and implications"
        else:
            return "Technical content"

    def _apply_format(self, content: Any, format_type: str) -> str:
        """Apply formatting to content."""
        if format_type == "json":
            return (
                json.dumps(content, indent=2)
                if not isinstance(content, str)
                else content
            )
        elif format_type == "markdown":
            if isinstance(content, dict):
                lines = []
                for key, value in content.items():
                    lines.append(f"**{key}**: {value}")
                return "\n".join(lines)
            elif isinstance(content, list):
                return "\n".join(f"- {item}" for item in content)
            else:
                return str(content)
        elif format_type == "html":
            if isinstance(content, str):
                return f"<p>{content}</p>"
            else:
                return f"<pre>{json.dumps(content, indent=2)}</pre>"
        else:
            return str(content)

    def shutdown(self) -> bool:
        """Shutdown the reporter agent."""
        logger.info(
            "reporter_agent_shutdown",
            reports_count=len(self.reports),
            docs_count=len(self.documentation),
        )
        self.reports.clear()
        self.documentation.clear()
        self.templates.clear()
        return True
