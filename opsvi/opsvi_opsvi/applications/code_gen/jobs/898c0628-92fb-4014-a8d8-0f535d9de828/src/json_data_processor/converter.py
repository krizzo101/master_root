import json
import logging
from typing import Any, Dict, Union
from pathlib import Path

import pandas as pd
import numpy as np
from fastapi import HTTPException
import dicttoxml
import yaml

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"xml", "csv", "yaml"}


def validate_json_data(data: Union[str, dict]) -> dict:
    """
    Validates that the provided data is valid JSON and returns it as a dict.
    Raises HTTPException if invalid.
    """
    try:
        if isinstance(data, str):
            parsed = json.loads(data)
        elif isinstance(data, dict):
            parsed = data
        else:
            raise ValueError("Provided data is neither string nor dict.")
        return parsed
    except Exception as e:
        logger.error(f"Invalid JSON input: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON input. Please upload a valid JSON file.",
        )


def json_to_xml(json_data: dict) -> bytes:
    """
    Converts JSON data to XML bytes.
    """
    try:
        xml_bytes = dicttoxml.dicttoxml(json_data, custom_root="root", attr_type=False)
        return xml_bytes
    except Exception as e:
        logger.error(f"JSON to XML conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Could not convert JSON to XML.")


def _normalize_json(json_data: Any) -> pd.DataFrame:
    """
    Normalizes JSON data for tabular output (CSV). Handles list/dict at root.
    """
    try:
        if isinstance(json_data, list):
            df = pd.json_normalize(json_data)
        elif isinstance(json_data, dict):
            # Try normalizing values if the root is a dict of lists
            for v in json_data.values():
                if isinstance(v, list):
                    df = pd.json_normalize(v)
                    break
            else:
                df = pd.json_normalize([json_data])
        else:
            raise ValueError("Data is not a JSON object or array.")
        return df
    except Exception as e:
        logger.error(f"Failed to normalize JSON for CSV: {e}")
        raise HTTPException(
            status_code=500, detail="JSON structure not supported for CSV."
        )


def json_to_csv(json_data: dict) -> str:
    """
    Converts JSON data to CSV string.
    """
    try:
        df = _normalize_json(json_data)
        # Replace NaN with empty strings
        df = df.replace({np.nan: ""})
        csv_str = df.to_csv(index=False, encoding="utf-8")
        return csv_str
    except Exception as e:
        logger.error(f"JSON to CSV conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Could not convert JSON to CSV.")


def json_to_yaml(json_data: dict) -> str:
    """
    Converts JSON data to YAML string.
    """
    try:
        yaml_str = yaml.safe_dump(json_data, allow_unicode=True, sort_keys=False)
        return yaml_str
    except Exception as e:
        logger.error(f"JSON to YAML conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Could not convert JSON to YAML.")


def convert_json(json_data: dict, output_format: str) -> Union[bytes, str]:
    """
    Convert JSON data to the specified output format.
    """
    fmt = output_format.lower()
    if fmt not in SUPPORTED_FORMATS:
        logger.error(f"Unsupported output format: {fmt}")
        raise HTTPException(status_code=400, detail=f"Unsupported output format: {fmt}")
    if fmt == "xml":
        return json_to_xml(json_data)
    elif fmt == "csv":
        return json_to_csv(json_data)
    elif fmt == "yaml":
        return json_to_yaml(json_data)
    else:
        # Should not reach here
        logger.error(f"Unhandled output format: {fmt}")
        raise HTTPException(status_code=500, detail=f"Unhandled output format: {fmt}")
