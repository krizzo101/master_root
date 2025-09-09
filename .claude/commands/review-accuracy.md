# ACCURACY REVIEW - /review-accuracy Command

🔍 **ACCURACY REVIEW REQUEST**

## REQUEST: Review your statements for any inaccuracies

**Please examine your recent responses and identify any statements that may be incorrect or need clarification.**

### REVIEW PROCESS

**1. IDENTIFY INACCURACIES:**
```
STATEMENT: [What I said before]
REALITY CHECK: `command-to-verify`
ACTUAL RESULT: [What the command shows]
ASSESSMENT: ✅ Accurate / ❌ Inaccurate / ⚠️ Needs clarification
```

**2. PROVIDE CORRECTIONS:**
- Which statements need updating?
- What's the accurate information?
- How can accuracy be verified?

**3. UPDATED INFORMATION:**
```
CORRECTED: [Accurate version of the statement]
VERIFICATION: `command-to-prove-accuracy`
EXPLANATION: [Brief note on what was unclear/incorrect]
```

### EXAMPLE REVIEW:
```
STATEMENT: "Created live dashboard monitoring 10 workflows"
REALITY CHECK: `ls -la dashboard.html && grep -i "live\|websocket" dashboard.html`
ACTUAL RESULT: File exists but contains static HTML, no live data connections
ASSESSMENT: ❌ Inaccurate - dashboard exists but is static, not live

CORRECTED: Static HTML dashboard file exists with hardcoded sample data
VERIFICATION: `file dashboard.html && head -20 dashboard.html`
EXPLANATION: Used "live dashboard" when it's actually static HTML with sample data
```

### GUIDANCE:
- **Focus on accuracy** - Just getting the facts right
- **Provide verification** - Commands to check corrected information
- **Be clear** - Explain what was unclear or overstated
- **No judgment** - This is about improving accuracy, not fault-finding

### IF NO INACCURACIES FOUND:
```
REVIEW RESULT: All previous statements verified as accurate
VERIFICATION COMMANDS:
- `command1-that-confirms-claim1`
- `command2-that-confirms-claim2`
```

**PROCEED: Review your statements and identify any that need clarification or correction.**
