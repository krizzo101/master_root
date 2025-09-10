# Project Context MCP Server - User Guide

**Version**: 0.1.0
**For Developers and Teams**

## 🌟 Overview

The Project Context MCP Server provides intelligent access to your project's codebase through 21 specialized tools. It analyzes code structure, dependencies, documentation, and provides actionable insights to improve development velocity and code quality.

### Key Benefits

- **🔍 Intelligent Code Discovery**: Find files, symbols, and patterns across large codebases
- **📊 Project Analytics**: Get comprehensive metrics on code quality, complexity, and health
- **🏗️ Architecture Insights**: Understand dependencies, call graphs, and system design
- **⚡ Performance Optimized**: Redis caching and PostgreSQL indexing for fast queries
- **🔒 Production Ready**: Enterprise security, monitoring, and deployment automation

## 🚀 Quick Start

### 1. Authentication

All API requests require an API key:

```bash
export API_KEY="your-api-key-here"
```

### 2. Basic Usage

```bash
# Get project overview
curl -X POST https://api.your-domain.com/tools/get_project_summary \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_metrics": true}'

# Search for files
curl -X POST https://api.your-domain.com/tools/find_files \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.tsx", "max_results": 20}'
```

### 3. Python SDK Example

```python
import requests

class ProjectContextClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_project_summary(self):
        response = requests.post(
            f"{self.base_url}/tools/get_project_summary",
            headers=self.headers,
            json={"include_metrics": True}
        )
        return response.json()

# Usage
client = ProjectContextClient("https://api.your-domain.com", "your-api-key")
summary = client.get_project_summary()
print(f"Project has {summary['metrics']['total_files']} files")
```

## 🛠️ Tool Categories

### 🔍 Discovery Tools

#### get_file_info
Get comprehensive information about a specific file.

**Use Cases:**
- Code review preparation
- Understanding file dependencies
- Analyzing file complexity

```bash
curl -X POST $BASE_URL/tools/get_file_info \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"file_path": "src/components/UserProfile.tsx"}'
```

**Response Preview:**
```json
{
  "file_path": "src/components/UserProfile.tsx",
  "language": "typescript",
  "size": 2048,
  "elements": [
    {
      "name": "UserProfile",
      "type": "component",
      "complexity": 6.2,
      "line_start": 10,
      "line_end": 85
    }
  ],
  "dependencies": {
    "imports": ["react", "axios"],
    "external": ["@types/react"]
  }
}
```

#### find_files
Search for files by pattern, type, or criteria.

**Use Cases:**
- Finding specific components
- Identifying configuration files
- Locating test files

```bash
# Find all TypeScript React components
curl -X POST $BASE_URL/tools/find_files \
  -d '{"pattern": "*Component.tsx", "max_results": 50}'

# Find configuration files
curl -X POST $BASE_URL/tools/find_files \
  -d '{"pattern": "config.*", "file_type": "json"}'
```

#### find_symbols
Locate functions, classes, variables across the codebase.

**Use Cases:**
- Finding function definitions
- Locating class usage
- Identifying variable references

```bash
# Find all authentication-related functions
curl -X POST $BASE_URL/tools/find_symbols \
  -d '{"symbol_name": "auth", "symbol_type": "function"}'

# Find specific class
curl -X POST $BASE_URL/tools/find_symbols \
  -d '{"symbol_name": "UserService", "exact_match": true}'
```

#### search_code
Semantic and text-based code search.

**Use Cases:**
- Finding specific implementations
- Searching for patterns
- Code exploration

```bash
# Search for async/await patterns
curl -X POST $BASE_URL/tools/search_code \
  -d '{"query": "async function", "semantic_search": true}'

# Search in specific file types
curl -X POST $BASE_URL/tools/search_code \
  -d '{"query": "API endpoint", "file_types": ["ts", "js"]}'
```

### 🏗️ Architecture Tools

#### get_project_summary
High-level project overview with metrics and structure.

**Use Cases:**
- Project health assessment
- Onboarding new developers
- Architecture documentation

```json
{
  "include_metrics": true,
  "include_dependencies": true,
  "depth_limit": 3
}
```

#### get_dependencies
Analyze project dependencies and their relationships.

**Use Cases:**
- Security auditing
- Dependency optimization
- License compliance

```json
{
  "include_dev": false,
  "vulnerability_check": true,
  "outdated_check": true
}
```

#### get_call_graph
Generate function call relationships and dependency graphs.

**Use Cases:**
- Understanding code flow
- Impact analysis
- Refactoring planning

```json
{
  "entry_point": "src/main.ts",
  "max_depth": 5,
  "format": "json"
}
```

### 📊 Quality Tools

#### get_quality_metrics
Calculate comprehensive code quality scores.

**Use Cases:**
- Code review metrics
- Technical debt assessment
- Quality tracking over time

```bash
curl -X POST $BASE_URL/tools/get_quality_metrics \
  -d '{"include_trends": true, "benchmark_comparison": true}'
```

#### get_complexity
Analyze code complexity using multiple metrics.

**Use Cases:**
- Identifying refactoring candidates
- Code review prioritization
- Maintainability assessment

```json
{
  "complexity_types": ["cyclomatic", "cognitive"],
  "threshold": 10,
  "include_suggestions": true
}
```

#### get_security_issues
Identify potential security vulnerabilities.

**Use Cases:**
- Security auditing
- Vulnerability management
- Compliance checking

```json
{
  "severity_filter": "medium",
  "include_suggestions": true,
  "scan_dependencies": true
}
```

### 🧪 Testing Tools

#### get_tests
Analyze test coverage and testing patterns.

**Use Cases:**
- Test coverage analysis
- Testing strategy review
- CI/CD optimization

```json
{
  "test_type": "unit",
  "include_coverage": true,
  "framework_info": true
}
```

### 📚 Documentation Tools

#### get_documentation
Extract and analyze project documentation.

**Use Cases:**
- Documentation audit
- Knowledge base creation
- Onboarding material generation

```json
{
  "doc_types": ["readme", "api", "inline"],
  "quality_analysis": true
}
```

### 📝 Maintenance Tools

#### get_todos
Find TODO comments and technical debt markers.

**Use Cases:**
- Technical debt tracking
- Sprint planning
- Code cleanup prioritization

```json
{
  "todo_types": ["TODO", "FIXME", "HACK"],
  "priority_analysis": true
}
```

#### get_recent_changes
Analyze recent code modifications and patterns.

**Use Cases:**
- Change impact analysis
- Developer activity tracking
- Release planning

```json
{
  "time_range": "7d",
  "include_authors": true,
  "change_analysis": true
}
```

## 🔧 Advanced Usage

### Batch Operations

```python
# Process multiple files efficiently
files = ["src/auth.ts", "src/database.ts", "src/api.ts"]
results = []

for file_path in files:
    result = client.get_file_info(file_path)
    results.append(result)

# Analyze all results together
total_complexity = sum(r['metrics']['complexity'] for r in results)
```

### Filtering and Pagination

```python
# Get large file lists with pagination
def get_all_typescript_files():
    all_files = []
    offset = 0
    limit = 100

    while True:
        response = client.find_files({
            "pattern": "*.ts",
            "max_results": limit,
            "offset": offset
        })

        files = response.get("matches", [])
        if not files:
            break

        all_files.extend(files)
        offset += limit

    return all_files
```

### Caching Strategies

```python
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_project_summary():
    """Cache expensive project summary calls"""
    return client.get_project_summary()

# Use cached version for frequent access
summary = cached_project_summary()
```

## 📈 Use Case Examples

### 1. Code Review Automation

```python
def automated_code_review(file_paths):
    """Automated code review using Project Context tools"""

    review_results = {
        "files_analyzed": len(file_paths),
        "high_complexity": [],
        "security_issues": [],
        "missing_tests": [],
        "todo_items": []
    }

    for file_path in file_paths:
        # Get file information
        file_info = client.get_file_info(file_path)

        # Check complexity
        complexity = client.get_complexity(file_path)
        if complexity["average_complexity"] > 10:
            review_results["high_complexity"].append({
                "file": file_path,
                "complexity": complexity["average_complexity"]
            })

        # Check for security issues
        security = client.get_security_issues(file_path)
        if security["issues"]:
            review_results["security_issues"].extend(security["issues"])

        # Find TODOs
        todos = client.get_todos(file_path)
        review_results["todo_items"].extend(todos["items"])

    return review_results

# Usage
changed_files = ["src/auth.ts", "src/api/users.ts"]
review = automated_code_review(changed_files)
print(f"Found {len(review['security_issues'])} security issues")
```

### 2. Architecture Documentation

```python
def generate_architecture_doc():
    """Generate architecture documentation automatically"""

    # Get project overview
    summary = client.get_project_summary()

    # Get API endpoints
    endpoints = client.get_api_endpoints()

    # Get data models
    models = client.get_data_models()

    # Get dependencies
    deps = client.get_dependencies()

    doc = {
        "title": f"Architecture Overview - {summary['project_name']}",
        "overview": {
            "languages": summary["languages"],
            "total_files": summary["metrics"]["total_files"],
            "lines_of_code": summary["metrics"]["total_lines"]
        },
        "api_endpoints": len(endpoints["endpoints"]),
        "data_models": len(models["models"]),
        "external_dependencies": len(deps["external"])
    }

    return doc
```

### 3. Technical Debt Analysis

```python
def analyze_technical_debt():
    """Comprehensive technical debt analysis"""

    debt_report = {
        "high_complexity_files": [],
        "security_vulnerabilities": [],
        "outdated_dependencies": [],
        "missing_documentation": [],
        "test_coverage_gaps": []
    }

    # Find high complexity areas
    complexity = client.get_complexity(threshold=15)
    debt_report["high_complexity_files"] = complexity["high_complexity_items"]

    # Security issues
    security = client.get_security_issues()
    debt_report["security_vulnerabilities"] = security["issues"]

    # Dependency analysis
    deps = client.get_dependencies(outdated_check=True)
    debt_report["outdated_dependencies"] = deps["outdated"]

    # Documentation gaps
    docs = client.get_documentation(quality_analysis=True)
    debt_report["missing_documentation"] = docs["missing_docs"]

    # Test coverage
    tests = client.get_tests(include_coverage=True)
    low_coverage = [f for f in tests["coverage"] if f["percentage"] < 70]
    debt_report["test_coverage_gaps"] = low_coverage

    return debt_report
```

### 4. Onboarding Assistant

```python
def generate_onboarding_guide(new_developer_role):
    """Generate personalized onboarding guide"""

    # Get project structure
    summary = client.get_project_summary()

    # Find entry points
    entry_points = client.get_entry_points()

    # Get documentation
    docs = client.get_documentation()

    guide = {
        "welcome": f"Welcome to {summary['project_name']}!",
        "start_here": entry_points["main_files"],
        "key_concepts": [],
        "recommended_reading": docs["api_docs"],
        "first_tasks": []
    }

    # Role-specific recommendations
    if new_developer_role == "frontend":
        frontend_files = client.find_files(pattern="*.tsx")
        guide["start_here"] = frontend_files["matches"][:5]
        guide["first_tasks"] = [
            "Review component structure",
            "Understand state management",
            "Check styling patterns"
        ]

    elif new_developer_role == "backend":
        api_endpoints = client.get_api_endpoints()
        guide["start_here"] = api_endpoints["main_files"]
        guide["first_tasks"] = [
            "Review API architecture",
            "Understand database schema",
            "Check authentication flow"
        ]

    return guide
```

## 🔧 Integration Examples

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
name: Code Quality Check
on: [pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run Project Context Analysis
        run: |
          # Get changed files
          CHANGED_FILES=$(git diff --name-only HEAD~1)

          # Analyze each changed file
          for file in $CHANGED_FILES; do
            curl -X POST ${{ secrets.PROJECT_CONTEXT_URL }}/tools/get_complexity \
              -H "Authorization: Bearer ${{ secrets.API_KEY }}" \
              -d "{\"file_path\": \"$file\"}" \
              >> complexity_report.json
          done

      - name: Check complexity threshold
        run: |
          python scripts/check_complexity.py complexity_report.json
```

### IDE Integration

```javascript
// VSCode Extension example
const vscode = require('vscode');
const axios = require('axios');

class ProjectContextProvider {
    constructor() {
        this.apiKey = vscode.workspace.getConfiguration().get('projectContext.apiKey');
        this.baseUrl = vscode.workspace.getConfiguration().get('projectContext.url');
    }

    async getFileInfo(filePath) {
        try {
            const response = await axios.post(`${this.baseUrl}/tools/get_file_info`, {
                file_path: filePath
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            vscode.window.showErrorMessage(`Project Context error: ${error.message}`);
        }
    }

    async showComplexityWarnings() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const filePath = editor.document.fileName;
        const fileInfo = await this.getFileInfo(filePath);

        if (fileInfo.metrics && fileInfo.metrics.complexity > 10) {
            vscode.window.showWarningMessage(
                `High complexity detected: ${fileInfo.metrics.complexity}`
            );
        }
    }
}
```

### Slack Bot Integration

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class ProjectContextSlackBot:
    def __init__(self, slack_token, project_context_client):
        self.slack_client = WebClient(token=slack_token)
        self.pc_client = project_context_client

    def handle_project_summary(self, channel, user):
        """Handle !project-summary command"""
        try:
            summary = self.pc_client.get_project_summary()

            message = f"""
            📊 *Project Summary*
            • Files: {summary['metrics']['total_files']}
            • Languages: {', '.join(summary['languages'].keys())}
            • Lines of Code: {summary['metrics']['total_lines']}
            • Test Coverage: {summary['metrics']['test_coverage']}%
            """

            self.slack_client.chat_postMessage(
                channel=channel,
                text=message
            )

        except Exception as e:
            self.slack_client.chat_postMessage(
                channel=channel,
                text=f"❌ Error getting project summary: {str(e)}"
            )

    def handle_file_search(self, channel, pattern):
        """Handle !find-files pattern command"""
        files = self.pc_client.find_files(pattern=pattern, max_results=10)

        if files['matches']:
            file_list = '\n'.join([f"• `{f['path']}`" for f in files['matches']])
            message = f"🔍 *Files matching '{pattern}'*:\n{file_list}"
        else:
            message = f"No files found matching '{pattern}'"

        self.slack_client.chat_postMessage(channel=channel, text=message)
```

## 🎯 Best Practices

### Performance Optimization

1. **Use Caching**: Enable Redis caching for frequently accessed data
2. **Batch Requests**: Process multiple files in single requests when possible
3. **Filter Results**: Use appropriate filters to reduce response sizes
4. **Pagination**: Implement pagination for large result sets

### Error Handling

```python
def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with retries"""
    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limited(max_per_minute=60):
    """Decorator for rate limiting API calls"""
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limited(max_per_minute=100)
def get_file_info(file_path):
    return client.get_file_info(file_path)
```

### Security

1. **API Key Security**: Store API keys in environment variables
2. **HTTPS Only**: Always use HTTPS endpoints in production
3. **Input Validation**: Validate file paths and parameters
4. **Access Control**: Implement proper authentication and authorization

## 🆘 Troubleshooting

### Common Issues

**Issue**: "Authentication failed"
**Solution**:
```bash
# Verify API key format
echo $API_KEY | wc -c  # Should be 32+ characters

# Test authentication
curl -H "Authorization: Bearer $API_KEY" $BASE_URL/health
```

**Issue**: "File not found"
**Solution**:
```python
# Check if intelligence data exists for the file
files = client.find_files(pattern=os.path.basename(file_path))
if not files['matches']:
    print("File not in intelligence database - may need indexing")
```

**Issue**: "Request timeout"
**Solution**:
```python
# Increase timeout and add retries
session = requests.Session()
session.timeout = 60  # 60 seconds
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount('https://', adapter)
```

### Getting Help

- **Documentation**: [Full API Reference](API_REFERENCE.md)
- **GitHub Issues**: https://github.com/your-org/project-context/issues
- **Community Discord**: https://discord.gg/your-server
- **Support Email**: support@your-domain.com

## 🚀 What's Next?

- Explore advanced [API endpoints](API_REFERENCE.md)
- Set up [monitoring dashboards](DEPLOYMENT_GUIDE.md#monitoring-setup)
- Join our [community Discord](https://discord.gg/your-server)
- Contribute to the [open source project](https://github.com/your-org/project-context)

---

*Happy coding! The Project Context team is here to help you build better software faster.*
