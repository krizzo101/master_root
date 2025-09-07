"""Code Generator - Generates project files from templates and requirements."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import textwrap

from core.base import BaseModule, BuildRequest, Requirements, ProjectType


class Generator(BaseModule):
    """Generates code files and project structures."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the generator."""
        super().__init__(config)
        self.templates_dir = Path("templates")
        self.generated_files = []
    
    def generate_project(self, 
                        request: BuildRequest,
                        requirements: Requirements,
                        tech_stack: Dict[str, str]) -> Dict[str, Any]:
        """Generate a complete project based on requirements."""
        self.log(f"Generating project: {requirements.project_type.value}")
        
        # Create project directory
        project_path = request.output_path / self._generate_project_name(request.description)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Generate based on project type
        if requirements.project_type == ProjectType.SIMPLE_APP:
            self._generate_simple_app(project_path, tech_stack)
        elif requirements.project_type == ProjectType.WEB_APP:
            self._generate_web_app(project_path, tech_stack)
        elif requirements.project_type == ProjectType.REST_API:
            self._generate_rest_api(project_path, tech_stack)
        elif requirements.project_type == ProjectType.CLI_TOOL:
            self._generate_cli_tool(project_path, tech_stack)
        else:
            self._generate_generic_project(project_path, tech_stack)
        
        return {
            "project_path": project_path,
            "files_created": self.generated_files,
            "tech_stack": tech_stack
        }
    
    def _generate_project_name(self, description: str) -> str:
        """Generate a project name from description."""
        # Simple name generation
        words = description.lower().split()[:3]
        name = "-".join(word for word in words if word.isalnum())
        return name or "project"
    
    def _generate_simple_app(self, path: Path, tech_stack: Dict[str, str]):
        """Generate a simple application."""
        self.log("Generating simple app structure")
        
        # Create package.json
        package_json = self._create_package_json(path.name, tech_stack)
        self._write_file(path / "package.json", json.dumps(package_json, indent=2))
        
        # Create index.html
        html_content = self._generate_html_template(path.name)
        self._write_file(path / "index.html", html_content)
        
        # Create src directory
        src_dir = path / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create main.ts
        main_content = self._generate_typescript_main()
        self._write_file(src_dir / "main.ts", main_content)
        
        # Create styles.css
        styles_content = self._generate_css_styles()
        self._write_file(src_dir / "styles.css", styles_content)
        
        # Create vite.config.ts
        vite_config = self._generate_vite_config()
        self._write_file(path / "vite.config.ts", vite_config)
        
        # Create tsconfig.json
        tsconfig = self._generate_tsconfig()
        self._write_file(path / "tsconfig.json", json.dumps(tsconfig, indent=2))
        
        # Create README.md
        readme = self._generate_readme(path.name, tech_stack)
        self._write_file(path / "README.md", readme)
    
    def _generate_web_app(self, path: Path, tech_stack: Dict[str, str]):
        """Generate a web application."""
        self.log("Generating web app structure")
        
        # Similar to simple app but with more structure
        self._generate_simple_app(path, tech_stack)
        
        # Add components directory
        components_dir = path / "src" / "components"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        # Add a sample component
        component_content = self._generate_react_component("App")
        self._write_file(components_dir / "App.tsx", component_content)
        
        # Add utils directory
        utils_dir = path / "src" / "utils"
        utils_dir.mkdir(exist_ok=True)
        
        # Add types directory
        types_dir = path / "src" / "types"
        types_dir.mkdir(exist_ok=True)
    
    def _generate_rest_api(self, path: Path, tech_stack: Dict[str, str]):
        """Generate a REST API project."""
        self.log("Generating REST API structure")
        
        # Create Python project structure
        self._write_file(path / "requirements.txt", self._generate_requirements(tech_stack))
        self._write_file(path / "main.py", self._generate_fastapi_main())
        self._write_file(path / "README.md", self._generate_api_readme(path.name, tech_stack))
        
        # Create app directory
        app_dir = path / "app"
        app_dir.mkdir(exist_ok=True)
        
        self._write_file(app_dir / "__init__.py", "")
        self._write_file(app_dir / "models.py", self._generate_python_models())
        self._write_file(app_dir / "routes.py", self._generate_api_routes())
        self._write_file(app_dir / "database.py", self._generate_database_config())
    
    def _generate_cli_tool(self, path: Path, tech_stack: Dict[str, str]):
        """Generate a CLI tool project."""
        self.log("Generating CLI tool structure")
        
        # Create Python CLI structure
        self._write_file(path / "requirements.txt", "typer>=0.9.0\\nrich>=13.0.0\\n")
        self._write_file(path / "cli.py", self._generate_cli_main())
        self._write_file(path / "README.md", self._generate_cli_readme(path.name))
        self._write_file(path / "setup.py", self._generate_setup_py(path.name))
    
    def _generate_generic_project(self, path: Path, tech_stack: Dict[str, str]):
        """Generate a generic project structure."""
        self.log("Generating generic project structure")
        
        # Create basic structure
        self._write_file(path / "README.md", f"# {path.name}\\n\\nGenerated project")
        
        # Determine language and create appropriate files
        if "python" in str(tech_stack.values()).lower():
            self._write_file(path / "requirements.txt", "")
            self._write_file(path / "main.py", "def main():\\n    print('Hello, World!')\\n\\nif __name__ == '__main__':\\n    main()")
        else:
            self._write_file(path / "package.json", json.dumps(self._create_package_json(path.name, tech_stack), indent=2))
            self._write_file(path / "index.js", "console.log('Hello, World!');")
    
    def _create_package_json(self, name: str, tech_stack: Dict[str, str]) -> Dict:
        """Create a package.json file."""
        # Extract versions from tech_stack (format: "package@version")
        dependencies = {}
        dev_dependencies = {}
        
        for key, value in tech_stack.items():
            if "@" in value:
                package, version = value.split("@")
                if package in ["vite", "typescript", "vitest", "eslint", "prettier"]:
                    dev_dependencies[package] = f"^{version}"
                else:
                    dependencies[package] = f"^{version}"
        
        return {
            "name": name,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "test": "vitest",
                "lint": "eslint src --ext .ts,.tsx",
                "format": "prettier --write 'src/**/*.{ts,tsx,css}'"
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
    
    def _generate_html_template(self, title: str) -> str:
        """Generate an HTML template."""
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{title} - Built with Autonomous Coder" />
    <title>{title}</title>
    <link rel="stylesheet" href="/src/styles.css" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>"""
    
    def _generate_typescript_main(self) -> str:
        """Generate a TypeScript main file."""
        return """// Main application entry point
import './styles.css';

interface AppState {
  count: number;
  message: string;
}

class App {
  private state: AppState = {
    count: 0,
    message: 'Welcome to your app!'
  };
  
  constructor(private container: HTMLElement) {
    this.render();
    this.attachEventListeners();
  }
  
  private render(): void {
    this.container.innerHTML = `
      <div class="app">
        <h1>${this.state.message}</h1>
        <div class="counter">
          <button id="decrement">-</button>
          <span class="count">${this.state.count}</span>
          <button id="increment">+</button>
        </div>
        <p>Built with TypeScript and Vite</p>
      </div>
    `;
  }
  
  private attachEventListeners(): void {
    this.container.querySelector('#increment')?.addEventListener('click', () => {
      this.state.count++;
      this.render();
      this.attachEventListeners();
    });
    
    this.container.querySelector('#decrement')?.addEventListener('click', () => {
      this.state.count--;
      this.render();
      this.attachEventListeners();
    });
  }
}

// Initialize app
const appElement = document.querySelector<HTMLDivElement>('#app');
if (appElement) {
  new App(appElement);
}
"""
    
    def _generate_css_styles(self) -> str:
        """Generate CSS styles."""
        return """/* Modern CSS with custom properties */
:root {
  --primary-color: #6366f1;
  --text-color: #1f2937;
  --bg-color: #ffffff;
  --border-color: #e5e7eb;
  --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--text-color);
  background: var(--bg-color);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app {
  text-align: center;
  padding: 2rem;
  background: white;
  border-radius: 1rem;
  box-shadow: var(--shadow);
  min-width: 300px;
}

h1 {
  color: var(--primary-color);
  margin-bottom: 2rem;
  font-size: 2rem;
}

.counter {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: 2rem 0;
}

button {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 1.25rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

button:hover {
  opacity: 0.9;
}

.count {
  font-size: 2rem;
  font-weight: bold;
  min-width: 3rem;
}

p {
  color: #6b7280;
  margin-top: 2rem;
}
"""
    
    def _generate_vite_config(self) -> str:
        """Generate Vite configuration."""
        return """import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  build: {
    target: 'esnext',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      }
    }
  },
  server: {
    port: 5173,
    open: true
  }
});
"""
    
    def _generate_tsconfig(self) -> Dict:
        """Generate TypeScript configuration."""
        return {
            "compilerOptions": {
                "target": "ES2022",
                "useDefineForClassFields": True,
                "module": "ESNext",
                "lib": ["ES2022", "DOM", "DOM.Iterable"],
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
                "allowJs": True,
                "esModuleInterop": True,
                "forceConsistentCasingInFileNames": True
            },
            "include": ["src/**/*", "vite.config.ts"]
        }
    
    def _generate_readme(self, name: str, tech_stack: Dict[str, str]) -> str:
        """Generate a README file."""
        tech_list = "\\n".join([f"- {k}: {v}" for k, v in tech_stack.items()])
        
        return f"""# {name}

Generated by Autonomous Coder on {datetime.now().strftime('%Y-%m-%d')}

## Tech Stack

{tech_list}

## Getting Started

### Prerequisites

- Node.js 20+ or Bun 1.2+
- pnpm (recommended) or npm

### Installation

```bash
pnpm install
```

### Development

```bash
pnpm dev
```

### Build

```bash
pnpm build
```

### Test

```bash
pnpm test
```

## Features

- ⚡ Vite for fast development
- 🎯 TypeScript for type safety
- 🎨 Modern CSS with custom properties
- 🧪 Vitest for testing
- 📦 Optimized production build

## License

MIT
"""
    
    def _generate_react_component(self, name: str) -> str:
        """Generate a React component."""
        return f"""import {{ useState }} from 'react';

interface {name}Props {{
  title?: string;
}}

export function {name}({{ title = 'Hello, World!' }}: {name}Props) {{
  const [count, setCount] = useState(0);
  
  return (
    <div className="{name.lower()}">
      <h1>{{title}}</h1>
      <div className="counter">
        <button onClick={{() => setCount(c => c - 1)}}>-</button>
        <span>{{count}}</span>
        <button onClick={{() => setCount(c => c + 1)}}>+</button>
      </div>
    </div>
  );
}}
"""
    
    def _generate_requirements(self, tech_stack: Dict[str, str]) -> str:
        """Generate Python requirements.txt."""
        requirements = []
        
        for key, value in tech_stack.items():
            if "@" in value:
                package, version = value.split("@")
                if package in ["fastapi", "django", "flask", "sqlalchemy", "pytest"]:
                    requirements.append(f"{package}>={version}")
        
        # Add common dependencies
        if "fastapi" in str(tech_stack.values()):
            requirements.extend(["uvicorn>=0.27.0", "pydantic>=2.5.0"])
        
        return "\\n".join(requirements)
    
    def _generate_fastapi_main(self) -> str:
        """Generate FastAPI main file."""
        return '''"""FastAPI Application"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="API Service",
    description="Generated by Autonomous Coder",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

# In-memory storage (replace with database)
items_db: List[Item] = []
next_id = 1

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "API is running", "timestamp": datetime.now()}

@app.get("/items", response_model=List[Item])
async def get_items():
    """Get all items"""
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item"""
    global next_id
    item.id = next_id
    item.created_at = datetime.now()
    next_id += 1
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get a specific item"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item"""
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_python_models(self) -> str:
        """Generate Python models file."""
        return '''"""Data models"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
'''
    
    def _generate_api_routes(self) -> str:
        """Generate API routes file."""
        return '''"""API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
'''
    
    def _generate_database_config(self) -> str:
        """Generate database configuration."""
        return '''"""Database configuration"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _generate_api_readme(self, name: str, tech_stack: Dict[str, str]) -> str:
        """Generate README for API project."""
        return f"""# {name} API

RESTful API built with FastAPI

## Tech Stack

- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

## Installation

```bash
pip install -r requirements.txt
```

## Development

```bash
uvicorn main:app --reload
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation

## Endpoints

- GET /items - List all items
- POST /items - Create new item
- GET /items/{{id}} - Get specific item
- DELETE /items/{{id}} - Delete item

## Testing

```bash
pytest
```
"""
    
    def _generate_cli_main(self) -> str:
        """Generate CLI main file."""
        return '''#!/usr/bin/env python3
"""CLI Tool"""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

app = typer.Typer()
console = Console()

@app.command()
def hello(name: str = "World"):
    """Say hello"""
    console.print(f"Hello, {name}!", style="bold green")

@app.command()
def list_items(limit: int = 10):
    """List items in a table"""
    table = Table(title="Items")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    
    for i in range(limit):
        table.add_row(str(i), f"Item {i}", "Active")
    
    console.print(table)

@app.command()
def process(
    input_file: str = typer.Argument(..., help="Input file path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Process a file"""
    if verbose:
        console.print(f"Processing {input_file}...", style="yellow")
    
    # Process logic here
    
    if output:
        console.print(f"Results saved to {output}", style="green")
    else:
        console.print("Processing complete!", style="bold green")

if __name__ == "__main__":
    app()
'''
    
    def _generate_cli_readme(self, name: str) -> str:
        """Generate README for CLI project."""
        return f"""# {name} CLI

Command-line tool built with Typer

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --help
python cli.py hello --name "User"
python cli.py list-items --limit 20
python cli.py process input.txt -o output.txt -v
```

## Development

```bash
pip install -e .
```

## Building

```bash
python setup.py sdist bdist_wheel
```
"""
    
    def _generate_setup_py(self, name: str) -> str:
        """Generate setup.py for Python projects."""
        return f'''from setuptools import setup, find_packages

setup(
    name="{name}",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    entry_points={{
        "console_scripts": [
            "{name}=cli:app",
        ],
    }},
    python_requires=">=3.8",
)
'''
    
    def _write_file(self, path: Path, content: str):
        """Write content to a file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        self.generated_files.append(str(path))
        self.log(f"Created: {path}")
    
    def format_code(self, code: str, language: str) -> str:
        """Format code based on language."""
        # Simple formatting (could integrate with prettier/black)
        return code
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of generation activities."""
        return {
            "files_generated": len(self.generated_files),
            "files": self.generated_files,
            "metrics": self.get_metrics()
        }