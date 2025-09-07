
# OpenAI API Standards 2025 Compliance Patch for Thinking Server
import os
import sys

# Add compliance path
sys.path.insert(0, "/home/opsvi/master_root/src")

try:
    from universal_openai_compliance import ensure_openai_compliance
    
    # Patch OpenAI model environment
    original_model = os.getenv("OPENAI_MODEL", "gpt-4")
    compliant_model = ensure_openai_compliance(
        model=original_model,
        context="thinking-server"
    )
    os.environ["OPENAI_MODEL"] = compliant_model
    
    print(f"🔐 Thinking server: {original_model} → {compliant_model}")
    
except Exception as e:
    print(f"❌ Thinking server compliance patch failed: {e}")
