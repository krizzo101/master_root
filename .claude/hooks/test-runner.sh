#!/bin/bash
# Automatic test runner hook

PROJECT_ROOT="/home/opsvi/master_root"
FILE_PATH="$1"

# Run tests for Python files
if [[ "$FILE_PATH" == *.py ]]; then
    echo "🧪 Running tests for $FILE_PATH..."

    # Find corresponding test file
    TEST_FILE="${FILE_PATH/.py/_test.py}"
    if [ -f "$TEST_FILE" ]; then
        pytest "$TEST_FILE" -v
    else
        # Run all tests if no specific test file
        pytest "$(dirname $FILE_PATH)" -v --tb=short
    fi
fi

# Run tests for TypeScript/JavaScript
if [[ "$FILE_PATH" == *.ts ]] || [[ "$FILE_PATH" == *.tsx ]]; then
    echo "🧪 Running TypeScript tests..."
    npm test 2>/dev/null || true
fi

exit 0
