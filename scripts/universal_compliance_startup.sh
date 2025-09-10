#!/bin/bash
# Universal OpenAI API Standards 2025 Compliance Startup Script

echo "🔐 Starting Universal OpenAI API Standards 2025 Compliance Enforcement"

# Set compliance environment variables
export OPENAI_COMPLIANCE_REQUIRED=true
export OPENAI_API_STANDARDS_2025=enforced

# Check and correct OPENAI_MODEL if needed
if [ ! -z "$OPENAI_MODEL" ]; then
    case "$OPENAI_MODEL" in
        "gpt-4"|"gpt-4o"|"gpt-4o-mini"|"gpt-3.5-turbo")
            echo "🚨 COMPLIANCE VIOLATION: Legacy model $OPENAI_MODEL detected"
            echo "🔧 CORRECTING: Setting OPENAI_MODEL to gpt-5-mini"
            export OPENAI_MODEL=gpt-5-mini
            ;;
        "gpt-5-nano"|"gpt-5-mini"|"gpt-5"|"o4-mini")
            echo "✅ Approved model: $OPENAI_MODEL"
            ;;
        *)
            echo "🚨 UNKNOWN MODEL: $OPENAI_MODEL"
            echo "🔧 DEFAULTING: Setting OPENAI_MODEL to gpt-5-mini"
            export OPENAI_MODEL=gpt-5-mini
            ;;
    esac
fi

# Add Python path for compliance
export PYTHONPATH="/home/opsvi/master_root/src:$PYTHONPATH"

echo "🔐 Universal OpenAI compliance enforcement active"

# Execute the original command
exec "$@"
