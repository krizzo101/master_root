# COMPREHENSIVE VERIFICATION - /verify-all Command

🔍 **COMPREHENSIVE ACCURACY CHECK REQUEST**

## TASK: Verify accuracy of all your previous statements

**This is routine verification to ensure accuracy - not an investigation.**

### VERIFICATION PROCESS

Please review your recent responses and:

1. **Test Each Claim**: Run commands to verify your statements
2. **Report Results**: Show what works vs what doesn't
3. **Provide Evidence**: Include proof commands for everything
4. **Correct if Needed**: Update any inaccurate information

### VERIFICATION CATEGORIES

**Files & Directories:**
- Verify claimed files exist: `ls -la [files]`
- Check file contents match descriptions: `cat/head [files]`

**Functionality:**
- Test claimed features work: `python script.py` or relevant commands
- Verify integrations: Test connections, APIs, etc.

**Performance:**
- Measure any performance claims: Benchmark commands
- Confirm capacity/speed statements: Load tests if applicable

### VERIFICATION FORMAT

For each claim, provide:

```
CLAIM: [What I stated]
TEST: `command-I-ran-to-verify`
RESULT: [Actual output/result]
STATUS: ✅ Verified / ❌ Incorrect / ⚠️ Partially correct
CORRECTION: [If needed, corrected information]
```

### EXAMPLE

```
CLAIM: Created dashboard.html with live data
TEST: `ls -la dashboard.html && head -10 dashboard.html`
RESULT: File exists (2.1KB), contains static HTML with hardcoded numbers
STATUS: ⚠️ Partially correct - file exists but data is static, not live
CORRECTION: dashboard.html exists with static data, no live data connection
```

**PROCEED: Verify all your previous statements using actual commands and report results.**
