# Token Configuration Guide

## Current Status
✅ **15 Claude Code tokens** are configured and validated

## Token Storage Locations

### Primary Storage (Encrypted)
- **Location**: `/apps/multi-agent-monitor/.secrets/tokens.encrypted`
- **Encryption**: AES-256 via Fernet cipher
- **Key File**: `.secrets/.key` (auto-generated, secure)

### Environment Variables
- Tokens can be loaded from: `CLAUDE_CODE_TOKEN1` through `CLAUDE_CODE_TOKEN15`
- Primary token: `CLAUDE_CODE_TOKEN` (if present)

## Managing Tokens

### Using Secrets Manager

```bash
# Interactive setup (recommended)
cd apps/multi-agent-monitor
python src/orchestration/secrets_manager.py

# Commands available:
python src/orchestration/secrets_manager.py list      # List token numbers
python src/orchestration/secrets_manager.py validate  # Validate all tokens
python src/orchestration/secrets_manager.py import    # Import from environment
python src/orchestration/secrets_manager.py export    # Export to environment
python src/orchestration/secrets_manager.py rotate    # Rotate encryption key
```

### Token Format
All Claude Code tokens should:
- Start with `sk-ant-`
- Be at least 50 characters long
- Be unique (no duplicates)

## Parallel Execution Capabilities

With 15 tokens, the system can run:
- **15 agents simultaneously** for maximum parallelism
- **Multiple teams** working on different phases
- **Entire workflows** in a single parallel batch

## Token Allocation Strategy

### Default Round-Robin
Tokens are distributed in order:
- Agent 1 gets Token 1
- Agent 2 gets Token 2
- ...
- Agent 16 gets Token 1 (wraps around)

### Team-Based Allocation
Teams can reserve specific token ranges:
- Discovery Team: Tokens 1-3
- Development Team: Tokens 4-9
- Testing Team: Tokens 10-12
- Deployment Team: Tokens 13-15

## Verification

To verify tokens are working:
```bash
cd apps/multi-agent-monitor
python test_basic.py
```

Expected output:
```
[1] Testing Token Management...
   ✅ Loaded 15 tokens successfully
```

## Security Notes

1. **Never commit tokens** to version control
2. **Tokens are encrypted** at rest in `.secrets/`
3. **Directory permissions** set to 0700 (owner only)
4. **File permissions** set to 0600 (owner read/write only)
5. **Automatic encryption** when plaintext tokens detected

## Troubleshooting

### Missing Tokens
- Check environment variables are set
- Run `python src/orchestration/secrets_manager.py import`

### Invalid Tokens
- Verify format starts with `sk-ant-`
- Check for trailing spaces or newlines
- Ensure no duplicates

### Token Rotation Issues
- Agents using old tokens will fail
- Update all running processes after rotation
- Check logs for authentication errors

## Performance Impact

| Tokens | Max Parallel Agents | Speedup | Use Case |
|--------|-------------------|---------|----------|
| 1 | 1 | 1x | Sequential execution |
| 3 | 3 | 3x | Small teams |
| 6 | 6 | 6x | Medium projects |
| 10 | 10 | 10x | Large projects |
| 15 | 15 | 15x | Enterprise workflows |

## Best Practices

1. **Use all available tokens** for maximum parallelism
2. **Monitor token usage** via pool status
3. **Rotate tokens monthly** for security
4. **Test token validity** before large runs
5. **Keep spare tokens** for debugging/testing
