from __future__ import annotations
from prometheus_client import Counter, Gauge, Histogram

decision_success = Counter(
    "dk_strategy_success_total",
    "Successful tasks by strategy and model",
    ["strategy", "model"],
)

decision_failure = Counter(
    "dk_strategy_failure_total",
    "Failed tasks by strategy and model",
    ["strategy", "model"],
)

# Note: This metric is redefined below, removing duplicate
# verifier_disagreement = Counter(
#     "dk_verifier_disagreement_total",
#     "Verifier disagreed with solver",
#     ["model"],
# )

retrieval_latency = Histogram(
    "ro_retrieval_latency_ms",
    "Retrieval latency in ms",
    ["retriever"],
    buckets=(50, 100, 200, 400, 800, 1600, 3200, 6400),
)

evidence_coverage = Gauge(
    "evidence_coverage_ratio",
    "Supported evidence items per claim",
)

cost_per_pass_gate = Gauge(
    "cost_per_pass_gate_usd",
    "Estimated cost per passed quality gate",
    ["gate"],
)

# Evidence retrieval metrics
ro_evidence_retrieval_success_total = Counter(
    "ro_evidence_retrieval_success_total",
    "Successful evidence retrieval by source type",
    ["source_type"],
)

ro_evidence_retrieval_failure_total = Counter(
    "ro_evidence_retrieval_failure_total",
    "Failed evidence retrieval by source type",
    ["source_type"],
)

# Verification metrics
dk_verification_duration_ms = Histogram(
    "dk_verification_duration_ms",
    "Verification duration in milliseconds",
    buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000],
)

dk_verification_success_total = Counter(
    "dk_verification_success_total",
    "Successful verifications",
)

dk_verification_failure_total = Counter(
    "dk_verification_failure_total",
    "Failed verifications",
)

dk_verifier_disagreement_total = Counter(
    "dk_verifier_disagreement_total",
    "Verifier model disagreements",
)

# Context pack assembly metrics
ro_context_pack_size_chars = Gauge(
    "ro_context_pack_size_chars",
    "Context pack size in characters",
    ["pack_type"],
)

ro_context_pack_assembly_duration_ms = Histogram(
    "ro_context_pack_assembly_duration_ms",
    "Context pack assembly duration in milliseconds",
    ["pack_type"],
    buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000],
)

# Quality gate metrics
quality_gate_passed_total = Counter(
    "quality_gate_passed_total",
    "Quality gates passed by gate name",
    ["gate_name"],
)

quality_gate_failed_total = Counter(
    "quality_gate_failed_total",
    "Quality gates failed by gate name",
    ["gate_name"],
)

quality_gate_repair_attempts_total = Counter(
    "quality_gate_repair_attempts_total",
    "Quality gate repair attempts by gate name",
    ["gate_name"],
)

quality_gate_repair_success_total = Counter(
    "quality_gate_repair_success_total",
    "Successful quality gate repairs by gate name",
    ["gate_name"],
)

quality_gate_repair_failure_total = Counter(
    "quality_gate_repair_failure_total",
    "Failed quality gate repairs by gate name",
    ["gate_name"],
)

# Auto-repair metrics
auto_repair_attempts_total = Counter(
    "auto_repair_attempts_total",
    "Auto-repair attempts by type",
    ["repair_type"],
)

auto_repair_success_total = Counter(
    "auto_repair_success_total",
    "Successful auto-repairs by type",
    ["repair_type"],
)

auto_repair_failure_total = Counter(
    "auto_repair_failure_total",
    "Failed auto-repairs by type",
    ["repair_type"],
)

# DSL metrics
dsl_config_loaded_total = Counter(
    "dsl_config_loaded_total",
    "DSL configuration loads",
)

dsl_knobs_applied_total = Counter(
    "dsl_knobs_applied_total",
    "DSL knobs applied by knob type",
    ["knob_type"],
)

# Router escalation metrics
router_escalations_total = Counter(
    "router_escalations_total",
    "Router escalations by from/to model",
    ["from_model", "to_model"],
)

# Decision confidence metrics
dk_decision_confidence_bucket = Histogram(
    "dk_decision_confidence_bucket",
    "Decision confidence distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
