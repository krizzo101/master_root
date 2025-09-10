# Test-Driven Development Workflow

Follow strict TDD discipline: Red → Green → Refactor

## Workflow

### 1. RED Phase (Write Failing Test)
- Understand the requirement clearly
- Write a test that describes the desired behavior
- Run the test and confirm it fails
- Commit: `git add . && git commit -m "test: add failing test for [feature]"`

### 2. GREEN Phase (Make Test Pass)
- Write MINIMAL code to make the test pass
- Don't add extra functionality
- Don't worry about code quality yet
- Run test and confirm it passes
- Commit: `git add . && git commit -m "feat: implement [feature] to pass test"`

### 3. REFACTOR Phase (Improve Code)
- Clean up the implementation
- Remove duplication
- Improve naming and structure
- Ensure tests still pass
- Commit: `git add . && git commit -m "refactor: improve [feature] implementation"`

## Commands to Run

For Python:
```bash
pytest path/to/test.py::TestClass::test_method -v
```

For JavaScript/TypeScript:
```bash
npm test -- path/to/test.spec.ts
```

For Go:
```bash
go test -run TestFunctionName ./...
```

## Rules
1. NEVER write code without a failing test first
2. ONLY write enough code to pass the current failing test
3. ALWAYS refactor after getting to green
4. COMMIT after each phase (red, green, refactor)
5. If stuck in red for >10 minutes, write a simpler test

## Benefits Reminder
- Ensures code is testable
- Documents behavior through tests
- Prevents over-engineering
- Builds confidence in changes
- Creates a safety net for refactoring
