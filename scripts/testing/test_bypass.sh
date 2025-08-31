#!/bin/bash
echo "=== Testing Prompt Optimizer Bypass Features ==="
echo ""

# Test 1: Normal prompt (gets optimized)
echo "1. Normal prompt:"
echo "   Input: 'Create an app'"
echo '{"prompt": "Create an app", "session_id": "test"}' | python3 -c "
import json, sys
inp = json.load(sys.stdin)
print(f\"   Would optimize: {inp['prompt']}\")
"

echo ""
echo "2. !raw prefix (bypasses optimization):"
echo "   Input: '!raw docker-compose up --build'"
echo '{"prompt": "!raw docker-compose up --build", "session_id": "test"}' | python3 -c "
import json, sys
inp = json.load(sys.stdin)
prompt = inp['prompt']
if prompt.lower().startswith('!raw '):
    print(f\"   Bypassed! Sends exact: {prompt[5:]}\")
else:
    print(f\"   Would optimize: {prompt}\")
"

echo ""
echo "3. [RAW] tags (partial bypass):"
echo "   Input: 'Build app with [RAW]legacy_api_v1.2.3[/RAW] integration'"
echo '{"prompt": "Build app with [RAW]legacy_api_v1.2.3[/RAW] integration", "session_id": "test"}' | python3 -c "
import json, sys, re
inp = json.load(sys.stdin)
prompt = inp['prompt']
raw_pattern = r'\[RAW\](.*?)\[/RAW\]'
raw_parts = re.findall(raw_pattern, prompt, re.IGNORECASE)
clean = re.sub(raw_pattern, '', prompt, flags=re.IGNORECASE)
print(f\"   Optimizes: {clean.strip()}\")
print(f\"   Preserves: {', '.join(raw_parts)}\")
"

echo ""
echo "=== Usage Guide ==="
echo ""
echo "1. To bypass ALL optimization:"
echo "   !raw <your exact command>"
echo "   !exact <your exact text>"
echo "   !verbatim <your exact prompt>"
echo ""
echo "2. To bypass PARTS of your prompt:"
echo "   Use [RAW]...[/RAW] tags around sensitive parts"
echo "   Example: Create function [RAW]calculateTax(income, state='CA')[/RAW]"
echo ""
echo "3. The optimizer will:"
echo "   - Skip optimization for !raw/!exact/!verbatim prefixes"
echo "   - Preserve [RAW] sections exactly as typed"
echo "   - Optimize the rest of your prompt normally"
