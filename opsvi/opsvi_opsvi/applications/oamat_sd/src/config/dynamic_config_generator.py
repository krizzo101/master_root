#!/usr/bin/env python3
"""
Dynamic Configuration Generator - Master Agent Implementation

The master agent that analyzes user requests and generates optimal runtime
configuration for the OAMAT Smart Decomposition system.

NO HARDCODED VALUES - All configuration is generated dynamically based on:
- Request complexity analysis
- Domain context understanding
- Resource requirement prediction
- Quality threshold optimization
"""

import json
from pathlib import Path
from typing import Any, Dict

from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)


async def generate_dynamic_config(
    user_request: str, debug: bool = False, standardized_request=None
) -> Dict[str, Any]:
    """
    Master Agent Dynamic Configuration Generation

    Analyzes user request and generates optimal runtime configuration
    using O3 reasoning without any hardcoded fallback values.
    """

    print("🔍 MASTER AGENT: Performing intelligent request analysis...")

    # Load the generation prompt and schema
    config_dir = Path(__file__).parent.parent.parent / "config"

    # Load master agent prompt
    prompt_path = config_dir / "dynamic_config_generation_prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Master agent prompt not found: {prompt_path}")

    with open(prompt_path) as f:
        generation_prompt = f.read()

    # Load configuration schema for validation
    schema_path = config_dir / "runtime_config_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Configuration schema not found: {schema_path}")

    with open(schema_path) as f:
        config_schema = json.load(f)

    # Enhanced prompt with standardized request context
    standardized_context_section = ""
    if standardized_request:
        standardized_context_section = f"""

## PREPROCESSED REQUEST ANALYSIS (Use for Enhanced Configuration)

**IMPORTANT**: The request has been intelligently preprocessed. Use this analysis for optimal configuration generation:

### CLASSIFICATION:
- **Request Type**: {standardized_request.classification.request_type.value}
- **Complexity Level**: {standardized_request.classification.complexity_level.value}
- **Platform Target**: {standardized_request.classification.platform_target.value}
- **Quality Level**: {standardized_request.classification.quality_level.value}
- **Estimated Effort**: {standardized_request.classification.estimated_effort}

### TECHNICAL REQUIREMENTS:
- **Languages**: {', '.join(standardized_request.technical_specification.programming_languages) if standardized_request.technical_specification.programming_languages else 'None specified'}
- **Frameworks**: {', '.join(standardized_request.technical_specification.frameworks) if standardized_request.technical_specification.frameworks else 'None specified'}
- **Platforms**: {', '.join(standardized_request.technical_specification.platforms) if standardized_request.technical_specification.platforms else 'None specified'}

### DELIVERABLES:
- **File Types**: {', '.join(standardized_request.deliverables.file_types) if standardized_request.deliverables.file_types else 'Standard files'}
- **Documentation**: {', '.join(standardized_request.deliverables.documentation_requirements) if standardized_request.deliverables.documentation_requirements else 'Basic documentation'}

### CONTEXT:
- **Complexity Assessment**: {standardized_request.classification.complexity_level.value} complexity requires {'high' if standardized_request.classification.complexity_level.value in ['complex', 'advanced'] else 'standard'} resource allocation
- **Quality Expectations**: {standardized_request.classification.quality_level.value} quality level
- **Confidence Level**: {standardized_request.confidence_scores.overall_confidence:.1f}/1.0

**CONFIGURATION OPTIMIZATION**: Use this detailed context to optimize timeouts, agent allocation, and quality thresholds for this specific request type and complexity.
"""

    # Prepare the master agent analysis prompt with schema awareness and enhanced context
    analysis_prompt = f"""
{generation_prompt}

## SCHEMA CONSTRAINTS TO FOLLOW:
{json.dumps(config_schema, indent=2)}
{standardized_context_section}

## USER REQUEST TO ANALYZE:
"{user_request}"

## YOUR TASK:
Analyze this specific user request and generate the complete JSON configuration that will enable optimal performance for this exact task.

Focus your analysis on:
1. **Complexity Level**: How complex is this request? (Simple/Moderate/Complex) {'[PREPROCESSED: ' + standardized_request.classification.complexity_level.value + ']' if standardized_request else ''}
2. **Domain Type**: What domain does this belong to? (Technical/Creative/Analytical) {'[PREPROCESSED: ' + standardized_request.classification.domain_category + ']' if standardized_request else ''}
3. **Resource Requirements**: How many agents and what timeouts are needed?
4. **Quality Standards**: What level of output quality is expected? {'[PREPROCESSED: ' + standardized_request.classification.quality_level.value + ']' if standardized_request else ''}

**CRITICAL**: Your generated JSON must validate against the schema above. Pay special attention to:
- Enum values (like reasoning_effort: "low"/"medium"/"high")
- Required fields and data types
- Value ranges and constraints

Generate the complete configuration JSON that matches the schema exactly.
Return ONLY the JSON configuration - no other text.
"""

    try:
        # Initialize structured output enforcer for O3 reasoning
        structured_enforcer = StructuredOutputEnforcer()

        if debug:
            print(
                "🔒 MASTER AGENT: Calling O3 reasoning model with STRUCTURED OUTPUT ENFORCEMENT..."
            )

        # O3 model configuration for structured output
        # Note: O3 models don't support temperature parameter
        model_config = {
            "model_name": "o3-mini",
            "reasoning_effort": "medium",
            "max_tokens": 16000,
        }

        # Call O3 with comprehensive structured output enforcement
        config_result = await structured_enforcer.enforce_dynamic_config(
            prompt=analysis_prompt,
            model_config=model_config,
            context={"user_request": user_request, "debug": debug},
        )

        # Configuration generation with structured output enforcement complete
        if debug:
            print(
                "📊 MASTER AGENT: Configuration generation complete with FULL VALIDATION!"
            )
            print(f"🔍 Generated config keys: {list(config_result.keys())}")

        # Use validated configuration directly (no parsing needed)
        dynamic_config_partial = config_result

        if debug:
            print(
                "✅ MASTER AGENT: Configuration validated against schema and business logic"
            )

        # Load base configuration and merge with O3 dynamic generation
        base_config_path = (
            Path(__file__).parent.parent.parent / "config" / "app_config.yaml"
        )
        with open(base_config_path) as f:
            import yaml

            base_config = yaml.safe_load(f)

        # Deep merge dynamic config into base config
        def deep_merge(base_dict, update_dict):
            """Deep merge update_dict into base_dict"""
            for key, value in update_dict.items():
                if (
                    key in base_dict
                    and isinstance(base_dict[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict

        # Create complete config by merging O3 dynamic portions with base
        complete_config = deep_merge(base_config, dynamic_config_partial)

        # Validate the complete merged configuration
        import jsonschema

        jsonschema.validate(instance=complete_config, schema=config_schema)

        if debug:
            print(
                "🧩 MASTER AGENT: Dynamic config successfully merged with base configuration"
            )
            _display_config_analysis(complete_config, user_request)

        return complete_config

    except Exception as e:
        print(f"❌ Dynamic configuration generation failed: {e}")
        if debug:
            print(f"🔄 Structured output enforcement error: {e}")

        # NO HARDCODED FALLBACKS - Fail fast as designed
        raise RuntimeError(
            f"Dynamic configuration generation failed: {e}. System cannot proceed without valid O3-generated configuration."
        )


def _display_config_analysis(config: Dict[str, Any], user_request: str):
    """Display the configuration analysis in a user-friendly way"""

    print("\n🎯 MASTER AGENT CONFIGURATION ANALYSIS:")
    print("=" * 50)

    # Extract key configuration decisions
    max_agents = config.get("execution", {}).get("max_parallel_agents", "unknown")
    timeout = config.get("execution", {}).get("agent_timeout_seconds", "unknown")

    # Determine complexity assessment from agent allocation
    if max_agents <= 3:
        complexity = "SIMPLE"
        emoji = "🟢"
    elif max_agents <= 6:
        complexity = "MODERATE"
        emoji = "🟡"
    else:
        complexity = "COMPLEX"
        emoji = "🔴"

    print(f"{emoji} COMPLEXITY ASSESSMENT: {complexity}")
    print(f"👥 AGENT ALLOCATION: {max_agents} parallel agents")
    print(f"⏱️  TIMEOUT CONFIGURATION: {timeout} seconds per agent")

    # Model configuration
    reasoning_tokens = (
        config.get("models", {}).get("reasoning", {}).get("max_tokens", "unknown")
    )
    agent_temp = config.get("models", {}).get("agent", {}).get("temperature", "N/A")
    reasoning_effort = (
        config.get("models", {}).get("reasoning", {}).get("reasoning_effort", "unknown")
    )

    print(
        f"🧠 REASONING MODEL: o3-mini with {reasoning_tokens} tokens (effort: {reasoning_effort})"
    )
    print(f"🤖 AGENT MODEL: gpt-4.1-mini (temperature: {agent_temp})")

    # Quality thresholds
    min_quality = config.get("quality", {}).get("minimum_confidence", "unknown")
    success_target = config.get("quality", {}).get("validation_enabled", "unknown")

    print(f"🎯 QUALITY TARGET: {min_quality}% sophistication minimum")
    print(
        f"✅ SUCCESS RATE: {success_target*100 if isinstance(success_target, float) else success_target}% target"
    )

    # Analysis rationale
    print("\n💡 OPTIMIZATION RATIONALE:")
    request_length = len(user_request)
    if request_length < 50:
        print("   • Short request → Focused resource allocation")
    elif request_length < 200:
        print("   • Medium request → Balanced configuration")
    else:
        print("   • Complex request → Enhanced resource allocation")

    # Domain indicators
    request_lower = user_request.lower()
    if any(word in request_lower for word in ["build", "create", "develop"]):
        print("   • Implementation focus → Higher quality standards")
    if any(word in request_lower for word in ["enterprise", "production", "system"]):
        print("   • Production system → Maximum quality/reliability")
    if any(word in request_lower for word in ["simple", "basic", "quick"]):
        print("   • Simple scope → Streamlined execution")
    if any(word in request_lower for word in ["api", "database", "integration"]):
        print("   • Technical complexity → Enhanced agent coordination")
