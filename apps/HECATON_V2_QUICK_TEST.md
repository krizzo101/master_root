# HECATON V2 Quick Test Guide

## Quick Validation Commands

### 1. Extract Archive
```bash
cd /home/opsvi/master_root/apps
tar -xzf hecaton_v2_with_mergeback.tar.gz
cd hecaton
```

### 2. Run Unit Tests
```bash
# Test merge-back functionality
PYTHONPATH=src python -m unittest tests.test_merge_back -v

# Expected: 8 tests passing
```

### 3. Test Basic Execution
```bash
# Simple parallel execution
python -m hecaton run "Write a hello world function" --agents 2

# With merge-back (dry-run for safety)
python -m hecaton run "Add error handling" --agents 3 --merge-back --dry-run
```

### 4. Verify Send API
```bash
# Check for true parallel execution
python -m hecaton run "Create REST endpoints" --agents 3 --verbose
# Look for: "🚀 Running HECATON with Send API parallel orchestration"
```

### 5. Test Conflict Detection
```bash
# This should generate conflicts and Fix-It tasks
python -m hecaton run "Refactor the main module completely" --agents 3 --merge-back --dry-run
```

## Key Files to Review

1. **Send API Orchestrator**: `src/hecaton/orchestration/send_api.py`
   - Line 37-56: OrchestrationState TypedDict with reducers
   - Line 205-218: _route_agents returning List[Send]

2. **Merger Module**: `src/hecaton/orchestration/merger.py`
   - Line 85-120: order_patches method
   - Line 150-200: apply_patches with conflict detection

3. **Tests**: `tests/test_merge_back.py`
   - Comprehensive test coverage for all merge-back features

## Success Indicators

✅ **Working Correctly If**:
- Tests pass (8/8)
- Agents run in parallel (not sequential)
- Patches are generated in `.hecaton/patches/`
- Conflicts are detected and reported
- Fix-It tasks are created for failures

❌ **Issues If**:
- "Expected dict, got [Send...]" error → Send API not fixed
- "AttributeError: 'dict' object has no attribute" → State management issue
- No patches generated → Export not working
- All patches conflict → Ordering issue

## Performance Benchmarks

Expected timings for 3-agent execution:
- **Sequential**: ~90 seconds
- **Parallel (Send API)**: ~30 seconds
- **Speedup**: 3x

## Common Issues and Solutions

### Issue: No patches exported
**Solution**: Check that agents are making changes and worktrees are writable

### Issue: All patches conflict
**Solution**: Verify patch ordering is working (docs → tests → src → code)

### Issue: Gates always fail
**Solution**: Check gate_commands in MergeBackConfig, may need to adjust for environment

### Issue: PR not created
**Solution**: Ensure git is configured and --dry-run is not set

## Quick Diagnostics

```bash
# Check if Send API is being used
grep -n "Send(" src/hecaton/orchestration/send_api.py

# Verify TypedDict state
grep -n "TypedDict" src/hecaton/orchestration/send_api.py

# Check patch export
grep -n "_export_patch" src/hecaton/agents/real_claude_executor.py

# Verify test coverage
PYTHONPATH=src python -m pytest tests/test_merge_back.py --cov=hecaton.orchestration --cov=hecaton.config
```

## Evaluation Checklist

- [ ] Archive extracts successfully
- [ ] Unit tests pass (8/8)
- [ ] Parallel execution works
- [ ] Patches are exported
- [ ] Patches are ordered correctly
- [ ] Conflicts are detected
- [ ] Fix-It tasks are created
- [ ] Quality gates run
- [ ] PR can be created (or direct merge)
- [ ] No linting errors

## Contact for Issues

If you encounter issues during evaluation:
1. Check the debug logs in `logs/hecaton_debug_*.log`
2. Review the implementation in the files listed above
3. Run with `--verbose` flag for detailed output
