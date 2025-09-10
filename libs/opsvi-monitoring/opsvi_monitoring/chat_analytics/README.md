# Chat Analytics Module

Comprehensive analytics system for Claude chat logs within the OPSVI monitoring framework.

## Structure

```
chat_analytics/
├── ingestion/          # Data ingestion from JSONL files
│   └── sqlite_ingester.py
├── analysis/           # Analytics and metrics
│   ├── response_analyzer.py
│   ├── response_history.py
│   └── session_analyzer.py
├── web/               # Web dashboard
│   └── dashboard.py
├── templates/         # HTML templates
│   └── dashboard.html
├── static/           # Static assets (CSS, JS)
└── cli.py           # Command-line interface
```

## Database

- **Location**: `/home/opsvi/master_root/chat_logs.db`
- **Type**: SQLite
- **Source**: `~/.claude/projects/-home-opsvi-master-root/*.jsonl`

## Usage

### CLI Commands

```bash
# Navigate to module directory
cd /home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics

# Ingest chat logs
python cli.py ingest

# Run analysis
python cli.py analyze

# Start dashboard (default port: 5001)
python cli.py dashboard

# With options
python cli.py dashboard --port 8080 --host localhost --debug

# Generate AI summaries
python cli.py summary
```

### Python API

```python
from opsvi_monitoring.chat_analytics import ResponseTimeAnalyzer

# Analyze response times
analyzer = ResponseTimeAnalyzer()
metrics = analyzer.get_response_times()
print(f"Average: {metrics['average']}")
analyzer.close()
```

### Web Dashboard

Access at `http://localhost:5001` after starting with:
```bash
python cli.py dashboard
```

## Features

- **Response Time Analysis**: Average, median, shortest, longest response times
- **Activity Patterns**: Active vs dead space timeline analysis
- **Session Summaries**: AI-powered session descriptions using Claude
- **Tool Usage Metrics**: Comprehensive tool usage statistics
- **Interactive Dashboard**: Real-time charts and visualizations
- **Cognitive Analysis**: Thinking and planning pattern insights

## API Endpoints

- `GET /api/overview` - Overall statistics
- `GET /api/response-times` - Response time metrics
- `GET /api/activity-summary` - Activity analysis
- `GET /api/sessions/summaries` - Session summaries
- `POST /api/cache/clear` - Clear cache

## Dependencies

- Flask (web framework)
- SQLite3 (database)
- Chart.js (visualizations)
- Claude CLI (AI summaries, optional)
