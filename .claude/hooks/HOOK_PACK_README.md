# Claude Code Hook Pack - Final Implementation

## Overview
This hook pack implements an advanced optimization and review system for Claude Code using OpenAI's Responses API (gpt-5-nano model). It provides:

1. **Prompt Optimization** - Rewrites user prompts for clarity and execution-readiness
2. **Answer Review** - Validates responses with up to 3 retry attempts
3. **Research Enforcement** - Ensures time-sensitive topics include proper citations
4. **Safety Gates** - Blocks dangerous operations before execution

## Components

### 1. Prompt Optimizer (`prompt_opt.py`)
- **Trigger**: UserPromptSubmit event
- **Function**: Optimizes user prompts into execution-ready instructions
- **Features**:
  - Detects time-sensitive topics requiring research
  - Injects RESEARCH BEFORE ACTION directives when needed
  - Uses structured outputs for consistent formatting
  - Gracefully degrades if API unavailable

### 2. Answer Reviewer (`answer_review.py`)
- **Triggers**: Stop, SubagentStop, PostToolUse events
- **Function**: Reviews agent responses for quality and accuracy
- **Features**:
  - Up to 3 retry attempts with actionable guidance
  - Research citation enforcement for volatile topics
  - Optional escalation to gpt-5-mini on first failure
  - Separate attempt counters per tool/scope

### 3. Safety Gate (`safety_gate.py`)
- **Trigger**: PreToolUse event (Edit, Write, Bash)
- **Function**: Blocks dangerous operations before execution
- **Protected**:
  - Files: `.env`, `.git/`, `secrets.json`, `/prod/`
  - Commands: `rm -rf /`, `sudo`, fork bombs

## Configuration

### Environment Variables
Add these to your `.env` file (see `hook_pack_config.txt`):

```bash
# Knowledge freshness controls
KNOWLEDGE_CUTOFF=2024-06-01          # ISO date for knowledge cutoff
RESEARCH_ENABLE=true                 # Enable/disable research enforcement
RESEARCH_SOURCES_REQUIRED=true       # Require citations for time-sensitive topics

# Unstable topics (comma-separated)
RESEARCH_UNSTABLE_TOPICS=latest,breaking,today,as of,price,cost,fee,exchange rate,version,api,sdk,library,release,changelog,cve,law,regulation,compliance,policy,election,medical,drug,dosage,availability,schedule,deadline,admission,calendar,travel,weather,market,stock,crypto,ceo,cfo,leadership,org change

# OpenAI model configuration
PROMPT_OPT_MODEL=gpt-5-nano         # Model for prompt optimization
PROMPT_OPT_MAX_TOK=400              # Max tokens for optimization
PROMPT_OPT_TEMPERATURE=0.2         # Temperature for consistency
PROMPT_OPT_SEED=42                 # Seed for reproducibility

# Review model configuration
REVIEW_MODEL=gpt-5-nano            # Primary review model
REVIEW_MODEL_ESCALATE=gpt-5-mini   # Escalation model (optional)
REVIEW_MAX_ATTEMPTS=3              # Max review attempts
REVIEW_MAX_TOK=300                 # Max tokens for review
REVIEW_TEMPERATURE=0.2             # Temperature for review
REVIEW_SEED=42                     # Seed for review
```

### Required Dependencies
```bash
pip install openai>=1.40.0
```

## Usage

### Activation
1. Ensure OPENAI_API_KEY is set in your environment
2. Add configuration variables to `.env`
3. Hooks are automatically active via `.claude/settings.json`
4. Open `/hooks` in Claude Code to review changes

### Testing
Run the acceptance test suite:
```bash
python /home/opsvi/master_root/test_hooks.py
```

### Expected Behavior

#### Time-Sensitive Prompts
**Input**: "What's the current Python 3.13 status?"
**Result**: Optimizer injects RESEARCH BEFORE ACTION directive

#### Missing Citations
**Input**: "Best current price of RTX 5090?"
**Without sources**: Reviewer blocks with "Research required" message
**With sources**: Response passes review

#### Stable Topics
**Input**: "Refactor utils/slugify.ts"
**Result**: No research directive, standard processing

## Performance Tuning

### Model Selection
- **gpt-5-nano**: Primary model (fast, efficient)
- **gpt-5-mini**: Optional escalation (higher quality)

### Optimization Parameters
- Temperature: 0.2 (consistent outputs)
- Max tokens: 300-400 (balanced responses)
- Seed: 42 (reproducible results)
- Verbosity: "low" (minimal overhead)

## Graceful Degradation

All hooks implement fail-safe mechanisms:
- **No API Key**: Hooks suppress output, allow normal flow
- **API Errors**: Hooks don't block user operations
- **Timeout**: Configurable per hook (20-60 seconds)
- **Invalid Input**: Safe defaults applied

## Security Considerations

### Protected Resources
- Environment files (`.env`, `secrets.json`)
- Version control (`.git/`)
- Production paths (`/prod/`)
- System commands (`sudo`, `rm -rf`)

### Hook Permissions
- Run under user account
- Limited to configured timeouts
- Cannot access external resources beyond API

## Troubleshooting

### Hook Not Triggering
1. Check `settings.json` configuration
2. Verify hook files are executable
3. Confirm CLAUDE_PROJECT_DIR is set

### API Errors
1. Verify OPENAI_API_KEY is valid
2. Check API quota/limits
3. Review error logs in hook output

### Research Not Enforced
1. Confirm RESEARCH_ENABLE=true
2. Check KNOWLEDGE_CUTOFF date
3. Verify topic matches RESEARCH_UNSTABLE_TOPICS

## Architecture

```
User Prompt
    ↓
[prompt_opt.py] → Optimization + Research Detection
    ↓
Claude Code Processing
    ↓
[safety_gate.py] → Block Dangerous Operations
    ↓
Tool Execution
    ↓
[answer_review.py] → Quality Check + Citation Enforcement
    ↓
Response Delivery
```

## Maintenance

### Updating Topics
Edit RESEARCH_UNSTABLE_TOPICS in `.env` to add/remove volatile topics

### Adjusting Models
Change model names in `.env` (e.g., when gpt-6 releases)

### Modifying Thresholds
Adjust MAX_ATTEMPTS, temperatures, and token limits as needed

## Version
- Implementation Date: 2025-08-30
- Hook Pack Version: 1.0.0
- Compatible with: Claude Code (latest)
- Requires: Python 3.9+, OpenAI API 1.40.0+
