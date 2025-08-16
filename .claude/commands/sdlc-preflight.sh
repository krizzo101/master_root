#!/bin/bash
# SDLC Pre-flight Checks - MUST pass before starting any project

set -e  # Exit on any error

PROJECT_NAME=$1
PROJECT_TYPE=${2:-app}  # app or lib

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project-name> [app|lib]"
    exit 1
fi

echo "🚀 Running SDLC Pre-flight Checks for: $PROJECT_NAME"
echo "=" 
echo ""

# 1. Check Git Branch
echo "1. Git Branch Check..."
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    echo "   ❌ On main branch. Creating feature branch..."
    git checkout -b "feature/${PROJECT_NAME}-$(date +%s)"
    echo "   ✅ Created feature branch"
else
    echo "   ✅ On feature branch: $CURRENT_BRANCH"
fi

# 2. Check .gitignore
echo ""
echo "2. Git Ignore Check..."
if [ "$PROJECT_TYPE" == "app" ]; then
    TARGET_DIR="apps"
else
    TARGET_DIR="libs"
fi

if grep -q "^${TARGET_DIR}$" .gitignore || grep -q "^${TARGET_DIR}/$" .gitignore; then
    echo "   ❌ ERROR: ${TARGET_DIR}/ is in .gitignore!"
    echo "   This means your code WILL NOT be committed to git!"
    echo "   Fix: Remove '${TARGET_DIR}' from .gitignore"
    exit 1
else
    echo "   ✅ ${TARGET_DIR}/ is not ignored"
fi

# 3. Check if project already exists
echo ""
echo "3. Duplicate Check..."
if [ "$PROJECT_TYPE" == "app" ]; then
    PROJECT_PATH="apps/${PROJECT_NAME}"
else
    PROJECT_PATH="libs/opsvi-${PROJECT_NAME}"
fi

if [ -d "$PROJECT_PATH" ]; then
    echo "   ❌ ERROR: Project already exists at ${PROJECT_PATH}"
    echo "   Choose a different name or remove existing project"
    exit 1
else
    echo "   ✅ No existing project found"
fi

# 4. Create project structure
echo ""
echo "4. Creating Project Structure..."
mkdir -p "${PROJECT_PATH}"/{docs,src,tests,.sdlc}

# Initialize SDLC tracking
cat > "${PROJECT_PATH}/.sdlc/state.json" <<EOF
{
  "project": "${PROJECT_NAME}",
  "type": "${PROJECT_TYPE}",
  "phase": "discovery",
  "started": "$(date -Iseconds)",
  "feature_branch": "$(git branch --show-current)"
}
EOF

echo "   ✅ Project structure created"

# 5. Create documentation structure
echo ""
echo "5. Setting up Documentation..."
touch "${PROJECT_PATH}/docs/1-requirements.md"
touch "${PROJECT_PATH}/docs/2-design.md"
touch "${PROJECT_PATH}/docs/3-planning.md"
touch "${PROJECT_PATH}/docs/4-testing.md"
touch "${PROJECT_PATH}/docs/5-deployment.md"
echo "   ✅ Documentation structure ready"

# 6. Initialize tracking files
echo ""
echo "6. Initializing Tracking..."
cat > "${PROJECT_PATH}/.sdlc/checklist.md" <<EOF
# SDLC Checklist for ${PROJECT_NAME}

## Discovery Phase
- [ ] Research existing solutions
- [ ] Use resource_discovery MCP tool
- [ ] Query knowledge system
- [ ] Document requirements
- [ ] Create discovery-complete.json

## Design Phase
- [ ] Create architecture diagram
- [ ] Define API specifications
- [ ] Document technology choices
- [ ] Create design-complete.json

## Planning Phase
- [ ] Break down into tasks
- [ ] Create TodoWrite entries
- [ ] Estimate effort
- [ ] Create planning-complete.json

## Development Phase
- [ ] Follow task sequence
- [ ] Write tests first (TDD)
- [ ] Commit after each feature
- [ ] Create development-complete.json

## Testing Phase
- [ ] Run unit tests
- [ ] Measure coverage (>80%)
- [ ] Run integration tests
- [ ] Create testing-complete.json

## Deployment Phase
- [ ] Create deployment config
- [ ] Update documentation
- [ ] Create deployment-complete.json

## Production Phase
- [ ] Final review
- [ ] Capture lessons learned
- [ ] Update knowledge system
- [ ] Create production-complete.json
EOF

echo "   ✅ Tracking initialized"

# 7. Commit initial structure
echo ""
echo "7. Initial Commit..."
git add "${PROJECT_PATH}"
git commit -m "init: create ${PROJECT_NAME} project structure

- SDLC tracking initialized
- Documentation structure created
- Phase: discovery" || echo "   ⚠️  Nothing to commit (may be ignored path)"

# Summary
echo ""
echo "=" 
echo "✅ PRE-FLIGHT CHECKS COMPLETE"
echo ""
echo "Project Path: ${PROJECT_PATH}"
echo "Current Phase: DISCOVERY"
echo ""
echo "Next Steps:"
echo "1. cd ${PROJECT_PATH}"
echo "2. Start discovery phase work"
echo "3. Use: python .claude/commands/sdlc-tool-verification.py checklist ${PROJECT_PATH} discovery"
echo ""