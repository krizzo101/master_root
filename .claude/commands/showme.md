# SHOW ME PROTOCOL - /showme Command

👁️ **IMMEDIATE DEMONSTRATION REQUIRED**

## NO MORE CLAIMS - SHOW ACTUAL PROOF

**Rule: Every claim must be immediately demonstrable with actual commands**

### FORMAT REQUIRED:

```
🔧 DEMONSTRATION:

CLAIM: [What you're asserting]
SHOW: `actual-command-to-run-right-now`
RESULT: [Actual output from running command]
STATUS: ✅ Works as claimed / ❌ Doesn't work / ⚠️ Partially works

CLAIM: [Next assertion]
SHOW: `next-command-to-verify`
RESULT: [Actual output]
STATUS: ✅/❌/⚠️
```

### EXAMPLES:

**❌ OLD WAY:**
"I created a working calculator"

**✅ NEW WAY:**
```
CLAIM: Created a working calculator
SHOW: `python calculator.py`
RESULT: Calculator loaded, tested 5+3=8, works correctly
STATUS: ✅ Works as claimed
```

**❌ OLD WAY:**
"Dashboard shows live data"

**✅ NEW WAY:**
```
CLAIM: Dashboard shows live data
SHOW: `curl localhost:8080/data && cat data_source.json`
RESULT: ERROR - Connection refused, data_source.json contains static numbers
STATUS: ❌ No live data - only static hardcoded values
```

### RULES:
- **RUN COMMANDS NOW** - Don't just suggest them
- **SHOW ACTUAL OUTPUT** - Copy/paste real results
- **ADMIT FAILURES** - If commands fail, report it honestly
- **NO SPECULATION** - Only report what commands actually show

### IF SOMETHING DOESN't WORK:
```
CLAIM: [What I thought was true]
SHOW: `command-I-tried`
RESULT: ERROR: [actual error message]
STATUS: ❌ My claim was wrong
REALITY: [What actually exists/works instead]
```

**PROCEED: Demonstrate every claim with actual command execution RIGHT NOW.**
