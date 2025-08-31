# CLAUDE.md - Enhanced Project Configuration

## 🎯 Project Overview
**Project Name**: Master Root Development Environment
**Type**: Multi-Service Development Platform
**Primary Language**: Python
**Architecture**: Microservices with MCP Integration

## 🛠️ Tech Stack
- **Languages**: Python 3.11+, TypeScript, Bash
- **Frameworks**: FastAPI, FastMCP, Pydantic
- **AI/ML**: OpenAI GPT-5, Anthropic Claude, Google Gemini
- **Database**: Neo4j, PostgreSQL, SQLite
- **Tools**: Docker, Git, pytest, ruff, mypy
- **MCP Servers**: Knowledge, Thinking, Claude-Code-Wrapper, Consult Suite

## 📁 Project Structure
```
/home/opsvi/master_root/
├── apps/                  # Applications
│   ├── ACCF/             # AI Consulting Framework
│   └── thinking-supervisor/  # Metacognitive systems
├── libs/                  # Shared libraries
│   └── opsvi_mcp/        # MCP server implementations
├── .claude/              # Claude Code configuration
│   ├── commands/         # Slash commands
│   ├── agents/           # Custom sub-agents
│   └── hooks/            # Automation hooks
└── scripts/              # Automation scripts
```

## 🔧 Development Standards

### Code Style
- Use Black formatter for Python (line length: 88)
- Follow PEP 8 with type hints
- Docstrings for all public functions
- Meaningful variable names (no single letters except loops)

### Git Workflow
- Branch naming: `feature/`, `fix/`, `docs/`, `refactor/`
- Commit messages: conventional commits format
- Always create feature branches from main
- Squash merge for features, regular merge for fixes

### Testing Requirements
- Minimum 80% code coverage
- Unit tests for all new functions
- Integration tests for API endpoints
- Use pytest with fixtures

### Security Practices
- NEVER commit secrets or API keys
- Use environment variables for credentials
- Validate all inputs
- Implement proper error handling
- Follow OWASP guidelines

## 🚀 Quick Commands

### Development
```bash
# Run tests
pytest --cov=. --cov-report=term-missing

# Type checking
mypy .

# Linting
ruff check .

# Format code
black .

# Start services
docker-compose up -d
```

### MCP Operations
```bash
# Test MCP server
python -m opsvi_mcp.servers.knowledge.server

# Claude Code wrapper
PYTHONPATH=/home/opsvi/master_root/libs python -m opsvi_mcp.servers.claude_code
```

## 🤖 AI Assistant Instructions

### MANDATORY On Session Start
1. Load knowledge base instructions
2. Check recent work context
3. Review pending tasks
4. Verify environment state

### Code Generation Rules
1. ALWAYS check existing patterns before writing new code
2. Use existing utilities and libraries
3. Follow project conventions exactly
4. Add comprehensive error handling
5. Include type hints for Python
6. Write tests alongside implementation

### File Operations
1. PREFER editing over creating new files
2. Check file existence before operations
3. Use absolute paths
4. Backup critical files before major changes

### Communication Style
1. Be concise and direct
2. Use bullet points for lists
3. Provide code examples
4. Explain complex changes
5. Ask for clarification when ambiguous

## 📋 Task Management

### Priority Levels
- **P0**: Critical bugs, security issues
- **P1**: Feature implementation, important fixes
- **P2**: Improvements, refactoring
- **P3**: Documentation, nice-to-have

### Workflow Steps
1. Understand requirements fully
2. Plan implementation approach
3. Check existing code patterns
4. Implement with tests
5. Verify functionality
6. Update documentation

## 🔍 Code Review Checklist
- [ ] Follows project conventions
- [ ] Has appropriate tests
- [ ] Includes error handling
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance considered
- [ ] Code is maintainable

## 🌐 External Integrations
- **GitHub**: Issue tracking, PRs
- **Neo4j**: Knowledge graph storage
- **OpenAI**: AI model integration
- **Brave Search**: Web search capability
- **Firecrawl**: Web scraping

## 📚 Important Files
- `/home/opsvi/master_root/.mcp.json` - MCP server configuration
- `/home/opsvi/master_root/CLAUDE.md` - This file
- `/home/opsvi/master_root/.env` - Environment variables
- `/home/opsvi/master_root/pyproject.toml` - Python project config

## 🚨 Critical Warnings
1. NEVER modify production databases directly
2. ALWAYS validate user inputs
3. Check memory usage for large operations
4. Be cautious with recursive operations
5. Verify API rate limits

## 🎓 Learning Resources
- MCP Documentation: https://modelcontextprotocol.io/
- Claude Code Docs: https://docs.anthropic.com/en/docs/claude-code/
- Project Wiki: Internal documentation
- Team Playbooks: Standard procedures

## 🔄 Continuous Improvement
- Regular code reviews
- Performance monitoring
- Security audits
- Documentation updates
- Knowledge base maintenance

## 📝 Session Notes
<!-- Add session-specific notes here -->
- Current focus: Enhanced Claude Code setup
- Recent changes: Added MCP servers, commands, agents
- Next steps: Complete automation setup

---
*This CLAUDE.md is version-controlled and should be updated as the project evolves.*
