# Claude Headless Agent Project Structure

## 📚 Main Documentation Files (Consistent Naming)

All documentation now follows lowercase with underscores convention:

- `claude_headless_complete_guide.md` - Main consolidated guide with all optimizations
- `claude_headless_guide.md` - Original comprehensive guide with session/hook details
- `claude_testing_report.md` - Performance testing results and benchmarks
- `readme.md` - Quick reference and project overview

## 🧪 Test Scripts (`performance_tests/`)

- `test_haiku.sh` - Haiku model performance tests
- `test_sonnet.sh` - Sonnet model performance tests
- `test_opus.sh` - Opus model performance tests
- `run_parallel_tests.sh` - Run all tests in parallel
- `test_optimization_combos.sh` - Test various optimization combinations
- `test_quality_samples.sh` - Generate quality comparison samples
- `claude_agent_orchestrator.py` - Python framework for agent orchestration
- `claude_agent_optimization_tests.sh` - Comprehensive optimization test suite
- Additional utility scripts for specific test scenarios

## 📦 Archive Directory

Contains:
- 7 redundant documentation files (now consolidated)
- Test result directories from performance testing
- Old sample code files
- Previous versions of guides

## Naming Convention

All files now follow consistent naming:
- **Lowercase** throughout
- **Underscores** for word separation (not hyphens)
- **Descriptive** names that clearly indicate content
- **No mixed case** (no CamelCase or UPPERCASE)

Examples:
- ✅ `claude_headless_guide.md`
- ✅ `test_optimization_combos.sh`
- ❌ ~~`CLAUDE-HEADLESS-GUIDE.md`~~
- ❌ ~~`TestOptimizationCombos.sh`~~
