# Chat Logs Analytics Dashboard

## 🚀 Access the Dashboard

The web interface is now running at: **http://localhost:5000**

## 📊 Available Reports

### 1. **Overview Dashboard**
- Total sessions, messages, tool calls, and files touched
- Message distribution (User vs Assistant)
- Activity timeline visualization
- Real-time statistics from 558 parsed JSONL files

### 2. **Developer Productivity Report**
- **Hourly Activity Pattern**: Identify peak productivity hours
- **Files Per Session**: Track coding intensity
- **Task Management Trends**: TodoWrite usage patterns
- **Session Efficiency Metrics**: Time vs output analysis

### 3. **Tool Utilization Analysis**
- **Top Tools Usage**: Most frequently used tools ranked
- **Tool Categories**: Breakdown by function (File Ops, Shell, Web, etc.)
- **Tool Sequences**: Common tool chains and workflows
- **Success/Error Rates**: Tool reliability metrics

### 4. **File Operations Intelligence**
- **File Type Distribution**: Python, JS/TS, Markdown, JSON, etc.
- **Directory Heat Map**: Most active project areas
- **Hot Files Table**: Most frequently edited files with operation breakdown
- **Change Patterns**: Read/Write/Edit ratios

### 5. **Cognitive Patterns Analysis**
- **Thinking Tool Usage**: Metacognitive and sequential thinking trends
- **Session Complexity**: Node count vs tool diversity scatter plot
- **Problem-Solving Patterns**: Iteration and decision reversal tracking
- **Planning vs Execution Ratios**: Strategic insights

### 6. **Timeline & History**
- **Daily Activity Trends**: Long-term patterns
- **Recent Sessions**: Detailed session information
- **Historical Analysis**: Activity over time
- **Session Duration Metrics**: Start/end times and durations

## 🔍 Search Capabilities

The dashboard includes a powerful search feature that can:
- Search across all messages
- Find specific file operations
- Locate sessions by content
- Filter by date ranges

## 📈 Key Insights from Your Data

Based on the analysis of **41,137 nodes** across **530 sessions**:

### Top Tools (by usage):
1. **Bash**: 6,286 calls (system commands dominant)
2. **TodoWrite**: 3,138 calls (heavy task tracking)
3. **Read**: 2,462 calls (file exploration)
4. **Edit**: 1,726 calls (code modification)
5. **Write**: 1,582 calls (new file creation)

### File Activity:
- **1,998 unique files** touched
- **11,299 total file operations**
- Heavy focus on Python files
- UNIFIED_CONTEXT_SYSTEM.md is a hot spot

### Cognitive Tools:
- Metacognitive thinking: 726 uses
- Sequential thinking: 396 uses
- Shows structured problem-solving approach

## 🛠 Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with optimized indexes
- **Frontend**: Tailwind CSS + Chart.js
- **Data**: 558 JSONL files parsed with custom taxonomy
- **Performance**: Sub-second query response times

## 📁 File Structure

```
/home/opsvi/master_root/
├── chat_logs.db              # SQLite database (main data store)
├── libs/
│   ├── chat_taxonomy_parser.py    # JSONL parser
│   ├── chat_report_generator.py   # Report generation
│   ├── chat_logs_web.py          # Flask web application
│   ├── ingest_chat_logs_sqlite.py # Ingestion script
│   └── templates/
│       └── dashboard.html        # Interactive dashboard
```

## 🔄 Updating Data

To refresh with new chat logs:
```bash
cd /home/opsvi/master_root/libs
python ingest_chat_logs_sqlite.py
```

## 🎯 Use Cases

1. **Performance Optimization**: Identify bottlenecks and inefficient patterns
2. **Tool Selection**: Understand which tools are most effective
3. **Code Hot Spots**: Find frequently modified areas needing refactoring
4. **Learning Patterns**: Track improvement over time
5. **Error Analysis**: Identify and prevent recurring issues
6. **Workflow Optimization**: Discover optimal tool sequences

## 🌟 Features

- **Real-time Updates**: Live data refresh
- **Interactive Charts**: Zoom, pan, and filter
- **Responsive Design**: Works on all screen sizes
- **Export Capability**: Download reports as JSON
- **Search & Filter**: Find specific patterns quickly
- **Multiple Views**: 6 specialized report categories

The dashboard provides comprehensive insights into your development patterns, helping optimize workflows and identify areas for improvement.
