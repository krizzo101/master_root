"""
Database Schema Generator - AI-powered database schema generation using OpenAI's O3 models.

This module defines DatabaseSchemaGenerator, which generates comprehensive database schemas
including table definitions, relationships, indexes, constraints, and migration scripts
using OpenAI's O3 and O3-mini models.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.prompts.technical_spec_prompts import (
    DATABASE_SCHEMA_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.technical_spec_schemas import (
    DatabaseSchemaInput,
    DatabaseSpecOutput,
    OutputFormat,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class DatabaseSchemaGenerator:
    """
    Generates database schemas based on provided configurations and manages schema-related operations.

    Attributes:
        logger: O3Logger instance for logging.
        config_manager: ConfigManager for loading configurations.
        client: OpenAI client for API calls.
        directory_manager: DirectoryManager for filesystem operations.
        file_generator: FileGenerator for writing files.
        input_loader: UniversalInputLoader for loading input data.
        output_formatter: OutputFormatter for formatting outputs.
        prompt_builder: PromptBuilder for building prompts.
    """

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the DatabaseSchemaGenerator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.logger = get_logger()
        self.logger.log_info("Initializing DatabaseSchemaGenerator")
        self.config_manager = ConfigManager(config_path)
        api_cfg = self.config_manager.get_api_config()
        self.client = OpenAI(api_key=api_cfg.api_key or "", base_url=api_cfg.base_url)
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()
        self.input_loader = UniversalInputLoader()
        self.output_formatter = OutputFormatter()
        self.prompt_builder = PromptBuilder()
        self._create_directories()
        self.logger.log_info("DatabaseSchemaGenerator initialization complete")

    def _create_directories(self) -> None:
        """
        Create necessary directories for output and logs.
        """
        try:
            dirs: list[Path] = [
                Path("generated_files/technical_specs/database_schemas"),
                Path("logs"),
                Path("config"),
                Path("schemas"),
                Path("prompts"),
            ]
            for directory in dirs:
                self.directory_manager.ensure_directory_exists(directory)
                self.logger.log_debug(f"Directory created/verified: {directory}")
            else:
                pass
        except Exception as e:
            self.logger.log_error(e, "Failed to create necessary directories")
            raise
        else:
            pass
        finally:
            pass

    def generate_schema(self, input_data: DatabaseSchemaInput) -> DatabaseSpecOutput:
        """
        Generate comprehensive database schema.

        Args:
            input_data: Input data for database schema generation.

        Returns:
            DatabaseSpecOutput containing generated database schema.
        """
        start = time.time()
        try:
            self.logger.log_info("Starting database schema generation")
            self.logger.log_debug(f"Input data: {input_data}")
            prompt = self._build_prompt(input_data)
            self.logger.log_debug(f"Built prompt of length {len(prompt)}")
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {"role": "system", "content": DATABASE_SCHEMA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw_text = response.choices[0].message.content
            try:
                schema_dict: dict[str, Any] = json.loads(raw_text)
            except json.JSONDecodeError as e:
                self.logger.log_error(e, "Failed to parse model response as JSON")
                raise ValueError(f"Invalid JSON response: {e}") from e
            else:
                pass
            finally:
                pass
            base_name = f"database_schema_{int(time.time())}"
            files = self._save_schema_files(
                schema_dict["database_schemas"], input_data.output_format, base_name
            )
            out = DatabaseSpecOutput(
                schema_definition=schema_dict["database_schemas"]["schema_definition"],
                table_definitions=schema_dict["database_schemas"]["table_definitions"],
                relationships=schema_dict["database_schemas"]["relationships"],
                indexes=schema_dict["database_schemas"]["indexes"],
                constraints=schema_dict["database_schemas"]["constraints"],
                migration_scripts=schema_dict["database_schemas"]["migration_scripts"],
                data_validation_rules=schema_dict["database_schemas"][
                    "data_validation_rules"
                ],
            )
            elapsed = time.time() - start
            self.logger.log_info(f"Completed in {elapsed:.2f}s, files: {files}")
            return out
        except Exception as e:
            self.logger.log_error(e, "Database schema generation failed")
            raise
        else:
            pass
        finally:
            pass

    def _build_prompt(self, input_data: DatabaseSchemaInput) -> str:
        """
        Build the prompt for O3 model based on input data.

        Args:
            input_data: Input data for database schema generation.

        Returns:
            Formatted prompt string.
        """
        analysis_data: dict[str, Any] = {
            "data_models": input_data.data_models,
            "requirements": input_data.requirements,
            "include_migrations": input_data.include_migrations,
            "include_indexes": input_data.include_indexes,
        }
        return self.prompt_builder.build_analysis_prompt(
            input_data=input_data,
            analysis_data=analysis_data,
            system_prompt=DATABASE_SCHEMA_SYSTEM_PROMPT,
        )

    def _save_schema_files(
        self, schema: dict[str, Any], fmt: OutputFormat, base_name: str
    ) -> list[str]:
        """
        Save database schema files in the specified format.

        Args:
            schema: The database schema data to save.
            fmt: The format to save in.
            base_name: Base filename for the output.

        Returns:
            List of generated file paths.
        """
        out_dir = Path("generated_files/technical_specs/database_schemas")
        self.directory_manager.ensure_directory_exists(out_dir)
        files: list[str] = []
        try:
            if fmt == OutputFormat.SQL:
                content = self._convert_to_sql(schema)
                file_path = out_dir / f"{base_name}.sql"
                self.file_generator.save_file(content, file_path)
                files.append(str(file_path))
            elif fmt == OutputFormat.JSON:
                content = self.output_formatter.to_json(schema, pretty=True)
                file_path = out_dir / f"{base_name}.json"
                self.file_generator.save_file(content, file_path)
                files.append(str(file_path))
            elif fmt == OutputFormat.MARKDOWN:
                content = self.output_formatter.to_markdown(
                    schema, title="Database Schema"
                )
                file_path = out_dir / f"{base_name}.md"
                self.file_generator.save_file(content, file_path)
                files.append(str(file_path))
            elif fmt == OutputFormat.YAML:
                content = self.output_formatter.to_yaml(schema)
                file_path = out_dir / f"{base_name}.yaml"
                self.file_generator.save_file(content, file_path)
                files.append(str(file_path))
            else:
                pass
            self.logger.log_info(f"Saved schema files: {files}")
            return files
        except Exception as e:
            self.logger.log_error(e, f"Failed to save schema files in {fmt} format")
            raise
        else:
            pass
        finally:
            pass

    def _convert_to_sql(self, schema: dict[str, Any]) -> str:
        """
        Convert database schema to SQL format.

        Args:
            schema: Database schema dictionary.

        Returns:
            SQL string.
        """
        try:
            lines: list[str] = []
            sd = schema.get("schema_definition", {})
            dbn = sd.get("database_name", "app_database")
            ver = sd.get("version", "1.0.0")
            desc = sd.get("description", "")
            lines.extend(
                [
                    f"-- Database: {dbn} v{ver}",
                    f"-- {desc}",
                    "",
                    f"CREATE DATABASE IF NOT EXISTS {dbn};",
                    f"USE {dbn};",
                    "",
                ]
            )
            for tbl in schema.get("table_definitions", []):
                lines.append(f"-- Table: {tbl.get('table_name', '')}")
                lines.append(f"CREATE TABLE {tbl.get('table_name', '')} (")
                cols: list[str] = []
                for c in tbl.get("columns", []):
                    column_def = f"    {c.get('name', '')} {c.get('type', '')}"
                    if c.get("not_null"):
                        column_def += " NOT NULL"
                    else:
                        pass
                    if c.get("default"):
                        column_def += f" DEFAULT {c.get('default')}"
                    else:
                        pass
                    if c.get("auto_increment"):
                        column_def += " AUTO_INCREMENT"
                    else:
                        pass
                    cols.append(column_def)
                else:
                    pass
                if tbl.get("primary_key"):
                    cols.append(f"    PRIMARY KEY ({tbl['primary_key']})")
                else:
                    pass
                lines.append(",\n".join(cols))
                lines.extend([");", ""])
            else:
                pass
            return "\n".join(lines)
        except Exception as e:
            self.logger.log_error(e, "Failed to convert schema to SQL")
            raise
        else:
            pass
        finally:
            pass

    def define_tables(self, data_models: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Define database tables based on data models.

        Args:
            data_models: Data models dictionary.

        Returns:
            List of table definitions.
        """
        self.logger.log_info("Defining database tables")
        prompt = self.prompt_builder.build_generation_prompt(
            input_data=None,
            context={"data_models": data_models},
            system_prompt="You are an expert database designer.",
            format_instructions="Return JSON array of table definitions.",
        )
        try:
            resp = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert database designer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            self.logger.log_error(e, "Failed to define tables")
            raise
        else:
            pass
        finally:
            pass

    def specify_relationships(
        self, tables: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Specify relationships between database tables.

        Args:
            tables: List of table definitions.

        Returns:
            List of relationship specifications.
        """
        self.logger.log_info("Specifying relationships")
        prompt = self.prompt_builder.build_generation_prompt(
            input_data=None,
            context={"tables": tables},
            system_prompt="You are an expert database relationship designer.",
            format_instructions="Return JSON array of relationships.",
        )
        try:
            resp = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert database relationship designer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            self.logger.log_error(e, "Failed to specify relationships")
            raise
        else:
            pass
        finally:
            pass

    def generate_migrations(self, schema: dict[str, Any]) -> list[str]:
        """
        Generate database migration scripts.

        Args:
            schema: Database schema dictionary.

        Returns:
            List of migration scripts.
        """
        self.logger.log_info("Generating migrations")
        prompt = self.prompt_builder.build_generation_prompt(
            input_data=None,
            context={"schema": schema},
            system_prompt="You are an expert database migration specialist.",
            format_instructions="Return SQL migration scripts separated by newlines.",
        )
        try:
            resp = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert database migration specialist.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
            )
            text = resp.choices[0].message.content
            return text.splitlines()
        except Exception as e:
            self.logger.log_error(e, "Failed to generate migrations")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """
    Main entry point for the DatabaseSchemaGenerator.
    """
    logger = get_logger()
    parser = argparse.ArgumentParser(
        description="Generate comprehensive database schemas using O3 models"
    )
    parser.add_argument(
        "input_file", help="Input JSON/YAML file with database schema requirements"
    )
    parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save generated database schemas to files",
    )
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    try:
        loader = UniversalInputLoader()
        data = loader.load_file_by_extension(Path(args.input_file))
        input_obj = DatabaseSchemaInput(**data)
        generator = DatabaseSchemaGenerator(args.config)
        output = generator.generate_schema(input_obj)
        logger.log_info(
            "Schema generation completed",
            {
                "tables": len(output.table_definitions),
                "relationships": len(output.relationships),
                "indexes": len(output.indexes),
                "constraints": len(output.constraints),
                "migrations": len(output.migration_scripts),
            },
        )
        if args.save_file:
            logger.log_info(
                "Schemas saved to generated_files/technical_specs/database_schemas"
            )
        else:
            pass
    except Exception as e:
        logger.log_error(e, "Fatal error in main")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
