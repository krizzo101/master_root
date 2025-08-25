#!/bin/bash
# Configure Claude Code tokens for the monitoring system
# This script sets up the 3 tokens provided by the user

echo "========================================"
echo "CLAUDE CODE TOKEN CONFIGURATION"
echo "========================================"

# Create secure directory for token storage
TOKEN_DIR="$HOME/.claude"
mkdir -p "$TOKEN_DIR"
chmod 700 "$TOKEN_DIR"

# Create environment file for tokens
ENV_FILE="$TOKEN_DIR/tokens.env"

# Write tokens to environment file (keeping them secure)
cat > "$ENV_FILE" << 'EOF'
# Claude Code Token Pool Configuration
# These tokens are used for parallel agent execution

# Token 1
export CLAUDE_CODE_TOKEN1='token1_placeholder'

# Token 2  
export CLAUDE_CODE_TOKEN2='token2_placeholder'

# Token 3
export CLAUDE_CODE_TOKEN3='token3_placeholder'

# Primary token (uses first token as fallback)
export CLAUDE_CODE_TOKEN='${CLAUDE_CODE_TOKEN1}'

# Ensure ANTHROPIC_API_KEY is not set (conflicts with Claude Code)
unset ANTHROPIC_API_KEY
EOF

# Set restrictive permissions
chmod 600 "$ENV_FILE"

echo "✅ Token configuration created at: $ENV_FILE"
echo ""
echo "To use the tokens:"
echo "  1. Edit $ENV_FILE and replace placeholders with actual tokens"
echo "  2. Source the file: source $ENV_FILE"
echo "  3. Run the token pool test: python setup_token_pool.py"
echo ""
echo "Security notes:"
echo "  - The tokens.env file has restrictive permissions (600)"
echo "  - Never commit this file to version control"
echo "  - Tokens are automatically rotated for parallel execution"
echo "  - ANTHROPIC_API_KEY is automatically removed to avoid conflicts"

# Create Python test script
cat > test_token_pool.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code.token_pool import token_pool_manager

# Check tokens
status = token_pool_manager.get_pool_status()
print(f"Tokens available: {status['token_count']}")

if status['token_count'] > 0:
    print("\n✅ Token pool is ready!")
    print("You can now run parallel Claude agents with automatic token rotation.")
else:
    print("\n⚠️ No tokens found. Please:")
    print("1. Edit ~/.claude/tokens.env")
    print("2. Add your tokens")
    print("3. Run: source ~/.claude/tokens.env")
    print("4. Run this test again")
EOF

chmod +x test_token_pool.py

echo ""
echo "Quick test command:"
echo "  ./test_token_pool.py"