#!/usr/bin/env python3
"""
Dashboard Readiness Validation
Comprehensive check of dashboard components and integration
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardReadinessValidator:
    """Validates dashboard readiness for production deployment"""

    def __init__(self):
        self.dashboard_path = Path(
            "/home/opsvi/master_root/apps/project-context/dashboard"
        )
        self.backend_path = self.dashboard_path / "backend"
        self.frontend_path = self.dashboard_path / "frontend"

        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "component_checks": {},
            "integration_checks": {},
            "data_source_checks": {},
            "deployment_readiness": {},
            "recommendations": [],
        }

    def validate_dashboard_readiness(self) -> Dict:
        """Execute comprehensive readiness validation"""
        logger.info("🔍 Starting Dashboard Readiness Validation...")

        try:
            # 1. Component Structure Validation
            self.validate_component_structure()

            # 2. Backend Components Validation
            self.validate_backend_components()

            # 3. Frontend Components Validation
            self.validate_frontend_components()

            # 4. Data Source Integration
            self.validate_data_sources()

            # 5. Configuration Validation
            self.validate_configuration()

            # 6. Deployment Readiness
            self.validate_deployment_readiness()

            # 7. Generate Overall Assessment
            self.generate_overall_assessment()

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            self.validation_results["overall_status"] = "failed"
            self.validation_results["error"] = str(e)
            self.validation_results["traceback"] = traceback.format_exc()

        return self.validation_results

    def validate_component_structure(self):
        """Validate dashboard directory structure and required files"""
        logger.info("📁 Validating component structure...")

        required_paths = {
            "dashboard_root": self.dashboard_path,
            "backend_directory": self.backend_path,
            "frontend_directory": self.frontend_path,
            "backend_app": self.backend_path / "app.py",
            "monitoring_service": self.backend_path / "monitoring_service.py",
            "websocket_handler": self.backend_path / "websocket_handler.py",
            "frontend_html": self.frontend_path / "index.html",
            "frontend_js": self.frontend_path / "js",
            "frontend_css": self.frontend_path / "styles.css",
        }

        structure_check = {
            "required_files_present": 0,
            "required_files_total": len(required_paths),
            "missing_files": [],
            "present_files": [],
        }

        for name, path in required_paths.items():
            if path.exists():
                structure_check["required_files_present"] += 1
                structure_check["present_files"].append(str(path))
            else:
                structure_check["missing_files"].append(str(path))
                logger.warning(f"❌ Missing required file/directory: {path}")

        structure_check["structure_complete"] = (
            len(structure_check["missing_files"]) == 0
        )
        self.validation_results["component_checks"]["structure"] = structure_check

        if structure_check["structure_complete"]:
            logger.info("✅ Component structure validation passed")
        else:
            logger.error(
                f"❌ Component structure incomplete: {len(structure_check['missing_files'])} files missing"
            )

    def validate_backend_components(self):
        """Validate backend Python components"""
        logger.info("🐍 Validating backend components...")

        backend_check = {
            "imports_valid": False,
            "fastapi_app_valid": False,
            "monitoring_service_valid": False,
            "websocket_handler_valid": False,
            "api_endpoints_present": False,
            "error_details": [],
        }

        # Test imports
        sys.path.insert(0, str(self.backend_path))

        try:
            # Test monitoring service import
            from monitoring_service import MonitoringService

            backend_check["monitoring_service_valid"] = True
            logger.info("✅ MonitoringService import successful")
        except Exception as e:
            backend_check["error_details"].append(
                f"MonitoringService import failed: {e}"
            )
            logger.error(f"❌ MonitoringService import failed: {e}")

        try:
            # Test websocket handler import
            from websocket_handler import WebSocketManager

            backend_check["websocket_handler_valid"] = True
            logger.info("✅ WebSocketManager import successful")
        except Exception as e:
            backend_check["error_details"].append(
                f"WebSocketManager import failed: {e}"
            )
            logger.error(f"❌ WebSocketManager import failed: {e}")

        try:
            # Test FastAPI app import
            from app import app

            backend_check["fastapi_app_valid"] = True

            # Check for required routes
            routes = [route.path for route in app.routes]
            required_routes = ["/api/status", "/api/tasks", "/api/performance", "/ws"]
            missing_routes = [route for route in required_routes if route not in routes]

            if not missing_routes:
                backend_check["api_endpoints_present"] = True
                logger.info("✅ All required API endpoints present")
            else:
                backend_check["error_details"].append(
                    f"Missing routes: {missing_routes}"
                )
                logger.error(f"❌ Missing routes: {missing_routes}")

        except Exception as e:
            backend_check["error_details"].append(f"FastAPI app import failed: {e}")
            logger.error(f"❌ FastAPI app import failed: {e}")

        backend_check["imports_valid"] = (
            backend_check["monitoring_service_valid"]
            and backend_check["websocket_handler_valid"]
            and backend_check["fastapi_app_valid"]
        )

        self.validation_results["component_checks"]["backend"] = backend_check

    def validate_frontend_components(self):
        """Validate frontend components and files"""
        logger.info("🌐 Validating frontend components...")

        frontend_check = {
            "html_structure_valid": False,
            "javascript_files_present": 0,
            "css_files_present": 0,
            "required_js_modules": 0,
            "missing_components": [],
        }

        # Check HTML structure
        html_file = self.frontend_path / "index.html"
        if html_file.exists():
            try:
                html_content = html_file.read_text()
                required_elements = [
                    "dashboard-container",
                    "executive-summary",
                    "task-monitoring",
                    "performance-charts",
                ]
                present_elements = [
                    elem for elem in required_elements if elem in html_content
                ]

                if len(present_elements) == len(required_elements):
                    frontend_check["html_structure_valid"] = True
                    logger.info("✅ HTML structure validation passed")
                else:
                    missing = set(required_elements) - set(present_elements)
                    frontend_check["missing_components"].extend(missing)
                    logger.warning(f"❌ Missing HTML elements: {missing}")

            except Exception as e:
                logger.error(f"❌ HTML validation error: {e}")

        # Check JavaScript files
        js_dir = self.frontend_path / "js"
        if js_dir.exists():
            js_files = list(js_dir.glob("*.js"))
            frontend_check["javascript_files_present"] = len(js_files)

            required_js = [
                "dashboard.js",
                "api-client.js",
                "websocket-manager.js",
                "chart-manager.js",
            ]
            present_js = [f.name for f in js_files]
            missing_js = [js for js in required_js if js not in present_js]

            if not missing_js:
                frontend_check["required_js_modules"] = len(required_js)
                logger.info("✅ All required JavaScript modules present")
            else:
                frontend_check["missing_components"].extend(missing_js)
                logger.warning(f"❌ Missing JavaScript modules: {missing_js}")

        # Check CSS files
        css_files = list(self.frontend_path.glob("*.css"))
        frontend_check["css_files_present"] = len(css_files)

        if css_files:
            logger.info(f"✅ Found {len(css_files)} CSS files")
        else:
            logger.warning("❌ No CSS files found")

        self.validation_results["component_checks"]["frontend"] = frontend_check

    def validate_data_sources(self):
        """Validate orchestrator data source integration"""
        logger.info("📊 Validating data sources...")

        data_check = {
            "orchestrator_output_dirs": 0,
            "valid_task_files": 0,
            "sample_data_valid": False,
            "data_directories": [],
        }

        # Check for orchestrator output directories
        project_root = Path("/home/opsvi/master_root/apps/project-context")
        output_patterns = ["*_output", "*_completion_*", "dashboard_output"]

        for pattern in output_patterns:
            matching_dirs = list(project_root.glob(pattern))
            for dir_path in matching_dirs:
                if dir_path.is_dir():
                    tasks_dir = dir_path / "tasks"
                    if tasks_dir.exists():
                        json_files = list(tasks_dir.glob("*.json"))
                        data_check["orchestrator_output_dirs"] += 1
                        data_check["valid_task_files"] += len(json_files)
                        data_check["data_directories"].append(
                            {"path": str(dir_path), "task_files": len(json_files)}
                        )

        # Validate sample data
        if data_check["valid_task_files"] > 0:
            # Try to read a sample task file
            for dir_info in data_check["data_directories"]:
                dir_path = Path(dir_info["path"]) / "tasks"
                if dir_path.exists():
                    json_files = list(dir_path.glob("*.json"))
                    if json_files:
                        try:
                            sample_file = json_files[0]
                            with open(sample_file, "r") as f:
                                sample_data = json.load(f)

                            # Validate sample data structure
                            required_fields = ["task_id", "status", "task_type"]
                            if all(field in sample_data for field in required_fields):
                                data_check["sample_data_valid"] = True
                                logger.info("✅ Sample data validation passed")
                                break
                        except Exception as e:
                            logger.error(f"❌ Sample data validation failed: {e}")

        if data_check["orchestrator_output_dirs"] > 0:
            logger.info(
                f"✅ Found {data_check['orchestrator_output_dirs']} output directories with {data_check['valid_task_files']} task files"
            )
        else:
            logger.warning("❌ No orchestrator output directories found")

        self.validation_results["data_source_checks"] = data_check

    def validate_configuration(self):
        """Validate configuration and dependencies"""
        logger.info("⚙️ Validating configuration...")

        config_check = {
            "python_dependencies": self._check_python_dependencies(),
            "ports_available": self._check_port_availability(),
            "file_permissions": self._check_file_permissions(),
        }

        self.validation_results["component_checks"]["configuration"] = config_check

    def _check_python_dependencies(self) -> Dict:
        """Check required Python dependencies"""
        required_packages = ["fastapi", "uvicorn", "websockets", "psutil"]
        dependency_check = {"available": [], "missing": []}

        for package in required_packages:
            try:
                __import__(package)
                dependency_check["available"].append(package)
            except ImportError:
                dependency_check["missing"].append(package)

        return dependency_check

    def _check_port_availability(self) -> Dict:
        """Check if required ports are available"""
        import socket

        ports_to_check = [8000, 8001]  # Common dashboard ports
        port_check = {"available": [], "in_use": []}

        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(("localhost", port))
                port_check["available"].append(port)
            except OSError:
                port_check["in_use"].append(port)
            finally:
                sock.close()

        return port_check

    def _check_file_permissions(self) -> Dict:
        """Check file permissions for key components"""
        files_to_check = [
            self.backend_path / "app.py",
            self.frontend_path / "index.html",
        ]

        permission_check = {"readable": [], "permission_issues": []}

        for file_path in files_to_check:
            if file_path.exists():
                if (
                    file_path.is_file() and file_path.stat().st_mode & 0o444
                ):  # Check read permission
                    permission_check["readable"].append(str(file_path))
                else:
                    permission_check["permission_issues"].append(str(file_path))

        return permission_check

    def validate_deployment_readiness(self):
        """Validate deployment readiness"""
        logger.info("🚀 Validating deployment readiness...")

        deployment_check = {
            "all_components_present": False,
            "backend_functional": False,
            "frontend_functional": False,
            "data_integration_ready": False,
            "production_ready": False,
        }

        # Check component completeness
        structure_ok = (
            self.validation_results.get("component_checks", {})
            .get("structure", {})
            .get("structure_complete", False)
        )
        backend_ok = (
            self.validation_results.get("component_checks", {})
            .get("backend", {})
            .get("imports_valid", False)
        )
        frontend_ok = (
            self.validation_results.get("component_checks", {})
            .get("frontend", {})
            .get("html_structure_valid", False)
        )

        deployment_check["all_components_present"] = structure_ok
        deployment_check["backend_functional"] = backend_ok
        deployment_check["frontend_functional"] = frontend_ok

        # Check data integration
        data_ok = self.validation_results.get("data_source_checks", {}).get(
            "sample_data_valid", False
        )
        deployment_check["data_integration_ready"] = data_ok

        # Overall production readiness
        deployment_check["production_ready"] = all(
            [
                deployment_check["all_components_present"],
                deployment_check["backend_functional"],
                deployment_check["frontend_functional"],
                deployment_check["data_integration_ready"],
            ]
        )

        self.validation_results["deployment_readiness"] = deployment_check

        if deployment_check["production_ready"]:
            logger.info("✅ Dashboard is production ready!")
        else:
            logger.warning(
                "❌ Dashboard needs additional work before production deployment"
            )

    def generate_overall_assessment(self):
        """Generate overall assessment and recommendations"""
        logger.info("📋 Generating overall assessment...")

        # Calculate overall score
        checks = self.validation_results["component_checks"]
        data_checks = self.validation_results["data_source_checks"]
        deployment = self.validation_results["deployment_readiness"]

        score_components = [
            checks.get("structure", {}).get("structure_complete", False),
            checks.get("backend", {}).get("imports_valid", False),
            checks.get("frontend", {}).get("html_structure_valid", False),
            data_checks.get("sample_data_valid", False),
            deployment.get("production_ready", False),
        ]

        score = sum(score_components) / len(score_components) * 100

        if score >= 90:
            self.validation_results["overall_status"] = "excellent"
        elif score >= 80:
            self.validation_results["overall_status"] = "good"
        elif score >= 70:
            self.validation_results["overall_status"] = "satisfactory"
        else:
            self.validation_results["overall_status"] = "needs_improvement"

        # Generate recommendations
        recommendations = []

        if not checks.get("structure", {}).get("structure_complete", False):
            recommendations.append("📁 Complete dashboard directory structure")

        if not checks.get("backend", {}).get("imports_valid", False):
            recommendations.append("🐍 Fix backend component imports and dependencies")

        if not checks.get("frontend", {}).get("html_structure_valid", False):
            recommendations.append("🌐 Improve frontend component structure")

        if not data_checks.get("sample_data_valid", False):
            recommendations.append("📊 Verify orchestrator data integration")

        if not deployment.get("production_ready", False):
            recommendations.append("🚀 Address deployment readiness issues")

        if not recommendations:
            recommendations.append(
                "✅ Dashboard validation passed - ready for production!"
            )

        self.validation_results["recommendations"] = recommendations
        self.validation_results["readiness_score"] = score

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        results = self.validation_results

        report = f"""
# Dashboard Readiness Validation Report

## Overall Assessment
- **Status**: {results.get('overall_status', 'unknown').upper()}
- **Readiness Score**: {results.get('readiness_score', 0):.1f}%
- **Production Ready**: {'✅ YES' if results.get('deployment_readiness', {}).get('production_ready') else '❌ NO'}
- **Timestamp**: {results.get('timestamp')}

## Component Validation

### Structure
- **Complete**: {'✅ YES' if results.get('component_checks', {}).get('structure', {}).get('structure_complete') else '❌ NO'}
- **Required Files**: {results.get('component_checks', {}).get('structure', {}).get('required_files_present', 0)}/{results.get('component_checks', {}).get('structure', {}).get('required_files_total', 0)}

### Backend Components
- **Imports Valid**: {'✅ YES' if results.get('component_checks', {}).get('backend', {}).get('imports_valid') else '❌ NO'}
- **FastAPI App**: {'✅ OK' if results.get('component_checks', {}).get('backend', {}).get('fastapi_app_valid') else '❌ FAIL'}
- **API Endpoints**: {'✅ OK' if results.get('component_checks', {}).get('backend', {}).get('api_endpoints_present') else '❌ FAIL'}

### Frontend Components
- **HTML Structure**: {'✅ OK' if results.get('component_checks', {}).get('frontend', {}).get('html_structure_valid') else '❌ FAIL'}
- **JavaScript Files**: {results.get('component_checks', {}).get('frontend', {}).get('javascript_files_present', 0)}
- **CSS Files**: {results.get('component_checks', {}).get('frontend', {}).get('css_files_present', 0)}

### Data Sources
- **Output Directories**: {results.get('data_source_checks', {}).get('orchestrator_output_dirs', 0)}
- **Task Files**: {results.get('data_source_checks', {}).get('valid_task_files', 0)}
- **Sample Data Valid**: {'✅ YES' if results.get('data_source_checks', {}).get('sample_data_valid') else '❌ NO'}

## Recommendations
"""

        for rec in results.get("recommendations", []):
            report += f"- {rec}\n"

        return report


def main():
    """Main validation runner"""
    validator = DashboardReadinessValidator()

    # Run validation
    results = validator.validate_dashboard_readiness()

    # Generate report
    report = validator.generate_validation_report()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(
        f"/home/opsvi/master_root/apps/project-context/dashboard/validation_results_{timestamp}.json"
    )
    report_file = Path(
        f"/home/opsvi/master_root/apps/project-context/dashboard/validation_report_{timestamp}.md"
    )

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    with open(report_file, "w") as f:
        f.write(report)

    # Display summary
    print(report)

    logger.info(f"✅ Validation completed. Results saved to {results_file}")
    logger.info(f"📊 Validation report saved to {report_file}")

    # Return appropriate exit code
    return 0 if results.get("deployment_readiness", {}).get("production_ready") else 1


if __name__ == "__main__":
    exit(main())
