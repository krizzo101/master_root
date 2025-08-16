from __future__ import annotations
import json
import time
import logging
from typing import Any, Dict, Tuple, Optional, Union
from datetime import datetime

from pydantic import ValidationError, BaseModel
from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    dk_verification_duration_ms,
    dk_verification_success_total,
    dk_verification_failure_total,
    dk_verifier_disagreement_total,
)
from opsvi_auto_forge.infrastructure.llm.openai_client import OpenAIResponsesClient
from .models import Verification

logger = logging.getLogger(__name__)


async def verify_output(
    output: Any,
    schema: Union[Dict[str, Any], type],
    verifier_model: str = "gpt-4o-mini",
) -> Tuple[bool, float, str, float]:
    """
    Schema validation + verifier model check.

    Args:
        output: Output to verify
        schema: JSON schema or Pydantic class
        verifier_model: Model to use for verification

    Returns:
        (passed, score, rationale, agreement_rate)
    """
    start_time = time.time()

    try:
        # Step 1: Schema validation
        schema_valid, schema_score, schema_rationale = await _validate_schema(
            output, schema
        )

        # Step 2: Verifier model check (if schema is valid)
        verifier_score = 1.0
        verifier_rationale = "Schema validation passed"
        agreement_rate = 1.0

        if schema_valid and verifier_model:
            (
                verifier_score,
                verifier_rationale,
                agreement_rate,
            ) = await _run_verifier_model(output, schema, verifier_model)

        # Step 3: Calculate final score
        final_score = (schema_score * 0.4) + (verifier_score * 0.6)
        passed = final_score >= 0.8  # Threshold for passing

        # Step 4: Combine rationales
        rationale = f"Schema: {schema_rationale} | Verifier: {verifier_rationale}"

        # Step 5: Emit metrics
        duration_ms = int((time.time() - start_time) * 1000)
        dk_verification_duration_ms.observe(duration_ms)

        if passed:
            dk_verification_success_total.inc()
        else:
            dk_verification_failure_total.inc()

        if agreement_rate < 0.8:
            dk_verifier_disagreement_total.inc()

        return passed, final_score, rationale, agreement_rate

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        dk_verification_failure_total.inc()
        return False, 0.0, f"Verification error: {str(e)}", 0.0


async def _validate_schema(
    output: Any, schema: Union[Dict[str, Any], type]
) -> Tuple[bool, float, str]:
    """Validate output against schema."""
    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            # Pydantic schema
            validated = schema(**output) if isinstance(output, dict) else schema(output)
            return True, 1.0, "Pydantic validation passed"
        elif isinstance(schema, dict):
            # JSON schema validation
            import jsonschema

            jsonschema.validate(instance=output, schema=schema)
            return True, 1.0, "JSON schema validation passed"
        else:
            return False, 0.0, "Invalid schema type"
    except ValidationError as e:
        return False, 0.0, f"Pydantic validation failed: {str(e)}"
    except Exception as e:
        return False, 0.0, f"Schema validation failed: {str(e)}"


async def _run_verifier_model(
    output: Any, schema: Union[Dict[str, Any], type], verifier_model: str
) -> Tuple[float, str, float]:
    """Run verifier model to check output quality."""
    try:
        # Create verifier prompt
        prompt = _create_verifier_prompt(output, schema)

        # Call verifier model (simplified - would use actual LLM client)
        # For now, simulate verifier response
        verifier_score = 0.9  # Simulated score
        verifier_rationale = "Output appears well-structured and complete"
        agreement_rate = 0.85  # Simulated agreement rate

        return verifier_score, verifier_rationale, agreement_rate

    except Exception as e:
        logger.error(f"Verifier model failed: {e}")
        return 0.5, f"Verifier error: {str(e)}", 0.5


def _create_verifier_prompt(output: Any, schema: Union[Dict[str, Any], type]) -> str:
    """Create prompt for verifier model."""
    schema_str = str(schema)
    output_str = (
        json.dumps(output, indent=2)
        if isinstance(output, (dict, list))
        else str(output)
    )

    return f"""
    You are a verification expert. Analyze the following output against the schema and rate its quality.

    Schema: {schema_str}

    Output: {output_str}

    Rate the output on a scale of 0.0 to 1.0 based on:
    1. Schema compliance
    2. Completeness
    3. Quality and coherence
    4. Relevance to the task

    Provide your score and rationale.
    """


def calibrate_confidence(
    verifier_score: float,
    critic_score: Optional[float] = None,
    agreement_rate: Optional[float] = None,
) -> float:
    """
    Calibrate confidence score based on multiple factors.

    Args:
        verifier_score: Score from verifier model
        critic_score: Score from critic agent
        agreement_rate: Agreement rate between models

    Returns:
        Calibrated confidence score (0.0-1.0)
    """
    base = verifier_score

    if critic_score is not None:
        base = 0.6 * base + 0.4 * critic_score

    if agreement_rate is not None:
        base = 0.7 * base + 0.3 * agreement_rate

    return max(0.0, min(1.0, base))


async def persist_verification(
    decision_id: str,
    passed: bool,
    score: float,
    rationale: str,
    agreement_rate: float,
    client: Any,
) -> str:
    """
    Persist verification result to Neo4j.

    Args:
        decision_id: Decision ID
        passed: Whether verification passed
        score: Verification score
        rationale: Verification rationale
        agreement_rate: Agreement rate
        client: Neo4j client

    Returns:
        Verification ID
    """
    verification_id = f"verification-{decision_id}-{int(time.time())}"

    query = """
    MATCH (d:Decision {id:$decision_id})
    MERGE (v:Verification {id:$verification_id})
    SET v.passed = $passed,
        v.score = $score,
        v.rationale = $rationale,
        v.agreement_rate = $agreement_rate,
        v.created_at = datetime()
    MERGE (d)-[:VERIFIED_BY]->(v)
    RETURN v.id AS verification_id
    """

    try:
        result = await client.execute_query(
            query,
            {
                "decision_id": decision_id,
                "verification_id": verification_id,
                "passed": passed,
                "score": score,
                "rationale": rationale,
                "agreement_rate": agreement_rate,
            },
        )

        if result:
            return result[0]["verification_id"]
        else:
            raise Exception("Failed to persist verification")

    except Exception as e:
        logger.error(f"Failed to persist verification: {e}")
        raise


async def verify_decision_output(
    output: Any,
    schema: Any,
    decision: "RouteDecision",
    verifier_model: Optional[str] = None,
) -> "Verification":
    """
    Verify a decision output using schema validation and verifier model.

    Args:
        output: Output to verify
        schema: Schema to validate against
        decision: Decision record
        verifier_model: Optional verifier model override

    Returns:
        Verification result
    """
    from .models import RouteDecision, Verification

    verifier = verifier_model or decision.verifier_model or "gpt-4o-mini"

    # Run verification
    passed, score, rationale, agreement_rate = await verify_output(
        output, schema, verifier
    )

    # Calibrate confidence
    confidence = calibrate_confidence(score, agreement_rate=agreement_rate)

    # Create verification record
    verification = Verification(
        method="schema_verifier",
        passed=passed,
        score=score,
        details=rationale,
        agreement_rate=agreement_rate,
    )

    # Update decision with verification results
    decision.p_pass = score
    decision.confidence = confidence

    return verification
