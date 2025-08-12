"""CI/CD Pipeline Generator - AI-powered CI/CD pipeline generation using OpenAI's O3 models.

This module generates comprehensive CI/CD pipelines for GitHub Actions, GitLab CI,
Jenkins, and other CI/CD platforms with intelligent workflow optimization and best practices.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.schemas.cicd_pipeline_generator_input_schema import (
    CICDPipelineGeneratorInput,
)
from src.tools.code_generation.o3_code_generator.schemas.cicd_pipeline_generator_output_schema import (
    CICDPipelineGeneratorOutput,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class ProjectAnalyzer:
    """Analyzes project structure and requirements for CI/CD configuration."""

    def __init__(self) -> None:
        """Initialize ProjectAnalyzer with O3Logger."""
        self.logger = get_logger()

    def analyze_project(self, project_path: Path) -> dict[str, Any]:
        """
        Analyze project for CI/CD requirements.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary containing project analysis
        """
        self.logger.log_info(
            f"Analyzing project for CI/CD configuration: {project_path}"
        )
        analysis: dict[str, Any] = {
            "project_type": self._detect_project_type(project_path),
            "dependencies": self._analyze_dependencies(project_path),
            "testing_framework": self._detect_testing_framework(project_path),
            "build_tools": self._detect_build_tools(project_path),
            "deployment_targets": self._detect_deployment_targets(project_path),
            "environment_configs": self._detect_environment_configs(project_path),
            "security_requirements": self._detect_security_requirements(project_path),
            "performance_requirements": self._detect_performance_requirements(
                project_path
            ),
        }
        self.logger.log_info(f"Project analysis completed: {analysis['project_type']}")
        return analysis

    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project."""
        if (project_path / "requirements.txt").exists():
            return "python"
        else:
            pass
        if (project_path / "package.json").exists():
            return "nodejs"
        else:
            pass
        if (project_path / "pom.xml").exists():
            return "java"
        else:
            pass
        if (project_path / "Cargo.toml").exists():
            return "rust"
        else:
            pass
        if (project_path / "go.mod").exists():
            return "go"
        else:
            pass
        return "unknown"

    def _analyze_dependencies(self, project_path: Path) -> dict[str, Any]:
        """Analyze project dependencies."""
        deps: dict[str, Any] = {"runtime": [], "dev": [], "build": []}
        try:
            requirements_file = project_path / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file) as f:
                    deps["runtime"] = [
                        line.strip()
                        for line in f
                        if line.strip() and (not line.startswith("#"))
                    ]
            else:
                pass
            package_file = project_path / "package.json"
            if package_file.exists():
                with open(package_file) as f:
                    pkg_data = json.load(f)
                deps["runtime"].extend(list(pkg_data.get("dependencies", {}).keys()))
                deps["dev"].extend(list(pkg_data.get("devDependencies", {}).keys()))
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error analyzing dependencies: {e}")
            raise
        else:
            pass
        finally:
            pass
        return deps

    def _detect_testing_framework(self, project_path: Path) -> list[str]:
        """Detect testing frameworks used in the project."""
        frameworks: list[str] = []
        try:
            if (project_path / "pytest.ini").exists() or (
                project_path / "pyproject.toml"
            ).exists():
                frameworks.append("pytest")
            else:
                pass
            if (project_path / "tox.ini").exists():
                frameworks.append("tox")
            else:
                pass
            package_file = project_path / "package.json"
            if package_file.exists():
                with open(package_file) as f:
                    pkg_data = json.load(f)
                dev_deps = pkg_data.get("devDependencies", {})
                for tool in ("jest", "mocha", "cypress"):
                    if tool in dev_deps:
                        frameworks.append(tool)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting testing frameworks: {e}")
            raise
        else:
            pass
        finally:
            pass
        return frameworks

    def _detect_build_tools(self, project_path: Path) -> list[str]:
        """Detect build tools used in the project."""
        tools: list[str] = []
        try:
            if (project_path / "setup.py").exists():
                tools.append("setuptools")
            else:
                pass
            if (project_path / "pyproject.toml").exists():
                tools.append("poetry")
            else:
                pass
            if (project_path / "Pipfile").exists():
                tools.append("pipenv")
            else:
                pass
            for name, label in (
                ("webpack.config.js", "webpack"),
                ("vite.config.js", "vite"),
                ("rollup.config.js", "rollup"),
            ):
                if (project_path / name).exists():
                    tools.append(label)
                else:
                    pass
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting build tools: {e}")
            raise
        else:
            pass
        finally:
            pass
        return tools

    def _detect_deployment_targets(self, project_path: Path) -> list[str]:
        """Detect deployment targets from configuration files."""
        targets: list[str] = []
        try:
            if (project_path / "Dockerfile").exists():
                targets.append("docker")
            else:
                pass
            if (project_path / "k8s").exists() or (
                project_path / "kubernetes"
            ).exists():
                targets.append("kubernetes")
            else:
                pass
            for fname in (
                "serverless.yml",
                "terraform.tf",
                "cloudformation.yml",
                "app.yaml",
            ):
                if (project_path / fname).exists():
                    targets.append("cloud")
                    break
                else:
                    pass
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting deployment targets: {e}")
            raise
        else:
            pass
        finally:
            pass
        return targets

    def _detect_environment_configs(self, project_path: Path) -> list[str]:
        """Detect environment configurations."""
        configs: list[str] = []
        try:
            for env_file in (".env", ".env.example", ".env.local", ".env.production"):
                if (project_path / env_file).exists():
                    configs.append(env_file)
                else:
                    pass
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting environment configs: {e}")
            raise
        else:
            pass
        finally:
            pass
        return configs

    def _detect_security_requirements(self, project_path: Path) -> list[str]:
        """Detect security requirements."""
        requirements: list[str] = []
        try:
            for fname in ("bandit.yaml", ".bandit", "safety.txt", "snyk.yaml"):
                if (project_path / fname).exists():
                    requirements.append("security_scanning")
                    break
                else:
                    pass
            else:
                pass
            if (project_path / "requirements.txt").exists() or (
                project_path / "package.json"
            ).exists():
                requirements.append("dependency_scanning")
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting security requirements: {e}")
            raise
        else:
            pass
        finally:
            pass
        return requirements

    def _detect_performance_requirements(self, project_path: Path) -> list[str]:
        """Detect performance requirements."""
        requirements: list[str] = []
        try:
            for fname in ("prometheus.yml", "grafana.ini", "newrelic.ini"):
                if (project_path / fname).exists():
                    requirements.append("performance_monitoring")
                    break
                else:
                    pass
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error detecting performance requirements: {e}")
            raise
        else:
            pass
        finally:
            pass
        return requirements


class GitHubActionsGenerator:
    """Generates GitHub Actions workflows using AI."""

    def __init__(self, client: OpenAI) -> None:
        """Initialize GitHubActionsGenerator with OpenAI client and logger."""
        self.client = client
        self.logger = get_logger()
        self.prompt_builder = PromptBuilder()

    def generate_workflow(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """
        Generate GitHub Actions workflow.

        Args:
            project_name: Name of the project
            analysis: Project analysis results
            config: CI/CD configuration

        Returns:
            Generated GitHub Actions workflow content
        """
        self.logger.log_info(f"Generating GitHub Actions workflow for {project_name}")
        system_prompt = (
            "You are a CI/CD expert. Generate comprehensive GitHub Actions workflows."
        )
        context = {"project_name": project_name, "analysis": analysis, "config": config}
        prompt = self.prompt_builder.build_generation_prompt(
            None,
            context=context,
            system_prompt=system_prompt,
            format_instructions="Respond with only YAML content",
        )
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error(f"Failed to generate GitHub Actions workflow: {e}")
            return self._generate_fallback_workflow(project_name, analysis, config)
        else:
            pass
        finally:
            pass

    def _generate_fallback_workflow(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """Generate a fallback GitHub Actions workflow."""
        project_type = analysis.get("project_type", "python")
        if project_type == "python":
            return f"""name: CI/CD Pipeline\n\non:\n  push:\n    branches: [ main, develop ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python-version: [3.9, 3.10, 3.11]\n\n    steps:\n      - uses: actions/checkout@v4\n      - name: Set up Python ${{{{ matrix.python-version }}}}\n        uses: actions/setup-python@v4\n        with:\n          python-version: ${{{{ matrix.python-version }}}}\n      - name: Cache dependencies\n        uses: actions/cache@v3\n        with:\n          path: ~/.cache/pip\n          key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}\n          restore-keys: |\n            ${{{{ runner.os }}}}-pip-\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install -r requirements.txt\n      - name: Run tests\n        run: pytest tests/\n      - name: Run security scan\n        run: |\n          pip install bandit\n          bandit -r src/\n  build:\n    needs: test\n    runs-on: ubuntu-latest\n    if: github.ref == 'refs/heads/main'\n    steps:\n      - uses: actions/checkout@v4\n      - name: Build and push Docker image\n        run: |\n          docker build -t {project_name} .\n          echo "Build completed"\n"""
        else:
            pass
        return f'name: CI/CD Pipeline\n\non:\n  push:\n    branches: [ main, develop ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Run tests\n        run: echo "Running tests for {project_name}"\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Build\n        run: echo "Building {project_name}"\n'


class GitLabCIGenerator:
    """Generates GitLab CI pipelines using AI."""

    def __init__(self, client: OpenAI) -> None:
        """Initialize GitLabCIGenerator with OpenAI client and logger."""
        self.client = client
        self.logger = get_logger()
        self.prompt_builder = PromptBuilder()

    def generate_pipeline(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """
        Generate GitLab CI pipeline.

        Args:
            project_name: Name of the project
            analysis: Project analysis results
            config: CI/CD configuration

        Returns:
            Generated GitLab CI pipeline content
        """
        self.logger.log_info(f"Generating GitLab CI pipeline for {project_name}")
        system_prompt = (
            "You are a CI/CD expert. Generate comprehensive GitLab CI pipelines."
        )
        context = {"project_name": project_name, "analysis": analysis, "config": config}
        prompt = self.prompt_builder.build_generation_prompt(
            None,
            context=context,
            system_prompt=system_prompt,
            format_instructions="Respond with only YAML content",
        )
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error(f"Failed to generate GitLab CI pipeline: {e}")
            return self._generate_fallback_pipeline(project_name, analysis, config)
        else:
            pass
        finally:
            pass

    def _generate_fallback_pipeline(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """Generate a fallback GitLab CI pipeline."""
        project_type = analysis.get("project_type", "python")
        if project_type == "python":
            return f'stages:\n  - test\n  - build\n  - deploy\n\nvariables:\n  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"\n\ncache:\n  paths:\n    - .pip-cache/\n\ntest:\n  stage: test\n  image: python:3.11\n  script:\n    - pip install -r requirements.txt\n    - pytest tests/\n  artifacts:\n    reports:\n      junit: test-results.xml\n\nsecurity_scan:\n  stage: test\n  image: python:3.11\n  script:\n    - pip install bandit\n    - bandit -r src/ -f json -o bandit-report.json\n  artifacts:\n    reports:\n      sast: bandit-report.json\n\nbuild:\n  stage: build\n  image: docker:latest\n  services:\n    - docker:dind\n  script:\n    - docker build -t {project_name} .\n  only:\n    - main\n\ndeploy:\n  stage: deploy\n  image: alpine:latest\n  script:\n    - echo "Deploying {project_name}"\n  only:\n    - main\n'
        else:
            pass
        return f'stages:\n  - test\n  - build\n  - deploy\n\ntest:\n  stage: test\n  script:\n    - echo "Running tests for {project_name}"\n\nbuild:\n  stage: build\n  script:\n    - echo "Building {{project_name}}"\n  only:\n    - main\n\ndeploy:\n  stage: deploy\n  script:\n    - echo "Deploying {project_name}"\n  only:\n    - main\n'


class JenkinsGenerator:
    """Generates Jenkins pipeline configurations using AI."""

    def __init__(self, client: OpenAI) -> None:
        """Initialize JenkinsGenerator with OpenAI client and logger."""
        self.client = client
        self.logger = get_logger()
        self.prompt_builder = PromptBuilder()

    def generate_pipeline(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """
        Generate Jenkins pipeline.

        Args:
            project_name: Name of the project
            analysis: Project analysis results
            config: CI/CD configuration

        Returns:
            Generated Jenkins pipeline content
        """
        self.logger.log_info(f"Generating Jenkins pipeline for {project_name}")
        system_prompt = (
            "You are a CI/CD expert. Generate comprehensive Jenkins pipelines."
        )
        context = {"project_name": project_name, "analysis": analysis, "config": config}
        prompt = self.prompt_builder.build_generation_prompt(
            None,
            context=context,
            system_prompt=system_prompt,
            format_instructions="Respond with only Jenkinsfile content",
        )
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.log_error(f"Failed to generate Jenkins pipeline: {e}")
            return self._generate_fallback_pipeline(project_name, analysis, config)
        else:
            pass
        finally:
            pass

    def _generate_fallback_pipeline(
        self, project_name: str, analysis: dict[str, Any], config: dict[str, Any]
    ) -> str:
        """Generate a fallback Jenkins pipeline."""
        project_type = analysis.get("project_type", "python")
        if project_type == "python":
            return f"pipeline {{\n    agent any\n\n    environment {{\n        _PYTHON_VERSION = '3.11'\n    }}\n\n    stages {{\n        stage('Checkout') {{\n            steps {{\n                checkout scm\n            }}\n        }}\n        stage('Setup') {{\n            steps {{\n                sh 'python -m pip install --upgrade pip'\n                sh 'pip install -r requirements.txt'\n            }}\n        }}\n        stage('Test') {{\n            steps {{\n                sh 'pytest tests/'\n            }}\n            post {{\n                always {{\n                    publishTestResults testResultsPattern: 'test-results.xml'\n                }}\n            }}\n        }}\n        stage('Security Scan') {{\n            steps {{\n                sh 'pip install bandit'\n                sh 'bandit -r src/'\n            }}\n        }}\n        stage('Build') {{\n            when {{\n                branch 'main'\n            }}\n            steps {{\n                sh 'docker build -t {project_name} .'\n            }}\n        }}\n        stage('Deploy') {{\n            when {{\n                branch 'main'\n            }}\n            steps {{\n                echo 'Deploying {project_name}'\n            }}\n        }}\n    }}\n\n    post {{\n        always {{\n            cleanWs()\n        }}\n        success {{\n            echo 'Pipeline succeeded!'\n        }}\n        failure {{\n            echo 'Pipeline failed!'\n        }}\n    }}\n}}"
        else:
            pass
        return f"pipeline {{\n    agent any\n\n    stages {{\n        stage('Checkout') {{\n            steps {{\n                checkout scm\n            }}\n        }}\n        stage('Test') {{\n            steps {{\n                echo 'Running tests for {project_name}'\n            }}\n        }}\n        stage('Build') {{\n            when {{\n                branch 'main'\n            }}\n            steps {{\n                echo 'Building {project_name}'\n            }}\n        }}\n        stage('Deploy') {{\n            when {{\n                branch 'main'\n            }}\n            steps {{\n                echo 'Deploying {project_name}'\n            }}\n        }}\n    }}\n}}"


class CICDPipelineGenerator:
    """Main CI/CD pipeline generator orchestrator."""

    def __init__(self, config: CICDPipelineGeneratorInput) -> None:
        """
        Initialize CICDPipelineGenerator.

        Args:
            config: CICDPipelineGeneratorInput schema instance
        """
        self.logger = get_logger()
        self.config = config
        try:
            self.client = OpenAI(api_key=config.openai_api_key)
        except Exception as e:
            self.logger.log_error(f"Failed to initialize OpenAI client: {e}")
            raise
        else:
            pass
        finally:
            pass
        self.project_analyzer = ProjectAnalyzer()
        self.github_actions_generator = GitHubActionsGenerator(self.client)
        self.gitlab_ci_generator = GitLabCIGenerator(self.client)
        self.jenkins_generator = JenkinsGenerator(self.client)
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()

    def generate_pipelines(self) -> CICDPipelineGeneratorOutput:
        """
        Generate CI/CD pipelines for the project.

        Returns:
            CICDPipelineGeneratorOutput with generated pipelines
        """
        self.logger.log_info(
            f"Starting CI/CD pipeline generation for project: {self.config.project_path}"
        )
        project_path = Path(self.config.project_path)
        if not project_path.exists():
            self.logger.log_error(f"Project path does not exist: {project_path}")
            raise ValueError(f"Project path does not exist: {project_path}")
        else:
            pass
        analysis = self.project_analyzer.analyze_project(project_path)
        pipelines: dict[str, str] = {}
        if "github_actions" in self.config.platforms:
            pipelines[
                "github_actions"
            ] = self.github_actions_generator.generate_workflow(
                self.config.project_name,
                analysis,
                self.config.github_actions_config,
            )
        else:
            pass
        if "gitlab_ci" in self.config.platforms:
            pipelines["gitlab_ci"] = self.gitlab_ci_generator.generate_pipeline(
                self.config.project_name, analysis, self.config.gitlab_ci_config
            )
        else:
            pass
        if "jenkins" in self.config.platforms:
            pipelines["jenkins"] = self.jenkins_generator.generate_pipeline(
                self.config.project_name, analysis, self.config.jenkins_config
            )
        else:
            pass
        output_files: list[str] = []
        if self.config.write_files:
            output_files = self._write_pipeline_files(pipelines, project_path)
        else:
            pass
        self.logger.log_info("CI/CD pipeline generation completed successfully")
        return CICDPipelineGeneratorOutput(
            project_name=self.config.project_name,
            project_analysis=analysis,
            generated_pipelines=pipelines,
            output_files=output_files,
            success=True,
            message="CI/CD pipelines generated successfully",
        )

    def _write_pipeline_files(
        self, pipelines: dict[str, str], project_path: Path
    ) -> list[str]:
        """
        Write pipeline files to the project directory.

        Args:
            pipelines: Mapping of platform to pipeline content
            project_path: Root path of the project

        Returns:
            List of written file paths
        """
        written: list[str] = []
        try:
            if "github_actions" in pipelines:
                gh_dir = project_path / ".github" / "workflows"
                self.directory_manager.ensure_directory_exists(gh_dir)
                gh_path = gh_dir / "ci-cd.yml"
                self.file_generator.save_file(pipelines["github_actions"], gh_path)
                written.append(str(gh_path))
            else:
                pass
            if "gitlab_ci" in pipelines:
                gl_path = project_path / ".gitlab-ci.yml"
                self.file_generator.save_file(pipelines["gitlab_ci"], gl_path)
                written.append(str(gl_path))
            else:
                pass
            if "jenkins" in pipelines:
                jenkins_path = project_path / "Jenkinsfile"
                self.file_generator.save_file(pipelines["jenkins"], jenkins_path)
                written.append(str(jenkins_path))
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Error writing pipeline files: {e}")
            raise
        else:
            pass
        finally:
            pass
        return written


def run_cicd_pipeline_generator(
    input_file: str, output_file: str | None = None
) -> None:
    """
    Run the CI/CD pipeline generator with input from file.

    Args:
        input_file: Path to input JSON/YAML configuration file
        output_file: Optional path to save the result output
    """
    logger = get_logger()
    try:
        loader = UniversalInputLoader()
        config_data = loader.load_file_by_extension(input_file)
        if output_file:
            config_data["output_file"] = output_file
        else:
            pass
        config = CICDPipelineGeneratorInput(**config_data)
        generator = CICDPipelineGenerator(config)
        result = generator.generate_pipelines()
        logger.log_info(
            f"CI/CD Pipeline Generation Completed Successfully for project {result.project_name}"
        )
        logger.log_info(f"Platforms: {', '.join(result.generated_pipelines.keys())}")
        logger.log_info(f"Files generated: {len(result.output_files)}")
        for fp in result.output_files:
            logger.log_info(f"Generated file: {fp}")
        else:
            pass
        if config.output_file:
            formatter = OutputFormatter()
            content = formatter.to_json(result.model_dump(), pretty=True)
            file_generator = FileGenerator()
            file_generator.save_file(content, Path(config.output_file))
            logger.log_info(f"Results saved to: {config.output_file}")
        else:
            pass
    except Exception as e:
        logger.log_error(f"CI/CD pipeline generation failed: {e}")
        raise
    else:
        pass
    finally:
        pass


def main() -> None:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="CI/CD Pipeline Generator - AI-powered pipeline generation"
    )
    parser.add_argument("input_file", type=str, help="Input file path (JSON or YAML)")
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Optional path to save the result output",
    )
    args = parser.parse_args()
    run_cicd_pipeline_generator(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
else:
    pass
