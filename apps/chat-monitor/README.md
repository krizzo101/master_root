# Enhanced Chat Monitor

**Next-generation agent collaboration observatory for Claude Code agent swarms.**

## What This Solves

Current chat monitors show basic tool usage but miss the critical collaboration layer:
- **Agent spawning** is visible, but **inter-agent communication** is hidden
- **File operations** are tracked, but **shared workspace coordination** is invisible
- **Task completion** is counted, but **handoff patterns** are unknown
- **Individual activity** is shown, but **collaboration networks** are obscured

## Key Features

### 🔍 Agent Collaboration Visibility
- **Communication Flow Tracking** - See who's talking to whom and how
- **Task Handoff Detection** - Identify when agents pass work between each other
- **Shared Workspace Monitoring** - Track multi-agent file coordination
- **Collaboration Network Visualization** - Understand agent relationship patterns

### 📊 Enhanced Intelligence
- **Smart Pattern Recognition** - Automatically detect collaboration events
- **Performance Metrics** - Measure collaboration efficiency and bottlenecks
- **Real-time Collaboration Status** - Live view of active agent coordination
- **Historical Analysis** - Track collaboration patterns over time

### 🎛️ Advanced Interface
- **Multi-panel Layout** - Statistics, communication flows, and activity logs
- **Dynamic Filtering** - Focus on specific agents or collaboration types
- **Interactive Controls** - Drill down into specific collaboration events
- **Export Capabilities** - Save collaboration data for analysis

## Architecture

```
apps/chat-monitor/
├── src/
│   ├── monitor.py          # Main monitoring engine
│   ├── collaboration/      # Collaboration detection logic
│   │   ├── detector.py     # Pattern detection algorithms
│   │   ├── network.py      # Agent network analysis
│   │   └── workspace.py    # Shared workspace tracking
│   ├── display/           # User interface components
│   │   ├── dashboard.py    # Main dashboard layout
│   │   ├── panels.py       # Individual display panels
│   │   └── formatting.py   # Output formatting utilities
│   └── analysis/          # Data analysis and insights
│       ├── metrics.py      # Performance calculations
│       ├── patterns.py     # Historical pattern analysis
│       └── export.py       # Data export functionality
├── bin/
│   └── chat-monitor       # Executable entry point
└── config/
    └── settings.py        # Configuration and defaults
```

## Usage

```bash
# Launch enhanced collaboration monitor
./apps/chat-monitor/bin/chat-monitor

# Focus on specific collaboration patterns
./apps/chat-monitor/bin/chat-monitor --focus communication
./apps/chat-monitor/bin/chat-monitor --focus workspace
./apps/chat-monitor/bin/chat-monitor --focus handoffs

# Historical analysis mode
./apps/chat-monitor/bin/chat-monitor --analyze-session <session_id>
```

## Design Principles

1. **Collaboration-First** - Built around making agent coordination visible
2. **Real-time Intelligence** - Show patterns as they emerge, not just raw events
3. **User-Centered** - Answer "what are my agents doing together?" immediately
4. **Performance-Aware** - Efficient monitoring that scales with agent count
5. **Integration-Ready** - Connects with existing collaboration infrastructure

## Replaces

This new monitor consolidates and supersedes:
- `chat-monitor` (current enhanced version)
- `chat-monitor-backup` (legacy multi-mode version)

Both will be archived after successful deployment.
