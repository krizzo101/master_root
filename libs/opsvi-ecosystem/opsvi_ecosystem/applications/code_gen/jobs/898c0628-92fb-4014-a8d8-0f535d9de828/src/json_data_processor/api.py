import logging
import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, Response
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import Optional
import tempfile

from .converter import validate_json_data, convert_json, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

app = FastAPI(title="JSON Data Processor for Multi-format Conversion")


class ConvertRequest(BaseModel):
    json_data: dict
    output_format: str


@app.post("/convert")
def convert_json_endpoint(request: ConvertRequest):
    """
    Accepts JSON directly in POST body, converts, and returns file contents.
    """
    json_data = validate_json_data(request.json_data)
    output_format = request.output_format.lower()
    if output_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400, detail=f"Unsupported output format: {output_format}"
        )

    converted = convert_json(json_data, output_format)
    filename = f"converted.{output_format}"

    if output_format == "xml":
        media_type = "application/xml"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif output_format == "csv":
        media_type = "text/csv"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif output_format == "yaml":
        media_type = "text/yaml"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        raise HTTPException(
            status_code=500, detail=f"Unexpected output format: {output_format}"
        )


@app.post("/upload")
def upload_and_convert(file: UploadFile = File(...), output_format: str = Form(...)):
    """
    Accepts a JSON file upload and converts it to the desired format. Returns result file.
    """
    logger.info(f"Received file: {file.filename} for conversion to {output_format}")

    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are supported.")

    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
    try:
        json_data = validate_json_data(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Uploaded file contains invalid JSON."
        )

    output_format = output_format.lower()
    if output_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400, detail=f"Unsupported output format: {output_format}"
        )
    converted = convert_json(json_data, output_format)
    filename = f"converted-{uuid.uuid4().hex[:8]}.{output_format}"

    if output_format == "xml":
        media_type = "application/xml"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif output_format == "csv":
        media_type = "text/csv"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif output_format == "yaml":
        media_type = "text/yaml"
        return Response(
            content=converted,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        raise HTTPException(
            status_code=500, detail=f"Unexpected output format: {output_format}"
        )


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}
