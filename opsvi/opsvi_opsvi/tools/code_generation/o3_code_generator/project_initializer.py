"""
Project Initializer for O3 Code Generator

This module provides comprehensive project initialization capabilities using OpenAI's O3 models,
including project scaffolding, dependency management, configuration setup, and development environment preparation.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    pass

try:
    from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
        ConfigManager,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass

try:
    from o3_logger.logger import LogConfig, setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass

try:
    from schemas.project_initializer_input_schema import ProjectInitializationInput
    from schemas.project_initializer_output_schema import ProjectInitializationOutput
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class ProjectScaffolder:
    """Handles project scaffolding and file generation."""

    def __init__(self, logger: Any) -> None:
        """Initialize the project scaffolder."""
        self.logger = logger

    def create_project_structure(
        self, project_path: Path, project_type: str
    ) -> list[str]:
        """
        Create basic project structure.

        Args:
            project_path: Path to create the project
            project_type: Type of project to create

        Returns:
            List of created files
        """
        created_files = []

        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            created_files.append(str(project_path))

            # Create project structure based on type
            if project_type == "python":
                created_files.extend(self._create_python_structure(project_path))
            elif project_type == "python-fastapi":
                created_files.extend(self._create_fastapi_structure(project_path))
            elif project_type == "nodejs":
                created_files.extend(self._create_nodejs_structure(project_path))
            elif project_type == "react":
                created_files.extend(self._create_react_structure(project_path))
            else:
                created_files.extend(self._create_generic_structure(project_path))

        except Exception as e:
            self.logger.log_error(e, f"Error creating project structure: {e}")

        return created_files

    def _create_python_structure(self, project_path: Path) -> list[str]:
        """Create Python project structure."""
        created_files = []

        # Create directories
        directories = ["src", "tests", "docs", "scripts", "config"]
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            created_files.append(str(dir_path))

        # Create basic files
        files = {
            "README.md": self._get_python_readme(),
            "requirements.txt": self._get_python_requirements(),
            "setup.py": self._get_python_setup(),
            "pyproject.toml": self._get_python_pyproject(),
            ".gitignore": self._get_python_gitignore(),
            "src/__init__.py": "",
            "tests/__init__.py": "",
            "config/config.yaml": self._get_python_config(),
        }

        for filename, content in files.items():
            file_path = project_path / filename
            file_path.write_text(content)
            created_files.append(str(file_path))

        return created_files

    def _create_fastapi_structure(self, project_path: Path) -> list[str]:
        """Create FastAPI project structure."""
        created_files = []

        # Create directories
        directories = [
            "src",
            "src/api",
            "src/models",
            "src/services",
            "tests",
            "docs",
            "scripts",
        ]
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            created_files.append(str(dir_path))

        # Create basic files
        files = {
            "README.md": self._get_fastapi_readme(),
            "requirements.txt": self._get_fastapi_requirements(),
            "main.py": self._get_fastapi_main(),
            "src/api/__init__.py": "",
            "src/models/__init__.py": "",
            "src/services/__init__.py": "",
            ".gitignore": self._get_python_gitignore(),
            "docker-compose.yml": self._get_fastapi_docker_compose(),
        }

        for filename, content in files.items():
            file_path = project_path / filename
            file_path.write_text(content)
            created_files.append(str(file_path))

        return created_files

    def _create_nodejs_structure(self, project_path: Path) -> list[str]:
        """Create Node.js project structure."""
        created_files = []

        # Create directories
        directories = ["src", "tests", "docs", "scripts", "config"]
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            created_files.append(str(dir_path))

        # Create basic files
        files = {
            "README.md": self._get_nodejs_readme(),
            "package.json": self._get_nodejs_package_json(),
            "package-lock.json": "{}",
            ".gitignore": self._get_nodejs_gitignore(),
            "src/index.js": self._get_nodejs_index(),
            "config/config.json": "{}",
        }

        for filename, content in files.items():
            file_path = project_path / filename
            file_path.write_text(content)
            created_files.append(str(file_path))

        return created_files

    def _create_react_structure(self, project_path: Path) -> list[str]:
        """Create React project structure."""
        created_files = []

        # Create directories
        directories = [
            "src",
            "src/components",
            "src/pages",
            "src/utils",
            "public",
            "tests",
        ]
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            created_files.append(str(dir_path))

        # Create basic files
        files = {
            "README.md": self._get_react_readme(),
            "package.json": self._get_react_package_json(),
            "public/index.html": self._get_react_index_html(),
            "src/index.js": self._get_react_index_js(),
            "src/App.js": self._get_react_app_js(),
            ".gitignore": self._get_react_gitignore(),
        }

        for filename, content in files.items():
            file_path = project_path / filename
            file_path.write_text(content)
            created_files.append(str(file_path))

        return created_files

    def _create_generic_structure(self, project_path: Path) -> list[str]:
        """Create generic project structure."""
        created_files = []

        # Create directories
        directories = ["src", "docs", "tests"]
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            created_files.append(str(dir_path))

        # Create basic files
        files = {
            "README.md": self._get_generic_readme(),
            ".gitignore": self._get_generic_gitignore(),
        }

        for filename, content in files.items():
            file_path = project_path / filename
            file_path.write_text(content)
            created_files.append(str(file_path))

        return created_files

    def _get_python_readme(self) -> str:
        """Get Python README template."""
        return """# Python Project

## Description
A Python project generated by O3 Code Generator.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python src/main.py
```

## Testing
```bash
pytest tests/
```
"""

    def _get_python_requirements(self) -> str:
        """Get Python requirements template."""
        return """# Core dependencies
pydantic>=2.0.0
fastapi>=0.100.0
uvicorn>=0.20.0

# Development dependencies
pytest>=7.0.0
black>=23.0.0
ruff>=0.1.0
"""

    def _get_python_setup(self) -> str:
        """Get Python setup.py template."""
        return """from setuptools import setup, find_packages

setup(
    name="python-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)
"""

    def _get_python_pyproject(self) -> str:
        """Get Python pyproject.toml template."""
        return """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "python-project"
version = "0.1.0"
description = "A Python project"
requires-python = ">=3.8"
dependencies = [
    "pydantic>=2.0.0",
]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.ruff]
line-length = 88
target-version = "py38"
"""

    def _get_python_gitignore(self) -> str:
        """Get Python .gitignore template."""
        return """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
"""

    def _get_python_config(self) -> str:
        """Get Python config template."""
        return """# Configuration
app:
  name: "Python Project"
  version: "0.1.0"
  debug: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""

    def _get_fastapi_readme(self) -> str:
        """Get FastAPI README template."""
        return """# FastAPI Project

## Description
A FastAPI project generated by O3 Code Generator.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
uvicorn main:app --reload
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

    def _get_fastapi_requirements(self) -> str:
        """Get FastAPI requirements template."""
        return """fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
python-multipart>=0.0.6
"""

    def _get_fastapi_main(self) -> str:
        """Get FastAPI main.py template."""
        return """from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FastAPI Project", version="0.1.0")

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(item: Item):
    return item
"""

    def _get_fastapi_docker_compose(self) -> str:
        """Get FastAPI docker-compose.yml template."""
        return """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DEBUG=true
"""

    def _get_nodejs_readme(self) -> str:
        """Get Node.js README template."""
        return """# Node.js Project

## Description
A Node.js project generated by O3 Code Generator.

## Installation
```bash
npm install
```

## Usage
```bash
npm start
```

## Testing
```bash
npm test
```
"""

    def _get_nodejs_package_json(self) -> str:
        """Get Node.js package.json template."""
        return """{
  "name": "nodejs-project",
  "version": "0.1.0",
  "description": "A Node.js project",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "test": "jest",
    "dev": "nodemon src/index.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "nodemon": "^3.0.0"
  }
}
"""

    def _get_nodejs_gitignore(self) -> str:
        """Get Node.js .gitignore template."""
        return """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
"""

    def _get_nodejs_index(self) -> str:
        """Get Node.js index.js template."""
        return """const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Hello World!' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
"""

    def _get_react_readme(self) -> str:
        """Get React README template."""
        return """# React Project

## Description
A React project generated by O3 Code Generator.

## Installation
```bash
npm install
```

## Usage
```bash
npm start
```

## Build
```bash
npm run build
```
"""

    def _get_react_package_json(self) -> str:
        """Get React package.json template."""
        return """{
  "name": "react-project",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
"""

    def _get_react_index_html(self) -> str:
        """Get React index.html template."""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""

    def _get_react_index_js(self) -> str:
        """Get React index.js template."""
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

    def _get_react_app_js(self) -> str:
        """Get React App.js template."""
        return """import React from 'react';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to React</h1>
        <p>This project was generated by O3 Code Generator.</p>
      </header>
    </div>
  );
}

export default App;
"""

    def _get_react_gitignore(self) -> str:
        """Get React .gitignore template."""
        return """# Dependencies
/node_modules
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""

    def _get_generic_readme(self) -> str:
        """Get generic README template."""
        return """# Project

## Description
A project generated by O3 Code Generator.

## Getting Started
Follow the project-specific documentation for setup and usage instructions.
"""

    def _get_generic_gitignore(self) -> str:
        """Get generic .gitignore template."""
        return """# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""


class GitInitializer:
    """Handles Git repository initialization."""

    def __init__(self, logger: Any) -> None:
        """Initialize the Git initializer."""
        self.logger = logger

    def initialize_git_repository(self, project_path: Path) -> bool:
        """
        Initialize a Git repository in the project directory.

        Args:
            project_path: Path to the project directory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.log_warning(
                    "Git not available, skipping repository initialization"
                )
                return False

            # Initialize git repository
            result = subprocess.run(
                ["git", "init"], cwd=project_path, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.log_error(
                    f"Failed to initialize git repository: {result.stderr}"
                )
                return False

            # Add all files
            result = subprocess.run(
                ["git", "add", "."], cwd=project_path, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.log_error(f"Failed to add files to git: {result.stderr}")
                return False

            # Initial commit
            result = subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.logger.log_error(
                    f"Failed to create initial commit: {result.stderr}"
                )
                return False

            self.logger.log_info("Git repository initialized successfully")
            return True

        except Exception as e:
            self.logger.log_error(e, "Error initializing git repository")
            return False


class VirtualEnvironmentManager:
    """Handles virtual environment creation for Python projects."""

    def __init__(self, logger: Any) -> None:
        """Initialize the virtual environment manager."""
        self.logger = logger

    def create_virtual_environment(self, project_path: Path) -> bool:
        """
        Create a virtual environment for Python projects.

        Args:
            project_path: Path to the project directory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if python is available
            result = subprocess.run(
                ["python", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.log_warning(
                    "Python not available, skipping virtual environment creation"
                )
                return False

            # Create virtual environment
            venv_path = project_path / "venv"
            result = subprocess.run(
                ["python", "-m", "venv", str(venv_path)], capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.log_error(
                    f"Failed to create virtual environment: {result.stderr}"
                )
                return False

            self.logger.log_info("Virtual environment created successfully")
            return True

        except Exception as e:
            self.logger.log_error(e, "Error creating virtual environment")
            return False


class ProjectInitializer:
    """Main project initializer class."""

    def __init__(self, config_path: str | None = None):
        """Initialize the project initializer.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = ConfigManager(config_path)
        log_config = LogConfig(
            level=self.config.get("logging.level", "INFO"),
            log_dir=self.config.get("paths.logs", "logs"),
            standard_log_file="project_initializer.log",
            debug_log_file="project_initializer_debug.log",
            error_log_file="project_initializer_error.log",
        )
        self.logger = setup_logger(log_config)
        self.client = OpenAI(
            api_key=self.config.get("api.openai_api_key"),
            base_url=self.config.get("api.base_url", "https://api.openai.com/v1"),
        )
        self.scaffolder = ProjectScaffolder(self.logger)
        self.git_initializer = GitInitializer(self.logger)
        self.venv_manager = VirtualEnvironmentManager(self.logger)
        self.logger.log_info("Project Initializer initialized successfully")

    def initialize_project(
        self, input_data: ProjectInitializationInput
    ) -> ProjectInitializationOutput:
        """
        Initialize a new project based on the input specifications.

        Args:
            input_data: Project initialization input specification

        Returns:
            Project initialization output with results
        """
        start_time = time.time()
        self.logger.log_info(
            f"Starting project initialization: {input_data.project_name}"
        )

        try:
            # Determine project path
            if input_data.target_directory:
                project_path = (
                    Path(input_data.target_directory) / input_data.project_name
                )
            else:
                project_path = Path.cwd() / input_data.project_name

            # Create project structure
            created_files = self.scaffolder.create_project_structure(
                project_path, input_data.project_type
            )

            # Initialize git repository if requested
            git_initialized = False
            if input_data.git_init:
                git_initialized = self.git_initializer.initialize_git_repository(
                    project_path
                )

            # Create virtual environment for Python projects
            venv_created = False
            if input_data.create_virtual_env and input_data.project_type.startswith(
                "python"
            ):
                venv_created = self.venv_manager.create_virtual_environment(
                    project_path
                )

            # Generate next steps
            next_steps = self._generate_next_steps(
                input_data, project_path, git_initialized, venv_created
            )

            generation_time = time.time() - start_time
            self.logger.log_info(
                f"Project initialization completed in {generation_time:.2f} seconds"
            )

            return ProjectInitializationOutput(
                success=True,
                project_path=str(project_path),
                created_files=created_files,
                next_steps=next_steps,
            )

        except Exception as e:
            self.logger.log_error(e, "Error during project initialization")
            return ProjectInitializationOutput(
                success=False,
                project_path="",
                created_files=[],
                next_steps=[],
                error_message=str(e),
            )

    def _generate_next_steps(
        self,
        input_data: ProjectInitializationInput,
        project_path: Path,
        git_initialized: bool,
        venv_created: bool,
    ) -> list[str]:
        """Generate next steps for the user."""
        next_steps = []

        next_steps.append(f"Navigate to the project directory: cd {project_path}")

        if input_data.project_type.startswith("python"):
            if venv_created:
                next_steps.append("Activate the virtual environment:")
                next_steps.append("  - On Windows: venv\\Scripts\\activate")
                next_steps.append("  - On macOS/Linux: source venv/bin/activate")
            next_steps.append("Install dependencies: pip install -r requirements.txt")
            next_steps.append("Run the project: python src/main.py")

        elif input_data.project_type == "nodejs":
            next_steps.append("Install dependencies: npm install")
            next_steps.append("Run the project: npm start")

        elif input_data.project_type == "react":
            next_steps.append("Install dependencies: npm install")
            next_steps.append("Start development server: npm start")

        if git_initialized:
            next_steps.append(
                "Git repository initialized - you can start committing changes"
            )

        next_steps.append("Review and customize the generated files as needed")
        next_steps.append("Add your specific business logic and features")

        return next_steps


def main() -> None:
    """Main entry point for the project initializer."""
    parser = argparse.ArgumentParser(
        description="Project Initializer - AI-powered project setup"
    )
    parser.add_argument(
        "input_file",
        help="Path to input file (JSON or YAML) containing project initialization parameters",
    )
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()

    try:
        initializer = ProjectInitializer(args.config)

        # Load input data
        with open(args.input_file) as f:
            input_data = json.load(f)

        # Create ProjectInitializationInput object
        project_input = ProjectInitializationInput(**input_data)

        # Initialize project
        output = initializer.initialize_project(project_input)

        if output.success:
            print("Project initialization completed successfully!")
            print(f"Project created at: {output.project_path}")
            print(f"Files created: {len(output.created_files)}")
            print("\nNext steps:")
            for step in output.next_steps:
                print(f"  - {step}")
        else:
            print(f"Project initialization failed: {output.error_message}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
