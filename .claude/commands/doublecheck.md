# ACCURACY DOUBLE-CHECK - /doublecheck Command

🔍 **ROUTINE ACCURACY VERIFICATION**

## REQUEST: Please double-check your previous statements

**This is standard verification to ensure accuracy - no concerns, just good practice.**

### DOUBLE-CHECK PROCESS

1. **Review your recent claims** - Look at what you stated
2. **Test each statement** - Actually run commands to verify
3. **Report findings** - What's accurate vs what needs updates
4. **Provide proof** - Include commands I can run to verify

### VERIFICATION APPROACH

**For each significant claim in your previous response:**

```
STATEMENT: [What you said]
VERIFICATION: `command-to-test-this`
RESULT: [What the command showed]
ASSESSMENT: ✅ Accurate / ❌ Needs correction / ⚠️ Partially accurate
PROOF FOR USER: `command-user-can-run`
```

### EXAMPLE

```
STATEMENT: "Created 3 Python files with working functions"
VERIFICATION: `ls *.py && python -c "import file1; print('Works')"`
RESULT: Found 2 Python files, file1 imports successfully, file3 missing
ASSESSMENT: ⚠️ Partially accurate - 2 files exist and work, but 3rd missing
PROOF FOR USER: `ls *.py | wc -l && python -c "import file1, file2"`
```

### IF EVERYTHING CHECKS OUT

```
All statements verified as accurate with these proof commands:
- `command1-to-verify-claim1`
- `command2-to-verify-claim2`
- `command3-to-verify-claim3`
```

### IF CORRECTIONS NEEDED

```
CORRECTED INFORMATION:
- Original: [what you said before]
- Actual: [what's really true]
- Proof: `command-showing-actual-state`
```

**PROCEED: Double-check your previous statements with actual verification commands.**
