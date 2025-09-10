# lightweight plugin-style validators for agent stdout
import json
import os
import re
from typing import Any, Dict, Optional, Tuple


class ValidationError(Exception):
    def __init__(self, code: str, detail: str, raw: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.raw = code, detail, raw


class BaseValidator:
    name = "base"

    def validate(self, stdout_text: str, task: Any) -> Dict[str, Any]:
        return {"status": "pass", "payload": {"raw_text": stdout_text}}


class StripFences(BaseValidator):
    name = "strip_fences"

    def validate(self, stdout_text: str, task: Any) -> Dict[str, Any]:
        if os.getenv("UNIFIED_STRIP_FENCES", "0") != "1":
            return {"status": "pass", "payload": {"raw_text": stdout_text}}
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", stdout_text, re.S | re.I)
        if m:
            stdout_text = m.group(1).strip()
        return {"status": "pass", "payload": {"raw_text": stdout_text}}


class JsonParse(BaseValidator):
    name = "json_parse"

    def validate(self, stdout_text: str, task: Any) -> Dict[str, Any]:
        try:
            obj = json.loads(stdout_text)
            return {"status": "pass", "payload": obj}
        except Exception as e:
            if os.getenv("UNIFIED_REQUIRE_JSON", "0") == "1":
                raise ValidationError("json_parse_failed", str(e)[:200], stdout_text)
            return {
                "status": "pass",
                "payload": {"status": "completed", "raw_text": stdout_text},
            }


# Optional, plug in JSON Schema when desired
try:
    import jsonschema

    class JsonSchema(BaseValidator):
        name = "json_schema"

        def validate(self, stdout_text: str, task: Any) -> Dict[str, Any]:
            if os.getenv("UNIFIED_VALIDATE_SCHEMA", "0") != "1":
                return {"status": "pass", "payload": json.loads(stdout_text)}
            schema = {
                "type": "object",
                "properties": {
                    "status": {"const": "completed"},
                    "task_id": {"type": "string"},
                },
                "required": ["status"],
                "additionalProperties": True,
            }
            obj = json.loads(stdout_text)
            jsonschema.validate(obj, schema)
            if "task_id" in obj and obj["task_id"] != getattr(
                task, "task_id", obj["task_id"]
            ):
                raise ValidationError(
                    "schema_task_id_mismatch",
                    "task_id differs from task.task_id",
                    stdout_text,
                )
            return {"status": "pass", "payload": obj}

except Exception:
    JsonSchema = None


def default_chain():
    chain = [StripFences(), JsonParse()]
    if JsonSchema:
        chain.append(JsonSchema())
    return chain
