# Usage Examples & Tutorials

**Version**: 1.0.0
**Status**: ✅ **PRODUCTION READY**
**Date**: September 4, 2025

---

## 🎯 Overview

This comprehensive tutorial guide provides **practical examples, step-by-step walkthroughs, and real-world use cases** for the Unified Context System Phase 1. Whether you're a developer integrating with the MCP API, an operations engineer deploying the system, or a data analyst exploring project intelligence, this guide has you covered.

---

## 🚀 Quick Start Tutorial

### 1. First Steps: Getting Started

#### Prerequisites Check
```bash
# Verify system requirements
docker --version          # >= 20.10
docker-compose --version  # >= 2.0
curl --version            # Any recent version
jq --version              # For JSON parsing

# Check available resources
free -h                   # Should have 4GB+ RAM
df -h                     # Should have 10GB+ free disk space
```

#### Initial Setup (5 minutes)
```bash
# 1. Clone the repository
git clone https://github.com/your-org/unified-context-system.git
cd unified-context-system

# 2. Copy environment template
cp .env.example .env

# 3. Edit essential settings
nano .env
# Set at minimum:
# API_KEY=your-32-character-secure-api-key-here
# DB_PASSWORD=your-secure-database-password
# REDIS_PASSWORD=your-secure-redis-password

# 4. Start the system
docker-compose -f docker-compose.prod.yml up -d

# 5. Wait for startup (usually 60-90 seconds)
sleep 90

# 6. Verify everything is working
curl -k https://localhost/health
```

#### Your First API Call
```bash
# Test the system with a simple project summary call
curl -X POST https://localhost/api/tools/get_project_summary \
  -H "Authorization: Bearer your-api-key-from-env-file" \
  -H "Content-Type: application/json" \
  -d '{"include_metrics": true}' | jq '.'
```

**Expected Response:**
```json
{
  "project_name": "unified-context-system",
  "languages": {
    "Python": {"files": 45, "lines": 12500, "percentage": 65.2},
    "JavaScript": {"files": 23, "lines": 6800, "percentage": 34.8}
  },
  "structure": {
    "src/": {"type": "directory", "files": 68},
    "docs/": {"type": "directory", "files": 12}
  },
  "metrics": {
    "total_lines": 19300,
    "total_files": 68,
    "average_complexity": 6.8
  },
  "_metadata": {
    "execution_time_ms": 245,
    "cached": false,
    "timestamp": "2025-09-04T10:30:00Z"
  }
}
```

🎉 **Congratulations!** Your Unified Context System is now running and ready for use.

---

## 📚 Tutorial Categories

### 🔍 Discovery & Analysis Tutorials

#### Tutorial 1: Finding Files and Analyzing Code

**Scenario:** You're new to a project and want to understand its structure and key components.

**Step 1: Discover the project structure**
```bash
# Get overall project summary
curl -X POST https://localhost/api/tools/get_project_summary \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "include_metrics": true,
    "include_dependencies": true,
    "depth_limit": 2
  }' | jq '.structure'
```

**Step 2: Find important files**
```bash
# Find main entry points
curl -X POST https://localhost/api/tools/find_files \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "main.py|index.js|app.py|server.py",
    "max_results": 10
  }' | jq '.matches'

# Find configuration files
curl -X POST https://localhost/api/tools/find_files \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "*.yml|*.yaml|*.json|*.toml|*.ini",
    "exclude_patterns": ["node_modules/**", ".git/**"],
    "max_results": 20
  }' | jq '.matches'
```

**Step 3: Analyze a key file**
```bash
# Get detailed information about a main file
curl -X POST https://localhost/api/tools/get_file_info \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "include_content": false,
    "include_dependencies": true
  }' | jq '{
    file_path,
    language,
    size,
    elements: .elements[0:5],
    dependencies: .dependencies.imports[0:10]
  }'
```

**Step 4: Search for specific functionality**
```bash
# Search for authentication-related code
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication login user",
    "semantic_search": true,
    "file_types": ["py", "js", "ts"],
    "limit": 10
  }' | jq '.results[0:3]'
```

**What you've learned:**
- Project structure and organization
- Key files and entry points
- Code dependencies and imports
- Where authentication logic is implemented
- How to use semantic search to find related functionality

---

#### Tutorial 2: Code Quality Assessment

**Scenario:** You want to assess the quality of the codebase and identify areas for improvement.

**Step 1: Analyze code complexity**
```bash
# Find overly complex functions
curl -X POST https://localhost/api/tools/get_complexity \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "complexity_types": ["cyclomatic", "cognitive"],
    "threshold": 8.0,
    "include_suggestions": true
  }' | jq '{
    high_complexity_files: .files | length,
    worst_functions: [.files[0:3][] | {
      file: .file_path,
      function: .functions[0].name,
      complexity: .functions[0].cyclomatic_complexity
    }],
    project_stats: .project_statistics
  }'
```

**Step 2: Check test coverage**
```bash
# Analyze test coverage and quality
curl -X POST https://localhost/api/tools/get_tests \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "include_coverage": true,
    "framework_info": true
  }' | jq '{
    total_tests: .summary.total_tests,
    coverage: .coverage_report.overall_percentage,
    frameworks: .frameworks | keys,
    test_files: [.test_files[0:5][] | {
      path,
      test_count,
      coverage_percentage
    }]
  }'
```

**Step 3: Find technical debt**
```bash
# Find TODO items and technical debt
curl -X POST https://localhost/api/tools/get_todos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "todo_types": ["TODO", "FIXME", "HACK"],
    "include_context": true,
    "priority_analysis": true
  }' | jq '{
    total_todos: .todos | length,
    high_priority: [.todos[] | select(.priority == "high")],
    by_type: (.todos | group_by(.type) | map({type: .[0].type, count: length}))
  }'
```

**Step 4: Security assessment**
```bash
# Check for security issues
curl -X POST https://localhost/api/tools/get_security_issues \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "severity_filter": "medium",
    "include_suggestions": true,
    "scan_dependencies": true
  }' | jq '{
    total_issues: .issues | length,
    critical_issues: [.issues[] | select(.severity == "critical")],
    dependency_vulnerabilities: .dependency_vulnerabilities | length
  }'
```

**Quality Report Summary:**
```bash
# Generate a comprehensive quality report
cat > quality_report.sh << 'EOF'
#!/bin/bash
API_KEY="your-api-key"
BASE_URL="https://localhost/api/tools"

echo "# Code Quality Report - $(date)"
echo "=================================="

echo "## Complexity Analysis"
curl -s -X POST $BASE_URL/get_complexity \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 10}' | \
  jq -r '"High complexity files: " + (.files | length | tostring)'

echo "## Test Coverage"
curl -s -X POST $BASE_URL/get_tests \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_coverage": true}' | \
  jq -r '"Overall coverage: " + (.coverage_report.overall_percentage | tostring) + "%"'

echo "## Technical Debt"
curl -s -X POST $BASE_URL/get_todos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | \
  jq -r '"TODO items: " + (.todos | length | tostring)'

echo "## Security Issues"
curl -s -X POST $BASE_URL/get_security_issues \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | \
  jq -r '"Security issues: " + (.issues | length | tostring)'
EOF

chmod +x quality_report.sh
./quality_report.sh
```

---

### 🏗️ Architecture & Dependencies Tutorials

#### Tutorial 3: Understanding Project Architecture

**Scenario:** You need to understand how the system is architected and what its dependencies are.

**Step 1: Get architectural overview**
```bash
# Understand the overall architecture
curl -X POST https://localhost/api/tools/get_project_summary \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"depth_limit": 3}' | jq '{
    project_name,
    languages: (.languages | to_entries | map({
      language: .key,
      files: .value.files,
      percentage: .value.percentage
    })),
    structure: .structure | to_entries[0:10]
  }'
```

**Step 2: Analyze dependencies**
```bash
# Get comprehensive dependency analysis
curl -X POST https://localhost/api/tools/get_dependencies \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "include_dev": true,
    "include_transitive": false,
    "vulnerability_check": true,
    "outdated_check": true
  }' | jq '{
    summary: .summary,
    ecosystems: (.ecosystems | keys),
    vulnerabilities: .summary.total_vulnerabilities,
    outdated: .summary.total_outdated,
    recommendations: .recommendations[0:3]
  }'
```

**Step 3: Understand data models**
```bash
# Discover data models and entities
curl -X POST https://localhost/api/tools/get_data_models \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "include_relationships": true,
    "model_types": ["class", "interface", "schema"]
  }' | jq '{
    total_models: .models | length,
    model_types: (.models | group_by(.type) | map({
      type: .[0].type,
      count: length
    })),
    relationships: (.relationships | length)
  }'
```

**Step 4: Find API endpoints**
```bash
# Discover API endpoints
curl -X POST https://localhost/api/tools/get_api_endpoints \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "include_middleware": true,
    "include_auth": true
  }' | jq '{
    total_endpoints: .endpoints | length,
    methods: (.endpoints | group_by(.method) | map({
      method: .[0].method,
      count: length
    })),
    authenticated_endpoints: ([.endpoints[] | select(.requires_auth == true)] | length)
  }'
```

**Architecture Documentation Generator:**
```python
#!/usr/bin/env python3
import requests
import json
from typing import Dict, Any

class ArchitectureAnalyzer:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def call_tool(self, tool_name: str, params: Dict = None) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/tools/{tool_name}",
            headers=self.headers,
            json=params or {}
        )
        return response.json()

    def generate_architecture_doc(self):
        print("# Project Architecture Analysis")
        print("=" * 40)

        # Project overview
        summary = self.call_tool('get_project_summary', {
            'include_metrics': True,
            'include_dependencies': True
        })

        print(f"\n## Project: {summary['project_name']}")
        print(f"Total Files: {summary['metrics']['total_files']}")
        print(f"Total Lines: {summary['metrics']['total_lines']:,}")

        # Language breakdown
        print("\n## Language Distribution")
        for lang, stats in summary['languages'].items():
            print(f"- {lang}: {stats['files']} files ({stats['percentage']:.1f}%)")

        # Dependencies
        deps = self.call_tool('get_dependencies', {
            'include_dev': False,
            'vulnerability_check': True
        })

        print("\n## Dependencies")
        print(f"Total Ecosystems: {len(deps['ecosystems'])}")
        print(f"Security Vulnerabilities: {deps['summary']['total_vulnerabilities']}")
        print(f"Outdated Packages: {deps['summary']['total_outdated']}")

        # API endpoints
        try:
            endpoints = self.call_tool('get_api_endpoints')
            print(f"\n## API Endpoints")
            print(f"Total Endpoints: {len(endpoints['endpoints'])}")

            methods = {}
            for endpoint in endpoints['endpoints']:
                method = endpoint.get('method', 'unknown')
                methods[method] = methods.get(method, 0) + 1

            for method, count in methods.items():
                print(f"- {method}: {count}")
        except:
            print("\n## API Endpoints: Not detected")

# Usage
if __name__ == "__main__":
    analyzer = ArchitectureAnalyzer(
        base_url="https://localhost",
        api_key="your-api-key"
    )
    analyzer.generate_architecture_doc()
```

---

### 🔧 Development Workflow Tutorials

#### Tutorial 4: Code Review Assistant

**Scenario:** You're doing a code review and want to quickly understand changes and their impact.

**Step 1: Analyze recent changes**
```bash
# Get recent changes with impact analysis
curl -X POST https://localhost/api/tools/get_recent_changes \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "time_range": "7d",
    "include_authors": true,
    "change_analysis": true
  }' | jq '{
    total_changes: .changes | length,
    active_authors: .authors | length,
    most_changed_files: [.changes[0:5][] | {
      file: .file_path,
      changes: .change_count,
      author: .author
    }],
    change_patterns: .analysis.patterns
  }'
```

**Step 2: Check complexity impact**
```bash
# Find if recent changes introduced complexity
curl -X POST https://localhost/api/tools/get_complexity \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 8.0,
    "include_suggestions": true
  }' | jq '[.files[] | select(.functions[].last_modified > "2025-09-01")] | {
    recently_complex_files: length,
    functions: map(.functions[] | select(.complexity > 10) | {
      name,
      complexity: .cyclomatic_complexity,
      file: .file_path
    })
  }'
```

**Step 3: Validate test coverage for changes**
```bash
# Check if new code is tested
curl -X POST https://localhost/api/tools/get_tests \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_coverage": true}' | jq '{
    overall_coverage: .coverage_report.overall_percentage,
    uncovered_lines: .coverage_report.uncovered_lines,
    test_files: .summary.total_test_files
  }'
```

**Code Review Checklist Script:**
```bash
#!/bin/bash
# Automated code review checklist

API_KEY="your-api-key"
BASE_URL="https://localhost/api/tools"

echo "🔍 Code Review Analysis"
echo "======================="

# Check for high complexity in recent changes
echo "1. Complexity Analysis:"
COMPLEX_FILES=$(curl -s -X POST $BASE_URL/get_complexity \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 10}' | jq '.files | length')
echo "   Files with high complexity: $COMPLEX_FILES"

# Check test coverage
echo "2. Test Coverage:"
COVERAGE=$(curl -s -X POST $BASE_URL/get_tests \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.coverage_report.overall_percentage // 0')
echo "   Overall coverage: ${COVERAGE}%"

# Check for new security issues
echo "3. Security Issues:"
SECURITY_ISSUES=$(curl -s -X POST $BASE_URL/get_security_issues \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.issues | length')
echo "   Security issues found: $SECURITY_ISSUES"

# Check for TODOs introduced
echo "4. Technical Debt:"
TODO_COUNT=$(curl -s -X POST $BASE_URL/get_todos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.todos | length')
echo "   TODO items: $TODO_COUNT"

# Summary
echo ""
echo "✅ Code Review Summary:"
if [ "$COMPLEX_FILES" -eq 0 ] && [ "${COVERAGE%.*}" -gt 80 ] && [ "$SECURITY_ISSUES" -eq 0 ]; then
    echo "   Status: APPROVED ✅"
else
    echo "   Status: NEEDS ATTENTION ⚠️"
    [ "$COMPLEX_FILES" -gt 0 ] && echo "   - Address high complexity functions"
    [ "${COVERAGE%.*}" -lt 80 ] && echo "   - Improve test coverage"
    [ "$SECURITY_ISSUES" -gt 0 ] && echo "   - Fix security issues"
fi
```

---

#### Tutorial 5: Refactoring Assistant

**Scenario:** You want to refactor a complex part of the codebase and need to understand its dependencies and impact.

**Step 1: Find the target code**
```bash
# Find a specific function or class to refactor
curl -X POST https://localhost/api/tools/find_symbols \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol_name": "UserService",
    "symbol_type": "class",
    "exact_match": true
  }' | jq '{
    matches: [.symbols[] | {
      name,
      type,
      file_path,
      complexity: .complexity,
      line_start,
      line_end
    }]
  }'
```

**Step 2: Analyze dependencies and usage**
```bash
# Find where this code is used
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "UserService",
    "semantic_search": false,
    "file_types": ["py", "js", "ts"],
    "limit": 20
  }' | jq '{
    total_usages: .total_matches,
    usage_files: [.results[] | .file_path] | unique,
    usage_patterns: [.results[0:5][] | {
      file: .file_path,
      line: .line_number,
      context: .match_text
    }]
  }'
```

**Step 3: Generate call graph**
```bash
# Understand the call relationships
curl -X POST https://localhost/api/tools/get_call_graph \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_point": "UserService",
    "max_depth": 3,
    "include_external": false
  }' | jq '{
    nodes: .nodes | length,
    edges: .edges | length,
    direct_dependencies: [.edges[] | select(.source == "UserService") | .target],
    dependents: [.edges[] | select(.target == "UserService") | .source]
  }'
```

**Step 4: Check test coverage**
```bash
# Ensure the code is well tested before refactoring
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test.*UserService|UserService.*test",
    "file_types": ["py", "js", "ts"],
    "include_tests": true,
    "limit": 10
  }' | jq '{
    test_files: [.results[] | select(.file_path | test("test|spec")) | .file_path] | unique,
    test_coverage: .results | length
  }'
```

**Refactoring Impact Analysis:**
```python
#!/usr/bin/env python3
import requests
import json
from typing import Set, Dict, List

class RefactoringAnalyzer:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def call_tool(self, tool_name: str, params: Dict = None) -> Dict:
        response = requests.post(
            f"{self.base_url}/api/tools/{tool_name}",
            headers=self.headers,
            json=params or {}
        )
        return response.json()

    def analyze_refactoring_impact(self, symbol_name: str, symbol_type: str = "function"):
        print(f"🔍 Refactoring Impact Analysis: {symbol_name}")
        print("=" * 50)

        # Find the symbol
        symbols = self.call_tool('find_symbols', {
            'symbol_name': symbol_name,
            'symbol_type': symbol_type,
            'exact_match': True
        })

        if not symbols['symbols']:
            print(f"❌ Symbol '{symbol_name}' not found")
            return

        symbol = symbols['symbols'][0]
        print(f"📍 Location: {symbol['file_path']}:{symbol['line_start']}")
        print(f"📊 Complexity: {symbol.get('complexity', 'N/A')}")

        # Find usages
        usages = self.call_tool('search_code', {
            'query': symbol_name,
            'semantic_search': False,
            'limit': 50
        })

        usage_files = set()
        test_files = set()

        for result in usages['results']:
            file_path = result['file_path']
            if 'test' in file_path or 'spec' in file_path:
                test_files.add(file_path)
            else:
                usage_files.add(file_path)

        print(f"\n📊 Impact Analysis:")
        print(f"   • Used in {len(usage_files)} source files")
        print(f"   • Tested in {len(test_files)} test files")
        print(f"   • Total references: {usages['total_matches']}")

        # Risk assessment
        complexity = symbol.get('complexity', 0)
        risk_level = "LOW"
        if complexity > 10 or len(usage_files) > 10:
            risk_level = "HIGH"
        elif complexity > 5 or len(usage_files) > 5:
            risk_level = "MEDIUM"

        print(f"\n⚠️  Refactoring Risk: {risk_level}")

        if risk_level == "HIGH":
            print("   Recommendations:")
            print("   • Create comprehensive tests before refactoring")
            print("   • Consider incremental refactoring approach")
            print("   • Review all usage patterns carefully")

        # Show most important usage files
        if usage_files:
            print(f"\n📁 Key Files to Review:")
            for file in list(usage_files)[:5]:
                print(f"   • {file}")

# Usage
if __name__ == "__main__":
    analyzer = RefactoringAnalyzer(
        base_url="https://localhost",
        api_key="your-api-key"
    )

    # Example: analyze refactoring impact of UserService
    analyzer.analyze_refactoring_impact("UserService", "class")
```

---

### 🤖 AI Integration Tutorials

#### Tutorial 6: Semantic Code Search and Analysis

**Scenario:** You want to use AI-powered semantic search to find related code across your project.

**Step 1: Basic semantic search**
```bash
# Find authentication-related code using semantic search
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication and login security",
    "semantic_search": true,
    "file_types": ["py", "js", "ts"],
    "limit": 15
  }' | jq '{
    interpretation: .query_interpretation,
    semantic_matches: [.results[0:5][] | {
      file: .file_path,
      relevance: .relevance_score,
      match_type: .match_type,
      summary: .match_text[0:100]
    }]
  }'
```

**Step 2: Compare semantic vs text search**
```bash
# Text-based search
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "semantic_search": false,
    "limit": 10
  }' > text_search.json

# Semantic search
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "semantic_search": true,
    "limit": 10
  }' > semantic_search.json

# Compare results
echo "Text search found:" $(cat text_search.json | jq '.total_matches')
echo "Semantic search found:" $(cat semantic_search.json | jq '.total_matches')
```

**Step 3: Advanced semantic queries**
```bash
# Find error handling patterns
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "exception handling error recovery graceful failure",
    "semantic_search": true,
    "limit": 10
  }' | jq '{
    error_handling_patterns: [.results[0:5][] | {
      file: .file_path,
      pattern: .match_text,
      score: .relevance_score
    }]
  }'

# Find database interaction patterns
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database query sql orm transaction connection",
    "semantic_search": true,
    "limit": 10
  }' | jq '.results[0:3]'
```

**Intelligent Code Explorer:**
```python
#!/usr/bin/env python3
import requests
import json
from typing import List, Dict

class IntelligentCodeExplorer:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        response = requests.post(
            f"{self.base_url}/api/tools/search_code",
            headers=self.headers,
            json={
                'query': query,
                'semantic_search': True,
                'limit': limit
            }
        )
        return response.json()

    def explore_concept(self, concept: str):
        """Explore a programming concept across the codebase"""
        print(f"🔍 Exploring concept: '{concept}'")
        print("=" * 40)

        # Search for the concept
        results = self.semantic_search(concept, limit=20)

        print(f"Found {results['total_matches']} matches")
        print(f"Query interpretation: {results.get('query_interpretation', 'N/A')}")

        # Group by file type
        by_filetype = {}
        for result in results['results']:
            file_ext = result['file_path'].split('.')[-1]
            if file_ext not in by_filetype:
                by_filetype[file_ext] = []
            by_filetype[file_ext].append(result)

        print(f"\n📊 Distribution by file type:")
        for ext, matches in by_filetype.items():
            print(f"   • {ext}: {len(matches)} matches")

        # Show top matches
        print(f"\n🎯 Top 5 most relevant matches:")
        for i, result in enumerate(results['results'][:5], 1):
            print(f"\n{i}. {result['file_path']}:{result['line_number']}")
            print(f"   Relevance: {result['relevance_score']:.2f}")
            print(f"   Context: {result['match_text'][:100]}...")

    def find_similar_patterns(self, file_path: str, function_name: str):
        """Find similar code patterns to a specific function"""
        print(f"🔍 Finding patterns similar to {function_name} in {file_path}")
        print("=" * 60)

        # Get the function details first
        file_info = requests.post(
            f"{self.base_url}/api/tools/get_file_info",
            headers=self.headers,
            json={
                'file_path': file_path,
                'include_content': True
            }
        ).json()

        # Find the function
        target_function = None
        for element in file_info.get('elements', []):
            if element['name'] == function_name and element['type'] == 'function':
                target_function = element
                break

        if not target_function:
            print(f"❌ Function {function_name} not found")
            return

        # Create a semantic query based on function characteristics
        query = f"{function_name} similar function pattern logic"

        results = self.semantic_search(query, limit=15)

        # Filter out the original function
        similar_functions = [
            r for r in results['results']
            if not (r['file_path'] == file_path and function_name in r['match_text'])
        ]

        print(f"Found {len(similar_functions)} similar patterns:")

        for i, result in enumerate(similar_functions[:5], 1):
            print(f"\n{i}. {result['file_path']}:{result['line_number']}")
            print(f"   Similarity: {result['relevance_score']:.2f}")
            print(f"   Match: {result['match_text'][:80]}...")

# Usage examples
if __name__ == "__main__":
    explorer = IntelligentCodeExplorer(
        base_url="https://localhost",
        api_key="your-api-key"
    )

    # Explore authentication patterns
    explorer.explore_concept("user authentication security validation")

    print("\n" + "="*60 + "\n")

    # Find similar patterns to a specific function
    explorer.find_similar_patterns("src/auth/login.py", "validate_user")
```

---

### 📊 Data Analysis & Reporting Tutorials

#### Tutorial 7: Project Health Dashboard

**Scenario:** You want to create a comprehensive health dashboard for your project.

**Project Health Monitor Script:**
```python
#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

class ProjectHealthMonitor:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def call_tool(self, tool_name: str, params: Dict = None) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/tools/{tool_name}",
            headers=self.headers,
            json=params or {}
        )
        return response.json()

    def get_health_score(self) -> float:
        """Calculate overall project health score (0-100)"""
        scores = []

        # Test coverage score (0-40 points)
        try:
            tests = self.call_tool('get_tests', {'include_coverage': True})
            coverage = tests.get('coverage_report', {}).get('overall_percentage', 0)
            scores.append(min(coverage * 0.4, 40))
        except:
            scores.append(0)

        # Code quality score (0-30 points)
        try:
            complexity = self.call_tool('get_complexity', {'threshold': 10})
            complex_files = len(complexity.get('files', []))
            total_files = len(self.call_tool('find_files', {'pattern': '*'})['matches'])
            quality_score = max(0, 30 - (complex_files / max(total_files, 1)) * 30)
            scores.append(quality_score)
        except:
            scores.append(15)

        # Security score (0-20 points)
        try:
            security = self.call_tool('get_security_issues')
            issues = len(security.get('issues', []))
            security_score = max(0, 20 - issues * 2)
            scores.append(security_score)
        except:
            scores.append(10)

        # Documentation score (0-10 points)
        try:
            docs = self.call_tool('get_documentation')
            doc_coverage = docs.get('coverage_percentage', 0)
            scores.append(doc_coverage * 0.1)
        except:
            scores.append(5)

        return sum(scores)

    def generate_health_report(self):
        """Generate comprehensive health report"""
        print("🏥 PROJECT HEALTH DASHBOARD")
        print("=" * 50)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Overall health score
        health_score = self.get_health_score()
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 60:
            status = "🟠 FAIR"
        else:
            status = "🔴 POOR"

        print(f"\n📊 Overall Health Score: {health_score:.1f}/100 {status}")

        # Project overview
        try:
            summary = self.call_tool('get_project_summary', {
                'include_metrics': True,
                'include_dependencies': True
            })

            print(f"\n📁 Project Overview:")
            print(f"   • Total Files: {summary['metrics']['total_files']:,}")
            print(f"   • Total Lines: {summary['metrics']['total_lines']:,}")
            print(f"   • Languages: {len(summary['languages'])}")
            print(f"   • Average Complexity: {summary['metrics']['average_complexity']:.1f}")
        except Exception as e:
            print(f"   Error getting overview: {e}")

        # Test coverage
        try:
            tests = self.call_tool('get_tests', {'include_coverage': True})
            coverage = tests.get('coverage_report', {}).get('overall_percentage', 0)
            total_tests = tests.get('summary', {}).get('total_tests', 0)

            print(f"\n🧪 Testing:")
            print(f"   • Test Coverage: {coverage:.1f}%")
            print(f"   • Total Tests: {total_tests:,}")

            if coverage < 80:
                print("   ⚠️  Low test coverage - consider adding more tests")
        except:
            print(f"\n🧪 Testing: Unable to analyze")

        # Code quality
        try:
            complexity = self.call_tool('get_complexity', {'threshold': 10})
            complex_files = len(complexity.get('files', []))

            print(f"\n⚙️  Code Quality:")
            print(f"   • High Complexity Files: {complex_files}")

            if complex_files > 0:
                print("   ⚠️  Consider refactoring complex functions")
                worst = complexity['files'][0] if complexity['files'] else None
                if worst:
                    print(f"   • Worst file: {worst['file_path']}")
        except:
            print(f"\n⚙️  Code Quality: Unable to analyze")

        # Security
        try:
            security = self.call_tool('get_security_issues')
            issues = security.get('issues', [])
            critical = [i for i in issues if i.get('severity') == 'critical']

            print(f"\n🔒 Security:")
            print(f"   • Total Issues: {len(issues)}")
            print(f"   • Critical Issues: {len(critical)}")

            if critical:
                print("   🚨 Critical security issues found!")
        except:
            print(f"\n🔒 Security: Unable to analyze")

        # Dependencies
        try:
            deps = self.call_tool('get_dependencies', {
                'vulnerability_check': True,
                'outdated_check': True
            })

            print(f"\n📦 Dependencies:")
            print(f"   • Vulnerabilities: {deps['summary']['total_vulnerabilities']}")
            print(f"   • Outdated: {deps['summary']['total_outdated']}")
            print(f"   • Ecosystems: {deps['summary']['total_ecosystems']}")
        except:
            print(f"\n📦 Dependencies: Unable to analyze")

        # Technical debt
        try:
            todos = self.call_tool('get_todos')
            todo_items = todos.get('todos', [])
            high_priority = [t for t in todo_items if t.get('priority') == 'high']

            print(f"\n🔧 Technical Debt:")
            print(f"   • TODO Items: {len(todo_items)}")
            print(f"   • High Priority: {len(high_priority)}")
        except:
            print(f"\n🔧 Technical Debt: Unable to analyze")

        # Recommendations
        print(f"\n💡 Recommendations:")
        if health_score < 60:
            print("   • Project needs immediate attention")
            print("   • Focus on increasing test coverage")
            print("   • Address security vulnerabilities")
            print("   • Reduce code complexity")
        elif health_score < 80:
            print("   • Good foundation, room for improvement")
            print("   • Consider adding more tests")
            print("   • Review and refactor complex code")
        else:
            print("   • Excellent project health!")
            print("   • Continue current practices")
            print("   • Consider mentoring other projects")

# Usage
if __name__ == "__main__":
    monitor = ProjectHealthMonitor(
        base_url="https://localhost",
        api_key="your-api-key"
    )

    monitor.generate_health_report()
```

**Continuous Health Monitoring:**
```bash
#!/bin/bash
# Continuous project health monitoring script

API_KEY="your-api-key"
BASE_URL="https://localhost/api/tools"
REPORT_FILE="/tmp/project_health_$(date +%Y%m%d).json"

# Function to call API
call_api() {
    local tool=$1
    local params=${2:-'{}'}

    curl -s -X POST "$BASE_URL/$tool" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$params"
}

# Collect health metrics
echo "Collecting project health metrics..."

{
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","

    # Test coverage
    echo "  \"test_coverage\": $(call_api get_tests '{"include_coverage": true}' | jq '.coverage_report.overall_percentage // 0'),"

    # Complexity
    echo "  \"high_complexity_files\": $(call_api get_complexity '{"threshold": 10}' | jq '.files | length'),"

    # Security issues
    echo "  \"security_issues\": $(call_api get_security_issues | jq '.issues | length'),"

    # Technical debt
    echo "  \"todo_items\": $(call_api get_todos | jq '.todos | length'),"

    # Dependencies
    echo "  \"dependency_vulnerabilities\": $(call_api get_dependencies '{"vulnerability_check": true}' | jq '.summary.total_vulnerabilities')"

    echo "}"
} > $REPORT_FILE

echo "Health metrics saved to: $REPORT_FILE"

# Alert if critical issues found
CRITICAL_ISSUES=$(jq '.security_issues + .dependency_vulnerabilities' $REPORT_FILE)
if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    echo "🚨 ALERT: $CRITICAL_ISSUES critical issues found!"
    # Send notification (Slack, email, etc.)
fi
```

---

### 🛠️ Operations & Monitoring Tutorials

#### Tutorial 8: System Monitoring and Performance Analysis

**Scenario:** You want to monitor the system performance and set up automated alerts.

**Performance Monitoring Script:**
```python
#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List
import statistics

class PerformanceMonitor:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.metrics_history = []

    def measure_api_performance(self, tool_name: str, params: Dict = None) -> Dict:
        """Measure API call performance"""
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/tools/{tool_name}",
                headers=self.headers,
                json=params or {},
                timeout=30
            )

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms

            return {
                'tool': tool_name,
                'response_time_ms': response_time,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'timestamp': datetime.now().isoformat(),
                'cached': response.json().get('_metadata', {}).get('cached', False) if response.status_code == 200 else False
            }

        except requests.exceptions.Timeout:
            return {
                'tool': tool_name,
                'response_time_ms': 30000,  # timeout value
                'status_code': 408,
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': 'timeout'
            }
        except Exception as e:
            return {
                'tool': tool_name,
                'response_time_ms': -1,
                'status_code': 500,
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def run_performance_suite(self) -> Dict:
        """Run comprehensive performance test suite"""
        print("🚀 Running performance test suite...")

        test_cases = [
            ('get_project_summary', {}),
            ('find_files', {'pattern': '*.py', 'max_results': 10}),
            ('search_code', {'query': 'function', 'limit': 5}),
            ('get_file_info', {'file_path': 'README.md'}),
            ('get_complexity', {'threshold': 10}),
            ('get_tests', {'include_coverage': True}),
            ('get_dependencies', {'vulnerability_check': False}),
        ]

        results = []
        for tool, params in test_cases:
            print(f"  Testing {tool}...")
            result = self.measure_api_performance(tool, params)
            results.append(result)
            time.sleep(0.5)  # Brief pause between tests

        # Calculate statistics
        response_times = [r['response_time_ms'] for r in results if r['success']]
        success_rate = sum(1 for r in results if r['success']) / len(results)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'successful_tests': sum(1 for r in results if r['success']),
            'success_rate': success_rate,
            'avg_response_time_ms': statistics.mean(response_times) if response_times else -1,
            'min_response_time_ms': min(response_times) if response_times else -1,
            'max_response_time_ms': max(response_times) if response_times else -1,
            'p95_response_time_ms': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else (max(response_times) if response_times else -1),
            'detailed_results': results
        }

        self.metrics_history.append(summary)
        return summary

    def analyze_performance_trends(self):
        """Analyze performance trends over time"""
        if len(self.metrics_history) < 2:
            print("Not enough data for trend analysis")
            return

        print("\n📈 Performance Trend Analysis")
        print("=" * 40)

        recent = self.metrics_history[-5:]  # Last 5 measurements

        avg_response_times = [m['avg_response_time_ms'] for m in recent if m['avg_response_time_ms'] > 0]
        success_rates = [m['success_rate'] for m in recent]

        if len(avg_response_times) > 1:
            trend = "improving" if avg_response_times[-1] < avg_response_times[0] else "degrading"
            print(f"Response Time Trend: {trend}")
            print(f"Current Avg: {avg_response_times[-1]:.1f}ms")
            print(f"Previous Avg: {avg_response_times[0]:.1f}ms")

        if len(success_rates) > 1:
            reliability_trend = "improving" if success_rates[-1] > success_rates[0] else "degrading"
            print(f"Reliability Trend: {reliability_trend}")
            print(f"Current Success Rate: {success_rates[-1]*100:.1f}%")

    def check_health_endpoint(self) -> Dict:
        """Check system health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return {
                'healthy': response.status_code == 200,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'status': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }

    def generate_performance_report(self, save_to_file: bool = True):
        """Generate comprehensive performance report"""
        print("\n📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 50)

        # Run fresh performance tests
        current_metrics = self.run_performance_suite()

        # Health check
        health = self.check_health_endpoint()
        print(f"\n🏥 System Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
        if 'response_time_ms' in health:
            print(f"Health Check Response Time: {health['response_time_ms']:.1f}ms")

        # Performance summary
        print(f"\n⚡ Performance Summary:")
        print(f"   • Success Rate: {current_metrics['success_rate']*100:.1f}%")
        print(f"   • Average Response Time: {current_metrics['avg_response_time_ms']:.1f}ms")
        print(f"   • P95 Response Time: {current_metrics['p95_response_time_ms']:.1f}ms")
        print(f"   • Slowest Endpoint: {max(current_metrics['detailed_results'], key=lambda x: x['response_time_ms'] if x['success'] else 0)['tool']}")

        # Alerts
        alerts = []
        if current_metrics['success_rate'] < 0.95:
            alerts.append(f"Low success rate: {current_metrics['success_rate']*100:.1f}%")

        if current_metrics['avg_response_time_ms'] > 3000:
            alerts.append(f"High response time: {current_metrics['avg_response_time_ms']:.1f}ms")

        if alerts:
            print(f"\n🚨 Alerts:")
            for alert in alerts:
                print(f"   • {alert}")
        else:
            print(f"\n✅ All performance metrics within acceptable ranges")

        # Save to file
        if save_to_file:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'report_time': datetime.now().isoformat(),
                    'system_health': health,
                    'performance_metrics': current_metrics,
                    'alerts': alerts,
                    'metrics_history': self.metrics_history
                }, f, indent=2)
            print(f"\n💾 Report saved to: {filename}")

        return current_metrics

# Usage
if __name__ == "__main__":
    monitor = PerformanceMonitor(
        base_url="https://localhost",
        api_key="your-api-key"
    )

    # Run continuous monitoring
    for i in range(3):
        print(f"\n--- Monitoring Round {i+1} ---")
        monitor.generate_performance_report(save_to_file=(i==2))  # Save only last report

        if i < 2:  # Don't sleep after last iteration
            print("Waiting 30 seconds before next check...")
            time.sleep(30)

    # Analyze trends
    monitor.analyze_performance_trends()
```

**Automated Alerting System:**
```bash
#!/bin/bash
# Automated alerting system for critical issues

API_KEY="your-api-key"
BASE_URL="https://localhost"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
ALERT_THRESHOLD_RESPONSE_TIME=5000  # 5 seconds
ALERT_THRESHOLD_ERROR_RATE=0.05     # 5%

# Function to send Slack alert
send_slack_alert() {
    local message=$1
    local color=${2:-"warning"}

    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        --data "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"🚨 Project Context Alert\",
                \"text\": \"$message\",
                \"footer\": \"Monitoring System\",
                \"ts\": $(date +%s)
            }]
        }"
}

# Function to test API endpoint
test_endpoint() {
    local endpoint=$1
    local params=${2:-'{}'}

    local start_time=$(date +%s%3N)
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/api/tools/$endpoint" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$params")
    local end_time=$(date +%s%3N)

    local http_status=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    local response_time=$((end_time - start_time))

    echo "$http_status:$response_time"
}

# Main monitoring loop
echo "Starting automated monitoring and alerting..."

while true; do
    echo "Checking system health: $(date)"

    # Check health endpoint
    health_response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL/health")
    health_status=$(echo $health_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

    if [ "$health_status" != "200" ]; then
        send_slack_alert "🔴 System health check failed (HTTP $health_status)" "danger"
        echo "ALERT: Health check failed"
    fi

    # Test critical endpoints
    declare -a endpoints=("get_project_summary" "find_files" "search_code")
    error_count=0
    total_response_time=0

    for endpoint in "${endpoints[@]}"; do
        result=$(test_endpoint "$endpoint")
        status=$(echo $result | cut -d: -f1)
        response_time=$(echo $result | cut -d: -f2)

        if [ "$status" != "200" ]; then
            error_count=$((error_count + 1))
            echo "ERROR: $endpoint failed with status $status"
        fi

        if [ "$response_time" -gt "$ALERT_THRESHOLD_RESPONSE_TIME" ]; then
            send_slack_alert "⚠️ Slow response time detected: $endpoint took ${response_time}ms" "warning"
            echo "WARNING: Slow response time for $endpoint: ${response_time}ms"
        fi

        total_response_time=$((total_response_time + response_time))
    done

    # Calculate error rate
    total_endpoints=${#endpoints[@]}
    error_rate=$(echo "scale=2; $error_count / $total_endpoints" | bc)

    if (( $(echo "$error_rate > $ALERT_THRESHOLD_ERROR_RATE" | bc -l) )); then
        send_slack_alert "🔴 High error rate detected: ${error_rate}% of endpoints failing" "danger"
        echo "ALERT: High error rate: ${error_rate}%"
    fi

    # Average response time
    avg_response_time=$((total_response_time / total_endpoints))
    echo "Average response time: ${avg_response_time}ms, Error rate: ${error_rate}%"

    # Wait before next check
    sleep 300  # 5 minutes
done
```

---

## 🎓 Advanced Use Cases

### Use Case 1: Microservices Architecture Analysis

```python
# Analyze microservices architecture patterns
class MicroservicesAnalyzer:
    def analyze_service_boundaries(self):
        # Find API endpoints across services
        endpoints = self.call_tool('get_api_endpoints')

        # Analyze data models and dependencies
        models = self.call_tool('get_data_models')
        deps = self.call_tool('get_dependencies')

        # Generate service map
        return self.generate_service_map(endpoints, models, deps)
```

### Use Case 2: Legacy System Modernization

```python
# Identify modernization opportunities
class LegacyAnalyzer:
    def identify_modernization_targets(self):
        # Find high complexity code
        complexity = self.call_tool('get_complexity', {'threshold': 15})

        # Find outdated dependencies
        deps = self.call_tool('get_dependencies', {'outdated_check': True})

        # Find untested code
        tests = self.call_tool('get_tests')

        return self.prioritize_modernization(complexity, deps, tests)
```

### Use Case 3: Security Audit Automation

```python
# Automated security auditing
class SecurityAuditor:
    def comprehensive_security_audit(self):
        # Find security issues
        security = self.call_tool('get_security_issues')

        # Check dependency vulnerabilities
        deps = self.call_tool('get_dependencies', {'vulnerability_check': True})

        # Find authentication patterns
        auth_code = self.call_tool('search_code', {
            'query': 'authentication authorization security',
            'semantic_search': True
        })

        return self.generate_security_report(security, deps, auth_code)
```

---

## 📝 Best Practices & Tips

### 1. API Usage Best Practices

```bash
# Always use semantic search for concept exploration
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error handling patterns",
    "semantic_search": true,
    "limit": 20
  }'

# Use specific parameters for better results
curl -X POST https://localhost/api/tools/find_files \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "*.py",
    "exclude_patterns": ["test_*", "__pycache__/*", "*.pyc"],
    "max_results": 50
  }'
```

### 2. Performance Optimization Tips

- **Cache frequently accessed data** - The system automatically caches responses
- **Use batch operations** when possible
- **Limit result sets** for better performance
- **Monitor cache hit rates** and adjust TTL as needed

### 3. Error Handling Patterns

```python
import requests
from typing import Optional

def robust_api_call(tool_name: str, params: dict, max_retries: int = 3) -> Optional[dict]:
    """Robust API call with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"https://localhost/api/tools/{tool_name}",
                headers={'Authorization': 'Bearer your-api-key'},
                json=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"API error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    return None
```

### 4. Integration Patterns

```python
# Integrate with CI/CD pipelines
class CIPipeline:
    def quality_gate_check(self):
        # Run quality checks before deployment
        complexity = self.call_tool('get_complexity', {'threshold': 10})
        tests = self.call_tool('get_tests', {'include_coverage': True})
        security = self.call_tool('get_security_issues')

        # Fail build if quality gates not met
        if (len(complexity['files']) > 0 or
            tests['coverage_report']['overall_percentage'] < 80 or
            len(security['issues']) > 0):
            return False

        return True
```

---

## 🎯 Quick Reference

### Essential Commands Cheat Sheet

```bash
# System health
curl -k https://localhost/health

# Project overview
curl -X POST https://localhost/api/tools/get_project_summary \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_metrics": true}'

# Find files
curl -X POST https://localhost/api/tools/find_files \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.py", "max_results": 10}'

# Search code
curl -X POST https://localhost/api/tools/search_code \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "semantic_search": true}'

# Check complexity
curl -X POST https://localhost/api/tools/get_complexity \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 10}'

# Get tests
curl -X POST https://localhost/api/tools/get_tests \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_coverage": true}'
```

### Common Use Cases Summary

| Use Case | Primary Tools | Key Parameters |
|----------|---------------|----------------|
| **Code Discovery** | `find_files`, `search_code` | `pattern`, `semantic_search` |
| **Quality Assessment** | `get_complexity`, `get_tests` | `threshold`, `include_coverage` |
| **Security Audit** | `get_security_issues`, `get_dependencies` | `vulnerability_check` |
| **Architecture Analysis** | `get_project_summary`, `get_api_endpoints` | `include_dependencies` |
| **Performance Monitoring** | All tools with timing | Monitor `_metadata.execution_time_ms` |

---

## 📖 Conclusion

This comprehensive tutorial guide provides **practical, real-world examples** for leveraging the Unified Context System Phase 1. From basic discovery tasks to advanced analysis workflows, the examples demonstrate how to:

**✅ Get Started Quickly:** 5-minute setup with immediate results
**✅ Explore Code Intelligently:** Semantic search and analysis capabilities
**✅ Assess Project Quality:** Automated quality and security assessments
**✅ Monitor Performance:** Continuous monitoring and alerting
**✅ Integrate with Workflows:** CI/CD, code review, and development processes

The system is **ready for production use** with comprehensive API coverage, robust performance, and flexible integration options.

---

**Document Version**: 1.0.0
**Last Updated**: September 4, 2025
**Status**: ✅ Production Ready
