#!/bin/bash
# Clean up unused opsvi libraries
# Run from master_root directory

set -e  # Exit on error

echo "="
echo "OPSVI Library Cleanup Script"
echo "="
echo

# Check we're in the right directory
if [ ! -d "libs" ]; then
    echo "Error: libs/ directory not found. Run from master_root directory."
    exit 1
fi

# 1. Create archive directory
echo "Creating archive directory..."
mkdir -p libs/ARCHIVED
echo "✓ Archive directory created"
echo

# 2. Remove empty stub libraries (no value to archive)
echo "Removing empty stub libraries..."
for lib in opsvi-communication opsvi-coordination opsvi-orchestration opsvi-sdlc-enhancements; do
    if [ -d "libs/$lib" ]; then
        file_count=$(find "libs/$lib" -name "*.py" 2>/dev/null | wc -l)
        echo "  Removing $lib (${file_count} py files)..."
        rm -rf "libs/$lib"
        echo "  ✓ Removed $lib"
    else
        echo "  ⊘ $lib already removed"
    fi
done
echo

# 3. Archive unused but substantial libraries
echo "Archiving unused libraries..."
for lib in opsvi-agents opsvi-auto-forge opsvi-memory opsvi-workers opsvi-orchestrator opsvi-comm opsvi-coord; do
    if [ -d "libs/$lib" ]; then
        file_count=$(find "libs/$lib" -name "*.py" 2>/dev/null | wc -l)
        echo "  Archiving $lib (${file_count} py files)..."
        mv "libs/$lib" "libs/ARCHIVED/"
        echo "  ✓ Archived $lib"
    elif [ -d "libs/ARCHIVED/$lib" ]; then
        echo "  ⊘ $lib already archived"
    else
        echo "  ⊘ $lib not found"
    fi
done
echo

# 4. Report on remaining libraries
echo "Remaining active libraries:"
echo "---"
active_count=0
for lib in libs/opsvi-*/; do
    if [ -d "$lib" ]; then
        name=$(basename "$lib")
        has_setup="✗"
        [ -f "$lib/setup.py" ] && has_setup="✓"
        file_count=$(find "$lib" -name "*.py" 2>/dev/null | wc -l)
        printf "%-30s setup.py: %s  files: %4d\n" "$name" "$has_setup" "$file_count"
        ((active_count++))
    fi
done
echo
echo "Total active libraries: $active_count"
echo

# 5. Show what needs setup.py
echo "Libraries needing setup.py:"
echo "---"
needs_setup=""
for lib in opsvi-core opsvi-data opsvi-llm opsvi-fs opsvi-auth opsvi-visualization; do
    if [ -d "libs/$lib" ] && [ ! -f "libs/$lib/setup.py" ]; then
        echo "  - $lib"
        needs_setup="$needs_setup $lib"
    fi
done

if [ -z "$needs_setup" ]; then
    echo "  None - all core libraries have setup.py!"
else
    echo
    echo "Run this to add setup.py to core libraries:"
    echo "  python scripts/create_setup_py.py$needs_setup"
fi

echo
echo "✓ Cleanup complete!"
echo
echo "Summary:"
echo "  - Removed 4 empty stub libraries"
echo "  - Archived 7 unused libraries"
echo "  - $active_count libraries remain active"
echo
echo "Next steps:"
echo "  1. Add setup.py to core libraries (if needed)"
echo "  2. Run tests on remaining libraries"
echo "  3. Complete implementation of opsvi-interfaces"
