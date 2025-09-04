"""FastAPI webhook endpoints for CI/CD platform integration."""

import json
from typing import Any, Dict, Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from ..ingestion.adapters.cicd_adapter import CICDPlatform
from ..ingestion.webhook_processor import WebhookProcessor

logger = structlog.get_logger(__name__)

# Global webhook processor instance (will be injected via dependency)
webhook_processor: Optional[WebhookProcessor] = None


def get_webhook_processor() -> WebhookProcessor:
    """Dependency to get webhook processor instance."""
    if webhook_processor is None:
        raise HTTPException(status_code=503, detail="Webhook processor not initialized")
    return webhook_processor


def set_webhook_processor(processor: WebhookProcessor) -> None:
    """Set the global webhook processor instance."""
    global webhook_processor
    webhook_processor = processor


# Create webhook router
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.get("/health")
async def webhook_health(
    processor: WebhookProcessor = Depends(get_webhook_processor),
) -> Dict[str, Any]:
    """Get webhook processing health status."""
    return processor.get_health_status()


@webhook_router.get("/stats")
async def webhook_stats(
    hours: int = 24, processor: WebhookProcessor = Depends(get_webhook_processor)
) -> Dict[str, Any]:
    """Get webhook processing statistics."""
    return await processor.get_processing_stats(hours=hours)


# GitHub webhooks
@webhook_router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    processor: WebhookProcessor = Depends(get_webhook_processor),
):
    """Handle GitHub webhook events."""
    try:
        # Get request body and client IP
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "GitHub webhook received",
            event_type=x_github_event,
            repository=payload.get("repository", {}).get("full_name"),
            client_ip=client_ip,
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=x_github_event,
            payload=payload,
            signature=x_hub_signature_256,
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in GitHub webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"GitHub webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


# GitLab webhooks
@webhook_router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(..., alias="X-Gitlab-Event"),
    x_gitlab_token: Optional[str] = Header(None, alias="X-Gitlab-Token"),
    processor: WebhookProcessor = Depends(get_webhook_processor),
):
    """Handle GitLab webhook events."""
    try:
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "GitLab webhook received",
            event_type=x_gitlab_event,
            project=payload.get("project", {}).get("path_with_namespace"),
            client_ip=client_ip,
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=CICDPlatform.GITLAB_CI,
            event_type=x_gitlab_event,
            payload=payload,
            signature=x_gitlab_token,  # GitLab uses token instead of signature
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in GitLab webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"GitLab webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


# Jenkins webhooks
@webhook_router.post("/jenkins")
async def jenkins_webhook(
    request: Request, processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Handle Jenkins webhook events."""
    try:
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        # Jenkins doesn't have a standard event type header, derive from payload
        event_type = _derive_jenkins_event_type(payload)

        logger.info(
            "Jenkins webhook received",
            event_type=event_type,
            job_name=payload.get("job_name"),
            build_number=payload.get("build_number"),
            client_ip=client_ip,
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=CICDPlatform.JENKINS,
            event_type=event_type,
            payload=payload,
            signature=None,  # Jenkins typically doesn't use signatures
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Jenkins webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Jenkins webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


# Azure DevOps webhooks
@webhook_router.post("/azure")
async def azure_webhook(
    request: Request, processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Handle Azure DevOps webhook events."""
    try:
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        # Azure DevOps event type is in the payload
        event_type = payload.get("eventType", "unknown")

        logger.info(
            "Azure DevOps webhook received",
            event_type=event_type,
            resource_type=payload.get("resource", {}).get("resourceType"),
            project=payload.get("resourceContainers", {}).get("project", {}).get("id"),
            client_ip=client_ip,
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=CICDPlatform.AZURE_DEVOPS,
            event_type=event_type,
            payload=payload,
            signature=None,  # Azure DevOps can use basic auth instead
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Azure DevOps webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Azure DevOps webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


# CircleCI webhooks
@webhook_router.post("/circleci")
async def circleci_webhook(
    request: Request, processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Handle CircleCI webhook events."""
    try:
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        # CircleCI event type is typically in the payload type field
        event_type = payload.get("type", "workflow-completed")

        logger.info(
            "CircleCI webhook received",
            event_type=event_type,
            project=payload.get("project", {}).get("slug"),
            workflow_id=payload.get("workflow", {}).get("id"),
            client_ip=client_ip,
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=CICDPlatform.CIRCLECI,
            event_type=event_type,
            payload=payload,
            signature=None,  # CircleCI uses different auth methods
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in CircleCI webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"CircleCI webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


# Generic webhook endpoint for testing
@webhook_router.post("/test")
async def test_webhook(
    request: Request,
    platform: str,
    event_type: str,
    processor: WebhookProcessor = Depends(get_webhook_processor),
):
    """Test webhook endpoint for development and debugging."""
    try:
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}
        client_ip = request.client.host if request.client else "unknown"

        # Validate platform
        try:
            cicd_platform = CICDPlatform(platform.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {platform}. Supported: {[p.value for p in CICDPlatform]}",
            )

        logger.info(
            "Test webhook received",
            platform=platform,
            event_type=event_type,
            client_ip=client_ip,
            payload_keys=list(payload.keys()) if payload else [],
        )

        # Process webhook
        result = await processor.process_webhook(
            platform=cicd_platform,
            event_type=event_type,
            payload=payload,
            signature=None,
            source_ip=client_ip,
        )

        return JSONResponse(content=result, status_code=202)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in test webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Test webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


def _derive_jenkins_event_type(payload: Dict[str, Any]) -> str:
    """Derive Jenkins event type from payload."""
    # Jenkins payloads are highly customizable, so this is best effort

    if "build_status" in payload:
        build_status = payload["build_status"]
        if build_status in ["STARTED", "START"]:
            return "build_started"
        elif build_status in ["SUCCESS", "FAILURE", "ABORTED", "UNSTABLE", "COMPLETED"]:
            return "build_completed"

    if "phase" in payload:
        phase = payload["phase"].upper()
        if phase == "STARTED":
            return "build_started"
        elif phase in ["COMPLETED", "FINALIZED"]:
            return "build_completed"

    # Look for deployment indicators
    if any(key in payload for key in ["deployment_id", "deploy_url", "environment"]):
        return "deployment_completed"

    # Default fallback
    return "build_event"


# Event validation endpoints
@webhook_router.post("/validate/{platform}")
async def validate_webhook_payload(
    platform: str,
    request: Request,
    processor: WebhookProcessor = Depends(get_webhook_processor),
):
    """Validate a webhook payload without processing it."""
    try:
        # Validate platform
        try:
            cicd_platform = CICDPlatform(platform.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

        body = await request.body()
        payload = json.loads(body.decode()) if body else {}

        # Get adapter for validation
        adapter = processor.adapters.get(cicd_platform)
        if not adapter:
            raise HTTPException(
                status_code=503, detail=f"No adapter configured for {platform}"
            )

        # Perform validation (this would be extended with actual validation logic)
        validation_result = {
            "platform": platform,
            "valid": True,
            "payload_size": len(body),
            "payload_keys": list(payload.keys()) if payload else [],
            "validation_details": {
                "has_required_fields": _validate_required_fields(
                    cicd_platform, payload
                ),
                "timestamp_valid": _validate_timestamp_fields(payload),
                "structure_valid": True,  # Could be extended with JSON schema validation
            },
        }

        return JSONResponse(content=validation_result, status_code=200)

    except json.JSONDecodeError as e:
        return JSONResponse(
            content={
                "platform": platform,
                "valid": False,
                "error": f"Invalid JSON: {str(e)}",
            },
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Webhook validation error: {e}")
        return JSONResponse(
            content={
                "platform": platform,
                "valid": False,
                "error": f"Validation error: {str(e)}",
            },
            status_code=500,
        )


def _validate_required_fields(platform: CICDPlatform, payload: Dict[str, Any]) -> bool:
    """Validate required fields for platform."""
    if platform == CICDPlatform.GITHUB_ACTIONS:
        # GitHub webhook should have repository and action/workflow info
        return "repository" in payload and (
            "workflow_run" in payload
            or "workflow_job" in payload
            or "deployment" in payload
            or "check_run" in payload
        )
    elif platform == CICDPlatform.GITLAB_CI:
        # GitLab should have project and pipeline/build info
        return "project" in payload and (
            "pipeline" in payload or "build" in payload or "deployment" in payload
        )
    elif platform == CICDPlatform.JENKINS:
        # Jenkins should have basic build info
        return any(key in payload for key in ["job_name", "build_number", "build_url"])
    elif platform == CICDPlatform.AZURE_DEVOPS:
        # Azure DevOps should have resource and event type
        return "resource" in payload and "eventType" in payload

    return True  # Default to valid for unknown platforms


def _validate_timestamp_fields(payload: Dict[str, Any]) -> bool:
    """Validate timestamp fields in payload."""
    # This is a simplified validation - could be extended
    timestamp_fields = [
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "timestamp",
        "eventTime",
        "createdDate",
    ]

    # Look for timestamp fields in nested structures
    def find_timestamp_fields(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key in timestamp_fields:
                    # Could validate timestamp format here
                    pass
                elif isinstance(value, (dict, list)):
                    find_timestamp_fields(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_timestamp_fields(item, f"{path}[{i}]")

    find_timestamp_fields(payload)
    return True  # Simplified - always return True for now
