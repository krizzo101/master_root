"""
Input Parser & Validator for workloads JSON schema
"""
import json
from pathlib import Path
from typing import Any

import jsonschema
from loguru import logger
from pydantic import BaseModel, Field, ValidationError, constr, validator

WORKLOAD_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string", "pattern": "^1\\.0$"},
        "workloads": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "tasks"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["agent", "type", "input"],
                            "properties": {
                                "agent": {"type": "string", "minLength": 1},
                                "type": {"type": "string", "minLength": 1},
                                "input": {"type": "object"},
                                "depends_on": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "additionalProperties": False,
                        },
                        "minItems": 1,
                    },
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
    },
    "required": ["version", "workloads"],
    "additionalProperties": False,
}


class TaskModel(BaseModel):
    agent: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    input: dict[str, Any]
    depends_on: list[str] = Field(default_factory=list)


class WorkloadModel(BaseModel):
    name: str
    description: str = ""
    tasks: list[TaskModel]


class InputModel(BaseModel):
    version: constr(regex=r"^1\.0$")
    workloads: list[WorkloadModel]

    @validator("workloads")
    def must_have_tasks(cls, workloads):
        for w in workloads:
            if not w.tasks:
                raise ValueError(f"Workload {w.name} must have at least one task.")
        return workloads


def parse_and_validate_input(input_file: Path) -> InputModel:
    """
    Loads and validates the user input JSON file.
    Returns an InputModel instance.
    Raises ValueError on schema or validation errors.
    """
    try:
        with open(input_file, encoding="utf-8") as f:
            input_data = json.load(f)
        jsonschema.validate(instance=input_data, schema=WORKLOAD_JSON_SCHEMA)
        validated = InputModel.parse_obj(input_data)
        logger.info(f"Input file '{input_file}' is valid and loaded.")
        return validated
    except (jsonschema.exceptions.ValidationError, ValidationError) as exc:
        logger.opt(exception=exc).error(f"Schema or model validation failed: {exc}")
        raise ValueError(f"Input file schema or model validation failed: {exc}")
    except Exception as exc:
        logger.opt(exception=exc).error(f"Failed to parse input JSON file: {exc}")
        raise ValueError(f"Failed to parse input file: {exc}")
