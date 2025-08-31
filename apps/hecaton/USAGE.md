# HECATON - Real Usage Guide

## Quick Start

HECATON is a production-ready multi-agent orchestration system that runs multiple Claude Code instances in parallel.

### Prerequisites

You need Claude Code tokens for API access. Set them up using one of these methods:

#### Method 1: Environment Variables
```bash
export CLAUDE_CODE_TOKEN="your-primary-token"
export CLAUDE_CODE_TOKEN1="your-token-1"
export CLAUDE_CODE_TOKEN2="your-token-2"
# ... up to CLAUDE_CODE_TOKEN15
```

#### Method 2: Configuration File
Edit `config/claude_tokens.json`:
```json
{
  "tokens": [
    "your-token-1",
    "your-token-2",
    "your-token-3"
  ]
}
```

### Running HECATON

#### Using the main module:
```bash
# Basic run with 2 agents
python -m hecaton run "Build a REST API"

# Run with 5 agents
python -m hecaton run "Build a complete web application" --agents 5

# Verbose output
python -m hecaton run "Analyze this codebase" --agents 3 --verbose

# Run benchmark
python -m hecaton benchmark

# Run self-test
python -m hecaton test
```

#### Using the CLI:
```bash
# Basic run
python hecaton_cli.py run "Your task here"

# With multiple agents
python hecaton_cli.py run "Complex task" --agents 5

# JSON output
python hecaton_cli.py run "Task" --output json
```

#### Using the enhanced orchestrator:
```bash
# Production-ready with all optimizations
python hecaton_cli_enhanced.py "Build enterprise application" \
  --agents 5 \
  --complexity complex \
  --profile quality
```

## How It Works

1. **Token Pool**: Rotates through your tokens for parallel execution
2. **Worktree Isolation**: Each agent works in its own git worktree
3. **Parallel Execution**: Agents run simultaneously using subprocess
4. **Real API Calls**: All agents make actual Claude API calls

## Configuration

The system automatically:
- Loads tokens from environment or config
- Creates isolated worktrees in `/tmp/hecaton_worktrees/`
- Manages parallel subprocess execution
- Handles results aggregation

## Agent Types

Available agent specializations:
- `code`: Code implementation
- `test`: Test writing
- `research`: Research and analysis
- `review`: Code review
- `docs`: Documentation

## Performance

- 2 agents: Basic parallelism
- 5 agents: Recommended for complex tasks
- 10 agents: High parallelism (requires 10 tokens)
- 15 agents: Maximum parallelism (requires 15 tokens)

## Troubleshooting

### No tokens found
- Ensure CLAUDE_CODE_TOKEN or config/claude_tokens.json is set
- Tokens must be valid Claude Code API tokens

### Agent failures
- Check token validity
- Ensure git repository is initialized
- Check `/tmp/hecaton_*.log` for debug info

### Performance issues
- Use fewer agents if rate limited
- Ensure sufficient system resources
- Check network connectivity

## Real Examples

```bash
# Build a full application
python -m hecaton run "Build a task management app with React frontend and FastAPI backend" --agents 5

# Refactor existing code
python -m hecaton run "Refactor this codebase to use async/await patterns" --agents 3

# Write comprehensive tests
python -m hecaton run "Write unit and integration tests for all modules" --agents 4

# Generate documentation
python -m hecaton run "Generate comprehensive API documentation" --agents 2
```

## Important Notes

- This runs REAL Claude API calls - costs apply
- Each agent consumes tokens independently
- Worktrees are cleaned up automatically
- Logs are stored in `/tmp/hecaton_*.log`

## Architecture

```
User Task
    ↓
Token Pool (Round-robin)
    ↓
Worktree Manager (Isolation)
    ↓
Agent Spawn (Parallel)
    ↓
Claude CLI Subprocess
    ↓
Result Aggregation
```

This is production-ready code with no simulations or mocks.
