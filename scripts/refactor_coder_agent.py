#!/usr/bin/env python3
"""
Automated refactoring script for CoderAgent modularization.
This script performs the safe, incremental refactoring of the monolithic CoderAgent.
"""

import os
import ast
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import argparse
import json
from datetime import datetime

class CoderAgentRefactorer:
    """Automated refactoring tool for CoderAgent modularization."""
    
    def __init__(self, source_path: str, target_path: str, dry_run: bool = True):
        """Initialize refactorer with paths and options."""
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.dry_run = dry_run
        self.backup_path = self.source_path.parent / f"coder_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        self.extracted_modules = {}
        self.method_mapping = {}
        self.import_mapping = {}
        
    def analyze_source(self) -> Dict[str, Any]:
        """Analyze source file to identify components."""
        print(f"Analyzing {self.source_path}...")
        
        with open(self.source_path, 'r') as f:
            source_code = f.read()
            
        tree = ast.parse(source_code)
        
        analysis = {
            'total_lines': len(source_code.splitlines()),
            'classes': [],
            'methods': [],
            'generators': [],
            'analyzers': [],
            'optimizers': [],
            'transformers': [],
            'templates': [],
            'utilities': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == 'CoderAgent':
                    # Analyze methods in CoderAgent class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_name = item.name
                            analysis['methods'].append({
                                'name': method_name,
                                'line': item.lineno,
                                'category': self._categorize_method(method_name)
                            })
                            
                            # Categorize by type
                            if '_generate_' in method_name:
                                analysis['generators'].append(method_name)
                            elif '_analyze_' in method_name or '_extract_' in method_name:
                                analysis['analyzers'].append(method_name)
                            elif '_optimize_' in method_name:
                                analysis['optimizers'].append(method_name)
                            elif '_refactor_' in method_name or '_transform_' in method_name:
                                analysis['transformers'].append(method_name)
                else:
                    analysis['classes'].append(node.name)
        
        return analysis
    
    def _categorize_method(self, method_name: str) -> str:
        """Categorize method by its name pattern."""
        patterns = {
            'generator': ['_generate_', 'generate_'],
            'analyzer': ['_analyze_', '_extract_', '_detect_', '_calculate_'],
            'optimizer': ['_optimize_'],
            'transformer': ['_refactor_', '_transform_', '_convert_', '_fix_'],
            'template': ['_register_templates', '_apply_template'],
            'utility': ['_build_', '_format_', '_validate_', '_create_']
        }
        
        for category, keywords in patterns.items():
            if any(keyword in method_name for keyword in keywords):
                return category
        
        return 'core'
    
    def create_module_structure(self):
        """Create the new modular directory structure."""
        print("Creating module structure...")
        
        modules = [
            'coder/__init__.py',
            'coder/agent.py',
            'coder/types.py',
            'coder/generators/__init__.py',
            'coder/generators/base.py',
            'coder/generators/python/__init__.py',
            'coder/generators/python/generator.py',
            'coder/generators/python/templates.py',
            'coder/generators/javascript/__init__.py',
            'coder/generators/javascript/generator.py',
            'coder/generators/web_frameworks/__init__.py',
            'coder/generators/web_frameworks/react.py',
            'coder/generators/compiled/__init__.py',
            'coder/generators/compiled/java.py',
            'coder/generators/compiled/go.py',
            'coder/generators/compiled/rust.py',
            'coder/analyzers/__init__.py',
            'coder/analyzers/base.py',
            'coder/analyzers/description.py',
            'coder/analyzers/code_issues.py',
            'coder/analyzers/metrics.py',
            'coder/transformers/__init__.py',
            'coder/transformers/base.py',
            'coder/transformers/refactorer.py',
            'coder/transformers/optimizer.py',
            'coder/optimizers/__init__.py',
            'coder/optimizers/base.py',
            'coder/optimizers/speed.py',
            'coder/optimizers/memory.py',
            'coder/templates/__init__.py',
            'coder/templates/manager.py',
            'coder/utils/__init__.py',
            'coder/utils/validation.py',
            'coder/utils/formatting.py'
        ]
        
        for module_path in modules:
            full_path = self.target_path / module_path
            
            if self.dry_run:
                print(f"  [DRY RUN] Would create: {full_path}")
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if not full_path.exists():
                    full_path.touch()
                    print(f"  Created: {full_path}")
    
    def extract_generators(self):
        """Extract language-specific generators to separate modules."""
        print("Extracting generators...")
        
        with open(self.source_path, 'r') as f:
            source_lines = f.readlines()
        
        # Language to module mapping
        language_modules = {
            'python': 'generators/python/generator.py',
            'javascript': 'generators/javascript/generator.py',
            'typescript': 'generators/javascript/typescript.py',
            'react': 'generators/web_frameworks/react.py',
            'java': 'generators/compiled/java.py',
            'go': 'generators/compiled/go.py',
            'rust': 'generators/compiled/rust.py'
        }
        
        # Extract methods for each language
        for language, module_path in language_modules.items():
            methods = self._extract_language_methods(source_lines, language)
            if methods:
                self._create_generator_module(module_path, language, methods)
    
    def _extract_language_methods(self, source_lines: List[str], language: str) -> List[str]:
        """Extract methods related to a specific language."""
        methods = []
        pattern = f"def _generate_{language}"
        
        in_method = False
        current_method = []
        indent_level = 0
        
        for line in source_lines:
            if pattern in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                current_method = [line]
            elif in_method:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level and line.strip().startswith('def '):
                    # End of current method
                    methods.append(''.join(current_method))
                    in_method = False
                    current_method = []
                else:
                    current_method.append(line)
        
        # Don't forget the last method
        if current_method:
            methods.append(''.join(current_method))
        
        return methods
    
    def _create_generator_module(self, module_path: str, language: str, methods: List[str]):
        """Create a generator module with extracted methods."""
        full_path = self.target_path / 'coder' / module_path
        
        module_content = f'''"""
{language.capitalize()} code generator module.
Extracted from monolithic CoderAgent.
"""

from typing import Dict, Any, List, Optional
from ...base import BaseGenerator
from ...types import Language, CodeSnippet

class {language.capitalize()}Generator(BaseGenerator):
    """Generator for {language.capitalize()} code."""
    
    def __init__(self):
        """Initialize {language} generator."""
        super().__init__()
        self.language = Language.{language.upper() if language.upper() in ['PYTHON', 'JAVASCRIPT', 'JAVA', 'GO', 'RUST'] else 'PYTHON'}
        self.templates = {{}}
        self._register_templates()
    
    def generate(self, description: str, style: Dict[str, Any]) -> str:
        """Generate {language} code from description."""
        # Main generation logic
        return self._generate_{language}(description, style)
    
    def get_templates(self) -> Dict[str, str]:
        """Return available templates."""
        return self.templates
    
    def validate_output(self, code: str) -> bool:
        """Validate generated {language} code."""
        # Add validation logic
        return True
    
    def _register_templates(self):
        """Register {language}-specific templates."""
        # Template registration logic
        pass

'''
        
        # Add extracted methods
        for method in methods:
            # Adjust indentation to class level
            adjusted_method = self._adjust_method_indentation(method)
            module_content += adjusted_method + '\n'
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create {language} generator at: {full_path}")
            print(f"    with {len(methods)} methods")
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(module_content)
            print(f"  Created {language} generator: {full_path}")
            print(f"    Extracted {len(methods)} methods")
    
    def _adjust_method_indentation(self, method: str) -> str:
        """Adjust method indentation for class context."""
        lines = method.splitlines()
        if not lines:
            return method
        
        # Find the base indentation
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        
        # Adjust each line
        adjusted_lines = []
        for line in lines:
            if line.strip():
                current_indent = len(line) - len(line.lstrip())
                relative_indent = current_indent - base_indent
                new_line = '    ' + (' ' * relative_indent) + line.lstrip()
                adjusted_lines.append(new_line)
            else:
                adjusted_lines.append('')
        
        return '\n'.join(adjusted_lines)
    
    def create_facade_agent(self):
        """Create the main facade agent that uses the modules."""
        print("Creating facade agent...")
        
        facade_content = '''"""
Refactored CoderAgent using modular architecture.
This is the main facade that orchestrates all subsystems.
"""

from typing import Any, Dict, Optional
from ..core import BaseAgent, AgentConfig, AgentResult
from .generators import GeneratorFactory
from .analyzers import AnalyzerEngine
from .transformers import TransformerEngine
from .optimizers import OptimizerEngine
from .templates import TemplateManager
import structlog

logger = structlog.get_logger()

class CoderAgent(BaseAgent):
    """
    Refactored CoderAgent with modular architecture.
    
    This facade orchestrates specialized subsystems for:
    - Code generation (multi-language)
    - Code analysis and metrics
    - Code transformation and refactoring
    - Optimization strategies
    - Template management
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize modular coder agent."""
        default_config = AgentConfig(
            name="CoderAgent",
            max_iterations=5,
            timeout=120
        )
        super().__init__(config or default_config)
        
        # Initialize subsystems
        self.generator_factory = GeneratorFactory()
        self.analyzer_engine = AnalyzerEngine()
        self.transformer_engine = TransformerEngine()
        self.optimizer_engine = OptimizerEngine()
        self.template_manager = TemplateManager()
        
        logger.info("coder_agent_initialized", 
                   agent=self.config.name,
                   architecture="modular")
    
    def initialize(self) -> bool:
        """Initialize the coder agent and its subsystems."""
        try:
            # Initialize each subsystem
            self.generator_factory.initialize()
            self.analyzer_engine.initialize()
            self.transformer_engine.initialize()
            self.optimizer_engine.initialize()
            self.template_manager.load_templates()
            
            logger.info("subsystems_initialized")
            return True
        except Exception as e:
            logger.error("initialization_failed", error=str(e))
            return False
    
    def _execute(self, prompt: str, **kwargs) -> Any:
        """Execute from prompt - BaseAgent abstract method implementation."""
        task = {"description": prompt}
        task.update(kwargs)
        
        # Analyze prompt to determine action
        action = self._determine_action(prompt)
        task["action"] = action
        
        return self.execute(task)
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coding task using appropriate subsystem."""
        action = task.get("action", "generate")
        
        try:
            if action == "generate":
                return self._handle_generation(task)
            elif action == "refactor":
                return self._handle_refactoring(task)
            elif action == "optimize":
                return self._handle_optimization(task)
            elif action == "analyze":
                return self._handle_analysis(task)
            elif action == "fix":
                return self._handle_fixing(task)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error("execution_failed", action=action, error=str(e))
            return {"error": str(e)}
    
    def _determine_action(self, prompt: str) -> str:
        """Determine action from prompt text."""
        prompt_lower = prompt.lower()
        
        action_keywords = {
            "refactor": ["refactor", "restructure", "reorganize"],
            "optimize": ["optimize", "improve performance", "speed up"],
            "fix": ["fix", "debug", "correct", "repair"],
            "analyze": ["analyze", "review", "examine", "inspect"],
            "generate": ["generate", "create", "build", "write"]
        }
        
        for action, keywords in action_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return action
        
        return "generate"  # Default action
    
    def _handle_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation using generator factory."""
        language = task.get("language", "python")
        description = task.get("description", "")
        style = task.get("style", {})
        
        # Get appropriate generator
        generator = self.generator_factory.get_generator(language)
        
        # Analyze description
        analysis = self.analyzer_engine.analyze_description(description)
        
        # Generate code
        code = generator.generate(description, style)
        
        # Apply templates if needed
        if analysis.get("use_template"):
            template_name = analysis.get("template_name")
            code = self.template_manager.apply_template(code, template_name)
        
        return {
            "code": code,
            "language": language,
            "analysis": analysis
        }
    
    def _handle_refactoring(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code refactoring using transformer engine."""
        code = task.get("code", "")
        language = task.get("language", "python")
        refactoring_type = task.get("refactoring_type", "general")
        
        # Analyze code first
        analysis = self.analyzer_engine.analyze_code(code, language)
        
        # Apply refactoring
        refactored_code = self.transformer_engine.refactor(
            code, language, refactoring_type, analysis
        )
        
        # Calculate improvements
        metrics_before = analysis.get("metrics", {})
        metrics_after = self.analyzer_engine.calculate_metrics(refactored_code, language)
        
        return {
            "original_code": code,
            "refactored_code": refactored_code,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
            "improvements": self._calculate_improvements(metrics_before, metrics_after)
        }
    
    def _handle_optimization(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code optimization using optimizer engine."""
        code = task.get("code", "")
        language = task.get("language", "python")
        optimization_type = task.get("optimization_type", "speed")
        
        # Analyze current performance
        analysis = self.analyzer_engine.analyze_performance(code, language)
        
        # Apply optimizations
        optimized_code = self.optimizer_engine.optimize(
            code, language, optimization_type, analysis
        )
        
        return {
            "original_code": code,
            "optimized_code": optimized_code,
            "optimization_type": optimization_type,
            "performance_analysis": analysis
        }
    
    def _handle_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis using analyzer engine."""
        code = task.get("code", "")
        language = task.get("language", "python")
        analysis_type = task.get("analysis_type", "comprehensive")
        
        # Perform analysis
        analysis = self.analyzer_engine.analyze(code, language, analysis_type)
        
        return {
            "code": code,
            "language": language,
            "analysis": analysis
        }
    
    def _handle_fixing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code fixing using transformer engine."""
        code = task.get("code", "")
        language = task.get("language", "python")
        
        # Analyze issues
        issues = self.analyzer_engine.detect_issues(code, language)
        
        # Fix issues
        fixed_code = self.transformer_engine.fix_issues(code, language, issues)
        
        # Validate fixes
        validation = self.analyzer_engine.validate_code(fixed_code, language)
        
        return {
            "original_code": code,
            "fixed_code": fixed_code,
            "issues_found": issues,
            "validation": validation
        }
    
    def _calculate_improvements(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvements between before and after metrics."""
        improvements = {}
        
        for metric in ["complexity", "lines_of_code", "functions", "classes"]:
            if metric in before and metric in after:
                before_val = before[metric]
                after_val = after[metric]
                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    if before_val > 0:
                        improvement = ((before_val - after_val) / before_val) * 100
                        improvements[metric] = f"{improvement:.1f}% reduction"
        
        return improvements
'''
        
        facade_path = self.target_path / 'coder' / 'agent.py'
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create facade agent at: {facade_path}")
        else:
            with open(facade_path, 'w') as f:
                f.write(facade_content)
            print(f"  Created facade agent: {facade_path}")
    
    def create_compatibility_wrapper(self):
        """Create backward compatibility wrapper."""
        print("Creating compatibility wrapper...")
        
        wrapper_content = '''"""
Backward compatibility wrapper for CoderAgent.
Allows gradual migration from monolithic to modular architecture.
"""

from typing import Optional
from ..core import AgentConfig

# Feature flag for gradual migration
USE_MODULAR_ARCHITECTURE = False

if USE_MODULAR_ARCHITECTURE:
    from .coder.agent import CoderAgent as ModularCoderAgent
    
    class CoderAgent(ModularCoderAgent):
        """Wrapper using new modular architecture."""
        pass
else:
    from .coder_legacy import CoderAgent as LegacyCoderAgent
    
    class CoderAgent(LegacyCoderAgent):
        """Wrapper using legacy monolithic architecture."""
        pass

# Export the appropriate version
__all__ = ['CoderAgent']
'''
        
        wrapper_path = self.target_path / 'coder.py'
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create compatibility wrapper at: {wrapper_path}")
        else:
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_content)
            print(f"  Created compatibility wrapper: {wrapper_path}")
    
    def backup_original(self):
        """Create backup of original file."""
        if not self.dry_run:
            shutil.copy2(self.source_path, self.backup_path)
            print(f"Created backup: {self.backup_path}")
        else:
            print(f"[DRY RUN] Would create backup: {self.backup_path}")
    
    def generate_report(self, analysis: Dict[str, Any]):
        """Generate refactoring report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': str(self.source_path),
            'target_directory': str(self.target_path),
            'analysis': analysis,
            'modules_created': list(self.extracted_modules.keys()),
            'dry_run': self.dry_run
        }
        
        report_path = self.target_path / 'refactoring_report.json'
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would save report to: {report_path}")
            print(json.dumps(report, indent=2))
        else:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nSaved report to: {report_path}")
    
    def refactor(self):
        """Execute the full refactoring process."""
        print("\n" + "="*60)
        print("CoderAgent Refactoring Tool")
        print("="*60)
        
        if self.dry_run:
            print("MODE: DRY RUN - No files will be modified")
        else:
            print("MODE: LIVE - Files will be created/modified")
        
        print("\n" + "-"*40)
        
        # Step 1: Analyze source
        analysis = self.analyze_source()
        print(f"\nSource Analysis:")
        print(f"  Total lines: {analysis['total_lines']}")
        print(f"  Methods: {len(analysis['methods'])}")
        print(f"  Generators: {len(analysis['generators'])}")
        print(f"  Analyzers: {len(analysis['analyzers'])}")
        print(f"  Optimizers: {len(analysis['optimizers'])}")
        
        # Step 2: Backup original
        if not self.dry_run:
            self.backup_original()
        
        # Step 3: Create module structure
        print("\n" + "-"*40)
        self.create_module_structure()
        
        # Step 4: Extract generators
        print("\n" + "-"*40)
        self.extract_generators()
        
        # Step 5: Create facade agent
        print("\n" + "-"*40)
        self.create_facade_agent()
        
        # Step 6: Create compatibility wrapper
        print("\n" + "-"*40)
        self.create_compatibility_wrapper()
        
        # Step 7: Generate report
        print("\n" + "-"*40)
        self.generate_report(analysis)
        
        print("\n" + "="*60)
        print("Refactoring Complete!")
        if self.dry_run:
            print("This was a DRY RUN. To execute, run without --dry-run flag")
        print("="*60 + "\n")


def main():
    """Main entry point for refactoring script."""
    parser = argparse.ArgumentParser(
        description="Refactor monolithic CoderAgent into modular architecture"
    )
    parser.add_argument(
        '--source',
        default='/home/opsvi/master_root/libs/opsvi-agents/opsvi_agents/core_agents/coder.py',
        help='Path to source coder.py file'
    )
    parser.add_argument(
        '--target',
        default='/home/opsvi/master_root/libs/opsvi-agents/opsvi_agents/core_agents',
        help='Target directory for modular structure'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without modifying files'
    )
    
    args = parser.parse_args()
    
    refactorer = CoderAgentRefactorer(
        source_path=args.source,
        target_path=args.target,
        dry_run=args.dry_run
    )
    
    refactorer.refactor()


if __name__ == '__main__':
    main()