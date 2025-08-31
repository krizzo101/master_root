# PR: Temporary Debug Print Statements for Hook Scripts

**Branch:** `temp/print-debug-20250831`
**Type:** Temporary debugging enhancement
**Priority:** Low (development aid)

## Summary

Added temporary print-based debug statements to Python hook scripts to aid in debugging without introducing heavy logging frameworks. All debug statements are:
- Guarded by `DEBUG` environment variable
- Marked with TODO comments for easy removal
- Output to stderr to avoid interfering with JSON responses

## Files Modified

1. `.claude/hooks/answer_review.py` - Added 4 debug points in key functions
2. `.claude/hooks/prompt_opt.py` - Added 4 debug points for prompt processing
3. `.claude/hooks/safety_gate.py` - Added 4 debug points for security checks

## How to Enable Debug Output

```bash
# Enable debug output for all hooks
export DEBUG=1

# Or run with debug for a single command
DEBUG=1 python3 .claude/hooks/prompt_opt.py < input.json

# Debug output appears on stderr, JSON output on stdout
```

## Sample Debug Output

```
DEBUG: prompt_opt.py:main() -- user_prompt='test prompt...'
DEBUG: prompt_opt.py:main() -- calling model=gpt-5-mini with max_tokens=4000
DEBUG: prompt_opt.py:main() -- optimized=True, research_flag=False
```

## Revert Instructions

⚠️ **IMPORTANT: This is temporary code that must be reverted before production use**

To revert all debug statements:
```bash
# Option 1: Revert all commits
git revert da91751 47b0aca 40ea593

# Option 2: Remove all lines containing "TODO: temporary print-based debug"
grep -r "TODO: temporary print-based debug" .claude/hooks/ | cut -d: -f1 | sort -u | xargs -I{} sed -i '/TODO: temporary print-based debug/,+3d' {}

# Option 3: Cherry-pick from main branch
git checkout main -- .claude/hooks/*.py
```

## Testing

All hooks tested and confirmed working:
- ✅ Basic functionality preserved (JSON output intact)
- ✅ Debug output only appears when DEBUG=1
- ✅ Debug output goes to stderr, doesn't interfere with stdout
- ✅ Exception handling still works

## Commits

- `da91751` - temp: use print for debug in answer_review.py - TODO revert to logger
- `47b0aca` - temp: use print for debug in prompt_opt.py - TODO revert to logger
- `40ea593` - temp: use print for debug in safety_gate.py - TODO revert to logger

## TODO

- [ ] Replace with proper logging framework before production
- [ ] Add log rotation and structured logging
- [ ] Consider using Python's `logging` module with JSON formatter
- [ ] Add correlation IDs for request tracking
