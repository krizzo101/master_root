# HECATON - A Hundred Hands Building as One

> Multi-Agent Orchestration Framework for Self-Amplifying Systems

## 🎯 Overview

HECATON is a self-amplifying multi-agent orchestration framework that starts with minimal parallel execution capability and builds itself into a full-featured system. Named after the Hecatoncheires (hundred-handed giants) from Greek mythology, HECATON enables true parallel execution of Claude Code agents.

## 🚀 Quick Start

### Phase 0: Bootstrap (Current)

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Claude Code tokens

# 2. Install dependencies
./scripts/run.sh setup

# 3. Run Phase 0 test (2 agents in parallel)
./scripts/run.sh test-parallel

# 4. Start Phase 1 bootstrap (system builds itself)
./scripts/run.sh bootstrap
```

## 📁 Project Structure

```
hecaton/
├── src/hecaton/           # Main package
│   ├── core/             # Core orchestrator
│   ├── orchestration/    # Send API, token pool, worktrees
│   ├── agents/           # Agent registry and types
│   ├── resources/        # Resource management
│   └── utils/            # Utilities
├── tests/                # Test suites
├── docs/                 # Documentation
│   └── design/          # Architecture docs
├── config/              # Configuration files
├── templates/           # Agent templates
└── scripts/            # Automation scripts
```

## 🔄 Bootstrapping Phases

### Phase 0: Manual Core (2 agents) ✅
- Minimal 4-file implementation
- 2-agent parallel execution
- Basic Send API orchestration

### Phase 1: Assisted Expansion (5 agents) 🚧
- System uses itself to expand
- Token pool expansion
- Enhanced error handling

### Phase 2: Semi-Autonomous (10 agents) 📅
- Agent registry
- Inter-agent communication
- Phase management

### Phase 3: Autonomous Evolution (15 agents) 📅
- Self-improvement capabilities
- Performance optimization
- Automatic bottleneck resolution

### Phase 4: Self-Optimizing (Continuous) 📅
- Continuous improvement loop
- Automatic feature implementation
- Self-documenting

## 🛠️ Development

```bash
# Run tests
./scripts/run.sh test

# Run linting & formatting
./scripts/run.sh quality

# Run security scan
./scripts/run.sh security

# Start development server
./scripts/run.sh dev

# Build project
./scripts/run.sh build
```

## 📚 Documentation

- [Architecture Overview](docs/design/MULTI_AGENT_ARCHITECTURE_V2.md)
- [Technical Specification](docs/design/MULTI_AGENT_TECHNICAL_SPEC_V2.md)
- [Implementation Guide](docs/design/MULTI_AGENT_IMPLEMENTATION_GUIDE.md)
- [Bootstrapping Plan](docs/design/BOOTSTRAPPING_IMPLEMENTATION_PLAN.md)
- [Phase 0 Implementation](docs/design/HECATON_PHASE_0_IMPLEMENTATION.md)

## 🔑 Key Features

- **Send API Parallelism**: True parallel execution using LangGraph Send API
- **Token Pool Management**: Thread-safe round-robin token rotation
- **Git Worktree Isolation**: Each agent gets isolated workspace
- **Self-Building**: System uses its own capabilities to build itself
- **Progressive Enhancement**: Each phase builds on the previous

## 📊 Performance

| Metric | Target | Current |
|--------|--------|---------|
| Parallel Agents | 15 | 2 |
| Performance Gain | 3-5x | Testing |
| Bootstrap Time | 4 days | In Progress |

## 🤝 Contributing

This is a self-building system. Contributions should focus on:
1. Ensuring Phase 0 works perfectly
2. Letting the system build itself for subsequent phases
3. Documenting learnings and patterns

## 📄 License

MIT

---

**Current Status**: Phase 0 Implementation
**Next Milestone**: 2-agent parallel execution test
