# Claude Code File Loading Mechanism

## Automatic Loading (No import needed)

1. **CLAUDE.md** - Loaded from project root and all parent directories
2. **`.claude/settings.json`** - Hooks configuration
3. **`.claude/settings.local.json`** - Local overrides
4. **`.claude/agents/*.md`** - When subagents are invoked

## Manual Import Required

Files in `.claude/` are NOT automatically loaded unless imported.

### Import Syntax in CLAUDE.md

```markdown
@.claude/MODEL_AWARENESS_2025.md
@.claude/commands/QUICK_REFERENCE.md
@.cursor/rules/953-openai-api-standards.mdc
```

### Import Rules

- Paths are relative to project root
- Supports up to 5 levels of nested imports
- Imported content is included at load time
- Files can import other files recursively

## Current Import Structure

```
CLAUDE.md
├── @.claude/MODEL_AWARENESS_2025.md  # Model awareness
└── References:
    └── .cursor/rules/953-openai-api-standards.mdc  # OpenAI standards
```

## Best Practices

1. Keep CLAUDE.md concise (<2000 tokens)
2. Use imports for detailed documentation
3. Import order matters (later imports can override)
4. Test imports with `/memory` command to verify loading

## Verification

To check what's loaded:
```bash
/memory  # View current memory
/reload  # Reload CLAUDE.md and imports
```
