# Claude Headless Agent Documentation

## 📚 Main Documentation

### [claude_headless_complete_guide.md](./claude_headless_complete_guide.md)
The complete, consolidated guide for running Claude in headless mode with all optimizations and best practices.

### [claude_headless_guide.md](./claude_headless_guide.md)
Original comprehensive guide with detailed examples, session management, and hook configurations.

### [claude_testing_report.md](./claude_testing_report.md)
Performance testing report with benchmarks and findings.

## 🚀 Quick Start

```bash
# One-time setup (30 seconds)
echo '{"mcpServers": {}}' > ~/.claude_minimal.json

# Run optimized Claude (3-20 seconds per call)
claude -p \
  --model opus \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  --session-id "$(uuidgen)" \
  "Your task"
```

## 📊 Key Performance Findings

- **Sonnet is fastest** (3.18s optimized) - surprising but true!
- **MCP servers cause 80% of delays** - always use `--strict-mcp-config`
- **Model differences are minimal** (1-3 seconds for simple tasks)
- **Parallelization cuts time by 70%** for multi-agent workflows

## 📁 Project Structure

```
/home/opsvi/test/
├── claude_headless_complete_guide.md         # Main consolidated guide
├── claude_headless_guide.md                  # Original detailed guide
├── claude_testing_report.md                  # Performance test results
├── readme.md                                  # This file
├── performance_tests/                        # Test scripts and tools
│   ├── test_haiku.sh
│   ├── test_sonnet.sh
│   ├── test_opus.sh
│   ├── run_parallel_tests.sh
│   └── claude_agent_orchestrator.py
└── archive/                                  # Old docs and test results
```

## 🎯 The 80/20 Solution

For 95% of your tasks, use:
```bash
claude -p \
  --model opus \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  "Your task"
```

Expected performance:
- Simple tasks: **3-10 seconds**
- Normal tasks: **10-30 seconds**
- Complex tasks: **30-100 seconds**
- Multi-agent: **2-5 minutes** (parallel)

Your 15+ minute problem is solved!
