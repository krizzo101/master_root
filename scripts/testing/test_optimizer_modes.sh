#!/bin/bash
echo "=== Testing Prompt Optimizer Modes ==="
echo ""

test_prompt() {
    local prompt="$1"
    local desc="$2"
    echo "Test: $desc"
    echo "Input: '$prompt'"

    result=$(echo "{\"prompt\": \"$prompt\", \"session_id\": \"test\"}" | \
        OPENAI_API_KEY="${OPENAI_API_KEY:-test_key}" \
        /home/opsvi/miniconda/bin/python /home/opsvi/master_root/.claude/hooks/prompt_opt.py 2>/dev/null)

    if echo "$result" | grep -q "PROMPT_OPTIMIZER"; then
        echo "Result: ✅ OPTIMIZED"
    elif echo "$result" | grep -q "USER EXACT INSTRUCTIONS"; then
        echo "Result: 🔒 BYPASSED (raw)"
    elif echo "$result" | grep -q "suppressOutput"; then
        echo "Result: ⏭️ SKIPPED"
    else
        echo "Result: ❓ Unknown"
    fi
    echo ""
}

# Test OPT-OUT mode (default)
echo "=== MODE: opt-out (default - optimize unless !skip) ==="
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh set opt-out >/dev/null 2>&1
test_prompt "Create an app" "Normal prompt"
test_prompt "!skip Create an app" "With !skip prefix"
test_prompt "!raw docker-compose up" "With !raw prefix"
echo ""

# Test OPT-IN mode
echo "=== MODE: opt-in (only optimize with !!) ==="
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh set opt-in >/dev/null 2>&1
test_prompt "Create an app" "Normal prompt"
test_prompt "!! Create an app" "With !! prefix"
test_prompt "!opt Build a system" "With !opt prefix"
test_prompt "!raw docker-compose up" "With !raw prefix"
echo ""

# Test ALWAYS mode
echo "=== MODE: always (always optimize except !raw) ==="
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh set always >/dev/null 2>&1
test_prompt "Create an app" "Normal prompt"
test_prompt "!skip Create an app" "With !skip (ignored in always mode)"
test_prompt "!raw docker-compose up" "With !raw prefix"
echo ""

# Test DISABLED mode
echo "=== MODE: disabled (never optimize) ==="
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh set disabled >/dev/null 2>&1
test_prompt "Create an app" "Normal prompt"
test_prompt "!! Create an app" "With !! (ignored when disabled)"
test_prompt "!raw docker-compose up" "With !raw prefix"
echo ""

# Reset to opt-out
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh set opt-out >/dev/null 2>&1
echo "Reset to opt-out mode for normal use."
echo ""

# Show current status
/home/opsvi/master_root/.claude/hooks/prompt_opt_mode.sh status
