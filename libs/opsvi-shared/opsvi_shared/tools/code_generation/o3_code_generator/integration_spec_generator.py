"""
Integration Specification Generator - AI-powered integration specification generation using OpenAI's O3 models.

This script generates comprehensive integration specifications for external services, message queues,
event streams, and data synchronization using OpenAI's latest O3 and O3-mini models.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Optional

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
        IntegrationSpecInput,
        IntegrationSpecOutput,
        OutputFormat,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from prompts.technical_spec_prompts import INTEGRATION_SPEC_SYSTEM_PROMPT
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class IntegrationSpecGenerator:
    """Main integration specification generator using OpenAI O3 models."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the IntegrationSpecGenerator.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        log_config = self.config_manager.get_logging_config()
        setup_logger(log_config)
        self.logger = get_logger()
        self.logger.log_system_event("IntegrationSpecGenerator initialized")
        api_config = self.config_manager.get_api_config()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=api_config.base_url
        )
        self._create_directories()
        self.logger.log_info("IntegrationSpecGenerator initialization complete")

    def _create_directories(self) -> None:
        """Create necessary directories for the generator."""
        directories = [
            "generated_files/technical_specs/integration_specs",
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

    def define_integrations(
        self, input_data: IntegrationSpecInput
    ) -> IntegrationSpecOutput:
        """
        Define comprehensive integration specifications.

        Args:
            input_data: Input data for integration specification generation

        Returns:
            IntegrationSpecOutput containing generated integration specifications
        """
        start_time = time.time()
        try:
            self.logger.log_info("Starting integration specification generation")
            self.logger.log_user_action(
                "integration_spec_generation_started",
                {
                    "external_services": len(input_data.external_services),
                    "protocols": len(input_data.protocols),
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
                    {"role": "system", "content": INTEGRATION_SPEC_SYSTEM_PROMPT},
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
                integration_specs = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.log_error(e, "Failed to parse O3 model response as JSON")
                raise ValueError(f"Invalid JSON response from O3 model: {e}")
            else:
                pass
            finally:
                pass
            base_filename = f"integration_spec_{int(time.time())}"
            output_files = self._save_integration_files(
                integration_specs["integration_specifications"],
                input_data.output_format,
                base_filename,
            )
            output = IntegrationSpecOutput(
                external_integrations=integration_specs["integration_specifications"][
                    "external_integrations"
                ],
                message_queue_specs=integration_specs["integration_specifications"][
                    "message_queue_specs"
                ],
                event_stream_specs=integration_specs["integration_specifications"][
                    "event_stream_specs"
                ],
                data_sync_specs=integration_specs["integration_specifications"][
                    "data_sync_specs"
                ],
                service_mesh_config=integration_specs["integration_specifications"][
                    "service_mesh_config"
                ],
                api_gateway_config=integration_specs["integration_specifications"][
                    "api_gateway_config"
                ],
            )
            self.logger.log_info(
                f"Integration specification generation completed in {generation_time:.2f}s"
            )
            self.logger.log_user_action(
                "integration_spec_generation_completed",
                {"output_files": output_files, "generation_time": generation_time},
            )
            return output
        except Exception as e:
            generation_time = time.time() - start_time
            self.logger.log_error(e, "Integration specification generation failed")
            raise
        else:
            pass
        finally:
            pass

    def _build_prompt(self, input_data: IntegrationSpecInput) -> str:
        """
        Build the prompt for O3 model based on input data.

        Args:
            input_data: Input data for integration specification generation

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"System Architecture: {input_data.system_architecture}",
            "",
            "Integration Requirements:",
            json.dumps(input_data.integration_requirements, indent=2),
            "",
            f"External Services: {', '.join(input_data.external_services)}",
            f"Protocols: {', '.join(input_data.protocols)}",
        ]
        return "\n".join(prompt_parts)

    def _save_integration_files(
        self,
        integration_specs: dict[str, Any],
        output_format: OutputFormat,
        base_filename: str,
    ) -> list[str]:
        """
        Save integration specification files in the specified format.

        Args:
            integration_specs: The integration specification data to save
            output_format: The format to save in
            base_filename: Base filename for the output

        Returns:
            List of generated file paths
        """
        output_dir = Path("generated_files/technical_specs/integration_specs")
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []
        try:
            if output_format == OutputFormat.JSON:
                file_path = output_dir / f"{base_filename}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(integration_specs, f, indent=2)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.MARKDOWN:
                file_path = output_dir / f"{base_filename}.md"
                markdown_content = self._convert_to_markdown(integration_specs)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.YAML:
                import yaml

                file_path = output_dir / f"{base_filename}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(integration_specs, f, default_flow_style=False, indent=2)
                generated_files.append(str(file_path))
            else:
                pass
            self.logger.log_info(
                f"Saved integration specifications to: {generated_files}"
            )
            return generated_files
        except Exception as e:
            self.logger.log_error(
                e,
                f"Failed to save integration specifications in {output_format} format",
            )
            raise
        else:
            pass
        finally:
            pass

    def _convert_to_markdown(self, integration_specs: dict[str, Any]) -> str:
        """Convert integration specifications to Markdown format."""
        markdown_lines = ["# Integration Specifications", ""]
        if "external_integrations" in integration_specs:
            markdown_lines.extend(["## External Service Integrations", ""])
            for integration in integration_specs["external_integrations"]:
                markdown_lines.extend(
                    [
                        f"### {integration.get('service_name', '')}",
                        f"**Endpoint:** {integration.get('endpoint', '')}",
                        f"**Authentication:** {json.dumps(integration.get('authentication', {}), indent=2)}",
                        f"**Rate Limits:** {json.dumps(integration.get('rate_limits', {}), indent=2)}",
                        f"**Error Handling:** {json.dumps(integration.get('error_handling', {}), indent=2)}",
                        "",
                    ]
                )
            else:
                pass
        else:
            pass
        if "message_queue_specs" in integration_specs:
            markdown_lines.extend(["## Message Queue Specifications", ""])
            for queue in integration_specs["message_queue_specs"]:
                markdown_lines.extend(
                    [
                        f"### {queue.get('queue_name', '')}",
                        f"**Type:** {queue.get('type', '')}",
                        f"**Configuration:** {json.dumps(queue.get('configuration', {}), indent=2)}",
                        f"**Routing:** {json.dumps(queue.get('routing', {}), indent=2)}",
                        "",
                    ]
                )
            else:
                pass
        else:
            pass
        if "event_stream_specs" in integration_specs:
            markdown_lines.extend(["## Event Stream Specifications", ""])
            for stream in integration_specs["event_stream_specs"]:
                markdown_lines.extend(
                    [
                        f"### {stream.get('stream_name', '')}",
                        f"**Platform:** {stream.get('platform', '')}",
                        f"**Topics:** {', '.join(stream.get('topics', []))}",
                        f"**Consumers:** {len(stream.get('consumers', []))}",
                        f"**Producers:** {len(stream.get('producers', []))}",
                        "",
                    ]
                )
            else:
                pass
        else:
            pass
        if "service_mesh_config" in integration_specs:
            mesh_config = integration_specs["service_mesh_config"]
            markdown_lines.extend(
                [
                    "## Service Mesh Configuration",
                    "",
                    f"**Mesh Type:** {mesh_config.get('mesh_type', '')}",
                    f"**Services:** {len(mesh_config.get('services', []))}",
                    f"**Policies:** {json.dumps(mesh_config.get('policies', {}), indent=2)}",
                    "",
                ]
            )
        else:
            pass
        if "api_gateway_config" in integration_specs:
            gateway_config = integration_specs["api_gateway_config"]
            markdown_lines.extend(
                [
                    "## API Gateway Configuration",
                    "",
                    f"**Gateway Type:** {gateway_config.get('gateway_type', '')}",
                    f"**Routes:** {len(gateway_config.get('routes', []))}",
                    f"**Policies:** {json.dumps(gateway_config.get('policies', {}), indent=2)}",
                    "",
                ]
            )
        else:
            pass
        return "\n".join(markdown_lines)

    def specify_protocols(
        self, external_services: list[str], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Specify integration protocols for external services.

        Args:
            external_services: List of external services to integrate with
            requirements: Integration requirements

        Returns:
            Dictionary containing protocol specifications
        """
        self.logger.log_info("Specifying integration protocols")
        prompt = f"\n        External Services: {', '.join(external_services)}\n        Requirements: {json.dumps(requirements, indent=2)}\n\n        Specify integration protocols including:\n        1. REST API protocols\n        2. GraphQL protocols\n        3. gRPC protocols\n        4. Message queue protocols\n        5. Event streaming protocols\n        6. Data synchronization protocols\n        7. Authentication protocols\n        8. Error handling protocols\n        "
        try:
            response = self.client.responses.create(
                model="o3-mini",
                instructions="You are an expert integration protocol specialist. Generate comprehensive protocol specifications in JSON format.",
                input=prompt,
                max_tokens=4000,
            )
            return json.loads(response.output[0].content[0].text)
        except Exception as e:
            self.logger.log_error(e, "Failed to specify integration protocols")
            raise
        else:
            pass
        finally:
            pass

    def generate_connectors(
        self, integration_specs: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate connector specifications for integrations.

        Args:
            integration_specs: Integration specifications

        Returns:
            List of connector specifications
        """
        self.logger.log_info("Generating connector specifications")
        prompt = f"\n        Integration Specifications: {json.dumps(integration_specs, indent=2)}\n\n        Generate connector specifications including:\n        1. External service connectors\n        2. Message queue connectors\n        3. Event stream connectors\n        4. Database connectors\n        5. Authentication connectors\n        6. Monitoring connectors\n        7. Error handling connectors\n        8. Retry and circuit breaker patterns\n        "
        try:
            response = self.client.responses.create(
                model="o3-mini",
                instructions="You are an expert connector designer. Generate comprehensive connector specifications in JSON format.",
                input=prompt,
                max_tokens=4000,
            )
            return json.loads(response.output[0].content[0].text)
        except Exception as e:
            self.logger.log_error(e, "Failed to generate connector specifications")
            raise
        else:
            pass
        finally:
            pass

    def validate_integrations(
        self, integration_specs: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate integration specifications for consistency and completeness.

        Args:
            integration_specs: Integration specifications to validate

        Returns:
            Dictionary containing validation results
        """
        self.logger.log_info("Validating integration specifications")
        prompt = f"\n        Integration Specifications: {json.dumps(integration_specs, indent=2)}\n\n        Validate integration specifications for:\n        1. Consistency across all integrations\n        2. Completeness of specifications\n        3. Security requirements\n        4. Performance considerations\n        5. Error handling patterns\n        6. Monitoring and observability\n        7. Scalability requirements\n        8. Compliance requirements\n        "
        try:
            response = self.client.responses.create(
                model="o3-mini",
                instructions="You are an expert integration validator. Generate comprehensive validation results in JSON format.",
                input=prompt,
                max_tokens=4000,
            )
            return json.loads(response.output[0].content[0].text)
        except Exception as e:
            self.logger.log_error(e, "Failed to validate integration specifications")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """Main entry point for the IntegrationSpecGenerator."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive integration specifications using O3 models"
    )
    parser.add_argument(
        "input_file",
        help="Input JSON/YAML file with integration specification requirements",
    )
    parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save generated integration specifications to files",
    )
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    try:
        generator = IntegrationSpecGenerator(args.config)
        with open(args.input_file) as f:
            input_data_dict = json.load(f)
        input_data = IntegrationSpecInput(**input_data_dict)
        output = generator.define_integrations(input_data)
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
