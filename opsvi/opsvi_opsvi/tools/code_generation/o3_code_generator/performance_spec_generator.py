"""TODO: Add module-level docstring."""

"\nPerformance Specification Generator - AI-powered performance specification generation using OpenAI's O3 models.\n\nThis script generates comprehensive performance specifications including load testing scenarios,\nperformance benchmarks, scalability requirements, and optimization guidelines using OpenAI's\nlatest O3 and O3-mini models.\n"
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    pass
try:
    from openai import OpenAI
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
        ConfigManager,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from o3_logger.logger import get_logger, setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from schemas.technical_spec_schemas import (
        OutputFormat,
        PerformanceSpecInput,
        PerformanceSpecOutput,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from prompts.technical_spec_prompts import PERFORMANCE_SPEC_SYSTEM_PROMPT
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class PerformanceSpecGenerator:
    """Main performance specification generator using OpenAI O3 models."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize the PerformanceSpecGenerator.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        log_config = self.config_manager.get_logging_config()
        setup_logger(log_config)
        self.logger = get_logger()
        self.logger.log_system_event("PerformanceSpecGenerator initialized")
        api_config = self.config_manager.get_api_config()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=api_config.base_url
        )
        self._create_directories()
        self.logger.log_info("PerformanceSpecGenerator initialization complete")

    def _create_directories(self) -> None:
        """Create necessary directories for the generator."""
        directories = [
            "generated_files/technical_specs/performance_specs",
            "logs",
            "config",
            "schemas",
            "prompts",
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.log_debug(f"Directory created/verified: {directory}")
        else:
            pass

    def define_performance_requirements(
        self, input_data: PerformanceSpecInput
    ) -> PerformanceSpecOutput:
        """
        Define comprehensive performance specifications.

        Args:
            input_data: Input data for performance specification generation

        Returns:
            PerformanceSpecOutput containing generated performance specifications
        """
        start_time = time.time()
        try:
            self.logger.log_info("Starting performance specification generation")
            self.logger.log_user_action(
                "performance_spec_generation_started",
                {
                    "output_format": input_data.output_format.value,
                    "model": input_data.model,
                },
            )
            prompt = self._build_prompt(input_data)
            self.logger.log_info(f"Calling O3 model: {input_data.model}")
            self.logger.log_api_call_start(input_data.model, len(prompt))
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {"role": "system", "content": PERFORMANCE_SPEC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            generation_time = time.time() - start_time
            content = response.choices[0].message.content
            self.logger.log_api_call_success(
                input_data.model,
                len(content),
                generation_time,
            )
            try:
                performance_specs = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.log_error(e, "Failed to parse O3 model response as JSON")
                raise ValueError(f"Invalid JSON response from O3 model: {e}")
            else:
                pass
            finally:
                pass
            base_filename = f"performance_spec_{int(time.time())}"
            output_files = self._save_performance_files(
                performance_specs["performance_specifications"],
                input_data.output_format,
                base_filename,
            )
            output = PerformanceSpecOutput(
                load_testing_specs=performance_specs["performance_specifications"][
                    "load_testing_specs"
                ],
                performance_benchmarks=performance_specs["performance_specifications"][
                    "performance_benchmarks"
                ],
                scalability_requirements=performance_specs[
                    "performance_specifications"
                ]["scalability_requirements"],
                resource_utilization=performance_specs["performance_specifications"][
                    "resource_utilization"
                ],
                monitoring_alerting=performance_specs["performance_specifications"][
                    "monitoring_alerting"
                ],
                optimization_guidelines=performance_specs["performance_specifications"][
                    "optimization_guidelines"
                ],
            )
            self.logger.log_info(
                f"Performance specification generation completed in {generation_time:.2f}s"
            )
            self.logger.log_user_action(
                "performance_spec_generation_completed",
                {"output_files": output_files, "generation_time": generation_time},
            )
            return output
        except Exception as e:
            generation_time = time.time() - start_time
            self.logger.log_error(e, "Performance specification generation failed")
            raise
        else:
            pass
        finally:
            pass

    def _build_prompt(self, input_data: PerformanceSpecInput) -> str:
        """
        Build the prompt for O3 model based on input data.

        Args:
            input_data: Input data for performance specification generation

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "Performance Requirements:",
            json.dumps(input_data.performance_requirements, indent=2),
            "",
            "Constraints:",
            json.dumps(input_data.constraints, indent=2),
        ]
        if input_data.load_patterns:
            prompt_parts.extend(
                ["", "Load Patterns:", json.dumps(input_data.load_patterns, indent=2)]
            )
        else:
            pass
        if input_data.scalability_requirements:
            prompt_parts.extend(
                [
                    "",
                    "Scalability Requirements:",
                    json.dumps(input_data.scalability_requirements, indent=2),
                ]
            )
        else:
            pass
        return "\n".join(prompt_parts)

    def _save_performance_files(
        self,
        performance_specs: dict[str, Any],
        output_format: OutputFormat,
        base_filename: str,
    ) -> list[str]:
        """
        Save performance specification files in the specified format.

        Args:
            performance_specs: The performance specification data to save
            output_format: The format to save in
            base_filename: Base filename for the output

        Returns:
            List of generated file paths
        """
        output_dir = Path("generated_files/technical_specs/performance_specs")
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []
        try:
            if output_format == OutputFormat.JSON:
                file_path = output_dir / f"{base_filename}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(performance_specs, f, indent=2)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.MARKDOWN:
                file_path = output_dir / f"{base_filename}.md"
                markdown_content = self._convert_to_markdown(performance_specs)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.YAML:
                import yaml

                file_path = output_dir / f"{base_filename}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(performance_specs, f, default_flow_style=False, indent=2)
                generated_files.append(str(file_path))
            else:
                pass
            self.logger.log_info(
                f"Saved performance specifications to: {generated_files}"
            )
            return generated_files
        except Exception as e:
            self.logger.log_error(
                e,
                f"Failed to save performance specifications in {output_format} format",
            )
            raise
        else:
            pass
        finally:
            pass

    def _convert_to_markdown(self, performance_specs: dict[str, Any]) -> str:
        """Convert performance specifications to Markdown format."""
        markdown_lines = ["# Performance Specifications", ""]
        if "load_testing_specs" in performance_specs:
            load_specs = performance_specs["load_testing_specs"]
            markdown_lines.extend(["## Load Testing Specifications", ""])
            for scenario in load_specs.get("scenarios", []):
                markdown_lines.extend(
                    [
                        f"### {scenario.get('name', '')}",
                        f"**Users:** {scenario.get('users', '')}",
                        f"**Duration:** {scenario.get('duration', '')}",
                        f"**Ramp Up:** {scenario.get('ramp_up', '')}",
                        "",
                    ]
                )
            else:
                pass
            markdown_lines.extend(
                [
                    f"**Tools:** {', '.join(load_specs.get('tools', []))}",
                    f"**Metrics:** {', '.join(load_specs.get('metrics', []))}",
                    "",
                ]
            )
        else:
            pass
        if "performance_benchmarks" in performance_specs:
            benchmarks = performance_specs["performance_benchmarks"]
            markdown_lines.extend(
                [
                    "## Performance Benchmarks",
                    "",
                    "### Baseline Metrics",
                    json.dumps(benchmarks.get("baseline_metrics", {}), indent=2),
                    "",
                    "### Target Metrics",
                    json.dumps(benchmarks.get("target_metrics", {}), indent=2),
                    "",
                    "### Acceptance Criteria",
                    "",
                ]
            )
            for criterion in benchmarks.get("acceptance_criteria", []):
                markdown_lines.append(f"- {criterion}")
            else:
                pass
            markdown_lines.append("")
        else:
            pass
        if "scalability_requirements" in performance_specs:
            scalability = performance_specs["scalability_requirements"]
            markdown_lines.extend(
                [
                    "## Scalability Requirements",
                    "",
                    "### Horizontal Scaling",
                    json.dumps(scalability.get("horizontal_scaling", {}), indent=2),
                    "",
                    "### Vertical Scaling",
                    json.dumps(scalability.get("vertical_scaling", {}), indent=2),
                    "",
                    "### Auto Scaling",
                    json.dumps(scalability.get("auto_scaling", {}), indent=2),
                    "",
                ]
            )
        else:
            pass
        if "resource_utilization" in performance_specs:
            resources = performance_specs["resource_utilization"]
            markdown_lines.extend(
                [
                    "## Resource Utilization",
                    "",
                    "### CPU Limits",
                    json.dumps(resources.get("cpu_limits", {}), indent=2),
                    "",
                    "### Memory Limits",
                    json.dumps(resources.get("memory_limits", {}), indent=2),
                    "",
                    "### Disk Limits",
                    json.dumps(resources.get("disk_limits", {}), indent=2),
                    "",
                    "### Network Limits",
                    json.dumps(resources.get("network_limits", {}), indent=2),
                    "",
                ]
            )
        else:
            pass
        if "monitoring_alerting" in performance_specs:
            monitoring = performance_specs["monitoring_alerting"]
            markdown_lines.extend(["## Monitoring and Alerting", "", "### Metrics", ""])
            for metric in monitoring.get("metrics", []):
                markdown_lines.append(f"- {metric}")
            else:
                pass
            markdown_lines.append("")
            markdown_lines.extend(["### Alerts", ""])
            for alert in monitoring.get("alerts", []):
                markdown_lines.append(f"- {alert}")
            else:
                pass
            markdown_lines.append("")
            markdown_lines.extend(["### Dashboards", ""])
            for dashboard in monitoring.get("dashboards", []):
                markdown_lines.append(f"- {dashboard}")
            else:
                pass
            markdown_lines.append("")
        else:
            pass
        if "optimization_guidelines" in performance_specs:
            markdown_lines.extend(["## Optimization Guidelines", ""])
            for guideline in performance_specs["optimization_guidelines"]:
                markdown_lines.append(f"- {guideline}")
            else:
                pass
            markdown_lines.append("")
        else:
            pass
        return "\n".join(markdown_lines)

    def specify_benchmarks(
        self, requirements: dict[str, Any], constraints: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Specify performance benchmarks based on requirements and constraints.

        Args:
            requirements: Performance requirements
            constraints: Performance constraints

        Returns:
            Dictionary containing benchmark specifications
        """
        self.logger.log_info("Specifying performance benchmarks")
        prompt = f"\n        Performance Requirements: {json.dumps(requirements, indent=2)}\n        Constraints: {json.dumps(constraints, indent=2)}\n\n        Specify performance benchmarks including:\n        1. Response time benchmarks\n        2. Throughput benchmarks\n        3. Resource utilization benchmarks\n        4. Scalability benchmarks\n        5. Availability benchmarks\n        6. Error rate benchmarks\n        7. Latency benchmarks\n        8. Capacity benchmarks\n        "
        try:
            response = self.client.responses.create(
                model="o3-mini",
                instructions="You are an expert performance engineer. Generate comprehensive benchmark specifications in JSON format.",
                input=prompt,
                max_tokens=4000,
            )
            return json.loads(response.output[0].content[0].text)
        except Exception as e:
            self.logger.log_error(e, "Failed to specify performance benchmarks")
            raise
        else:
            pass
        finally:
            pass

    def generate_test_scenarios(
        self, performance_specs: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate performance test scenarios.

        Args:
            performance_specs: Performance specifications

        Returns:
            List of test scenario specifications
        """
        self.logger.log_info("Generating performance test scenarios")
        prompt = f"\n        Performance Specifications: {json.dumps(performance_specs, indent=2)}\n\n        Generate performance test scenarios including:\n        1. Load testing scenarios\n        2. Stress testing scenarios\n        3. Spike testing scenarios\n        4. Endurance testing scenarios\n        5. Scalability testing scenarios\n        6. Volume testing scenarios\n        7. Soak testing scenarios\n        8. Performance regression testing\n        "
        try:
            response = self.client.responses.create(
                model="o3-mini",
                instructions="You are an expert performance test designer. Generate comprehensive test scenarios in JSON format.",
                input=prompt,
                max_tokens=4000,
            )
            return json.loads(response.output[0].content[0].text)
        except Exception as e:
            self.logger.log_error(e, "Failed to generate test scenarios")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """Main entry point for the PerformanceSpecGenerator."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive performance specifications using O3 models"
    )
    parser.add_argument(
        "input_file",
        help="Input JSON/YAML file with performance specification requirements",
    )
    parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save generated performance specifications to files",
    )
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    try:
        generator = PerformanceSpecGenerator(args.config)
        with open(args.input_file) as f:
            input_data_dict = json.load(f)
        input_data = PerformanceSpecInput(**input_data_dict)
        output = generator.define_performance_requirements(input_data)
        if args.save_file:
            pass
        else:
            pass
    except Exception:
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
