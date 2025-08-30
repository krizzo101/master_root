#!/bin/bash
# Setup script for Claude Code Hook Pack

echo "Claude Code Hook Pack Setup"
echo "==========================="
echo

# Check if .env exists
if [ ! -f "$HOME/master_root/.env" ]; then
    echo "Warning: .env file not found at $HOME/master_root/.env"
    echo "Creating from .env.example..."
    cp "$HOME/master_root/.env.example" "$HOME/master_root/.env"
fi

# Check for OPENAI_API_KEY
if grep -q "OPENAI_API_KEY" "$HOME/master_root/.env"; then
    echo "✓ OPENAI_API_KEY found in .env"
else
    echo "✗ OPENAI_API_KEY not found in .env"
    echo "  Please add: OPENAI_API_KEY=your_key_here"
fi

# Check if hook pack config is already added
if grep -q "KNOWLEDGE_CUTOFF" "$HOME/master_root/.env"; then
    echo "✓ Hook pack configuration already in .env"
else
    echo "Adding hook pack configuration to .env..."
    echo "" >> "$HOME/master_root/.env"
    cat "$HOME/master_root/hook_pack_config.txt" >> "$HOME/master_root/.env"
    echo "✓ Hook pack configuration added"
fi

# Verify Python dependencies
echo
echo "Checking Python dependencies..."
if python3 -c "import openai" 2>/dev/null; then
    echo "✓ OpenAI package installed"
else
    echo "Installing OpenAI package..."
    pip install -q openai>=1.40.0
    echo "✓ OpenAI package installed"
fi

# Make hooks executable
echo
echo "Setting hook permissions..."
chmod +x "$HOME/master_root/.claude/hooks/"*.py 2>/dev/null
chmod +x "$HOME/master_root/.claude/hooks/"*.sh 2>/dev/null
echo "✓ Hook scripts are executable"

# Verify hooks in settings.json
echo
echo "Verifying hook configuration..."
if grep -q "prompt_opt.py" "$HOME/master_root/.claude/settings.json"; then
    echo "✓ Prompt optimizer configured"
fi
if grep -q "answer_review.py" "$HOME/master_root/.claude/settings.json"; then
    echo "✓ Answer reviewer configured"
fi
if grep -q "safety_gate.py" "$HOME/master_root/.claude/settings.json"; then
    echo "✓ Safety gate configured"
fi

# Run tests
echo
echo "Running acceptance tests..."
python3 "$HOME/master_root/test_hooks.py"

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "1. Set your OPENAI_API_KEY in .env if not already done"
echo "2. Review settings in .env (especially KNOWLEDGE_CUTOFF date)"
echo "3. Open /hooks in Claude Code to apply changes"
echo
echo "Documentation: .claude/hooks/HOOK_PACK_README.md"
