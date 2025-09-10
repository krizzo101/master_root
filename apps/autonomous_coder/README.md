# 🚀 Autonomous Coder v2.0

> Build any software from natural language descriptions using current 2024-2025 technology

## ✨ Features

- **🔍 Research-Driven**: Always uses current package versions (React 19, Vite 7, TypeScript 5.7, etc.)
- **🎯 Intelligent**: Automatically selects appropriate tech stack based on requirements
- **⚡ Fast**: Generates complete projects in seconds
- **🛡️ Robust**: Error recovery and validation built-in
- **📦 Modern**: Uses 2025 best practices and avoids deprecated tools

## 🎉 What's New in v2.0

- **Current Technology Database**: Built-in knowledge of 2024-2025 package versions
- **Multi-Project Support**: Can build web apps, REST APIs, CLI tools, libraries, and more
- **Smart Tech Selection**: Chooses the right stack for your project type
- **Production Ready**: Generated code follows best practices and includes proper configuration

## 🚀 Quick Start

```bash
# Build a TODO app
python3 main.py "Build a TODO app with modern web technologies"

# Create a REST API
python3 main.py "Create a REST API for user management" --output ./my-api

# Build a CLI tool
python3 main.py "Build a CLI tool for file processing"

# With custom configuration
python3 main.py "Build a dashboard" --config custom.yaml
```

## 📦 Installation

```bash
# Clone the repository
cd /home/opsvi/master_root/autonomous_coder

# Install dependencies (optional - only for YAML config support)
pip install -r requirements.txt

# Run the coder
python3 main.py "Your project description here"
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────┐
│         ORCHESTRATOR                 │
│    (Coordinates all modules)         │
└──┬────┬────┬────┬────┬────┬────┬───┘
   │    │    │    │    │    │    │
┌──▼──┐ │ ┌──▼──┐ │ ┌──▼──┐ │ ┌──▼──┐
│RESE │ │ │INTE │ │ │GENE │ │ │VALI │
│ARCH │ │ │LLIG │ │ │RATO │ │ │DATO │
│     │ │ │ENCE │ │ │R    │ │ │R    │
└─────┘ │ └─────┘ │ └─────┘ │ └─────┘
        │         │         │
   ┌────▼───┐ ┌──▼──┐ ┌───▼───┐
   │PLANNER │ │ERROR│ │STATE  │
   │        │ │RECOV│ │MANAGER│
   └────────┘ └─────┘ └───────┘
```

## 📚 Supported Project Types

### Web Applications
- **Simple Apps**: Basic HTML/CSS/JS with modern tooling
- **React Apps**: React 19 with Vite 7 and TypeScript 5.7
- **Vue Apps**: Vue 3.5 with Vite
- **Dashboards**: Full-featured with charts and data visualization

### Backend Services
- **REST APIs**: FastAPI or Express with current versions
- **Microservices**: Service-oriented architecture
- **GraphQL APIs**: Apollo Server with TypeScript

### Tools & Libraries
- **CLI Tools**: Python with Typer or Node.js
- **Libraries**: NPM packages or Python packages
- **Desktop Apps**: Electron or Tauri

## 🔧 Configuration

Create a `config.yaml` or `config.json`:

```yaml
research:
  cache_ttl: 86400
  use_cache: true

generation:
  default_language: typescript
  documentation: true
  tests: true

validation:
  strict_mode: true
  security_scan: true
```

## 📊 Current Technology Stack (2025)

### Frontend
- **React**: 19.1.1 (Latest with Server Components)
- **Vue**: 3.5.13 (Composition API)
- **Vite**: 7.1.1 (Fastest bundler)
- **TypeScript**: 5.7.2 (Latest type safety)

### Backend
- **Node.js**: 22.13.0 (Current)
- **FastAPI**: 0.117.1 (Python)
- **Express**: 4.21.2 (Node.js)
- **Django**: 5.1.5 (Python)

### Databases
- **PostgreSQL**: 17.2
- **MongoDB**: 8.0.0
- **Redis**: 7.4.2
- **SQLite**: 3.48.0

### Tools
- **pnpm**: 9.16.1 (Fastest package manager)
- **Bun**: 1.2.0 (All-in-one toolkit)
- **Docker**: 25.0.4
- **Playwright**: 1.50.0 (Testing)

## ⚠️ Deprecated Technologies Avoided

- ❌ Create React App (Use Vite instead)
- ❌ Webpack for simple projects (Use Vite)
- ❌ Class components in React
- ❌ Moment.js (Use date-fns or Temporal)
- ❌ jQuery for new projects
- ❌ CommonJS modules (Use ES modules)

## 🎯 Examples

### TODO App
```bash
python3 main.py "Build a TODO app with drag and drop"
# Creates: Vite + React 19 + TypeScript + Modern CSS
```

### REST API
```bash
python3 main.py "Create a REST API for blog posts with auth"
# Creates: FastAPI + SQLAlchemy + JWT auth + PostgreSQL
```

### CLI Tool
```bash
python3 main.py "Build a CLI for batch image processing"
# Creates: Python + Typer + Rich + Pillow
```

### Dashboard
```bash
python3 main.py "Create an admin dashboard with charts"
# Creates: Next.js 15 + React 19 + Tailwind + Recharts
```

## 📈 Performance

- **Simple App**: < 1 second
- **Web App**: < 2 seconds
- **REST API**: < 2 seconds
- **Complex Project**: < 5 seconds

## 🔍 How It Works

1. **Understanding**: Analyzes your natural language request
2. **Research**: Checks current versions and best practices
3. **Planning**: Selects appropriate technology stack
4. **Generation**: Creates all project files
5. **Validation**: Ensures everything is correct

## 🤝 Contributing

The system is designed to be extensible:

1. **Add Templates**: Place in `templates/` directory
2. **Update Versions**: Edit `CURRENT_VERSIONS` in `research_engine.py`
3. **Add Project Types**: Extend `ProjectType` enum
4. **Custom Generators**: Inherit from `BaseModule`

## 📝 License

MIT

## 🙏 Acknowledgments

Built with modern AI-driven development practices using:
- Claude Code for autonomous capabilities
- MCP (Model Context Protocol) for tool integration
- Current 2024-2025 web technologies

---

**Built by Autonomous Coder** - *Building the future, one project at a time* 🚀