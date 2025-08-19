"""
Real Implementation Pipeline using actual MCP tools

No simulations, no stubs - actual implementation of TODOs.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .todo_discovery import TodoItem
from .real_mcp_integration import RealMCPIntegration

logger = logging.getLogger(__name__)


@dataclass
class RealImplementationResult:
    """Result of an actual TODO implementation"""
    
    todo_id: str
    status: str  # success, failure, partial
    files_modified: List[str]
    tests_created: List[str]
    lines_changed: int
    test_passed: bool
    knowledge_stored: bool
    error_message: Optional[str]
    duration_seconds: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "todo_id": self.todo_id,
            "status": self.status,
            "files_modified": self.files_modified,
            "tests_created": self.tests_created,
            "lines_changed": self.lines_changed,
            "test_passed": self.test_passed,
            "knowledge_stored": self.knowledge_stored,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp
        }


class RealImplementationPipeline:
    """Pipeline that actually implements TODOs using real MCP tools"""
    
    def __init__(self, project_root: str = "/home/opsvi/master_root"):
        self.project_root = Path(project_root)
        self.mcp = RealMCPIntegration()
        self.results: List[RealImplementationResult] = []
        
    async def implement_todo_for_real(self, todo: TodoItem) -> RealImplementationResult:
        """Actually implement a TODO - no simulation"""
        
        start_time = datetime.now()
        logger.info(f"Starting REAL implementation of TODO: {todo.id}")
        
        try:
            # Convert TodoItem to dict for easier handling
            todo_dict = todo.to_dict()
            
            # Phase 1: Discovery - Understand what needs to be done
            logger.info("Phase 1: Discovery")
            discovery = await self.mcp.execute_discovery(todo_dict)
            
            if discovery.get("status") != "completed":
                raise Exception(f"Discovery failed: {discovery.get('error', 'Unknown error')}")
            
            # Phase 2: Implementation - Actually modify the file
            logger.info("Phase 2: Implementation")
            implementation = await self.mcp.execute_implementation(todo_dict, discovery)
            
            if implementation.get("status") == "error":
                raise Exception(f"Implementation failed: {implementation.get('error', 'Unknown error')}")
            
            files_modified = implementation.get("files_modified", [])
            lines_changed = implementation.get("lines_changed", 0)
            
            # Phase 3: Testing - Generate and run tests
            logger.info("Phase 3: Testing")
            test_result = await self.mcp.execute_test_generation(todo_dict, implementation)
            
            tests_created = test_result.get("tests_created", [])
            test_passed = test_result.get("passed", False)
            
            # Phase 4: Knowledge Storage - Store what we learned
            logger.info("Phase 4: Knowledge Storage")
            knowledge_stored = await self._store_knowledge(
                todo, 
                implementation, 
                test_result,
                success=test_passed
            )
            
            # Determine overall status
            if files_modified and test_passed:
                status = "success"
            elif files_modified:
                status = "partial"  # Code changed but tests failed
            else:
                status = "failure"
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RealImplementationResult(
                todo_id=todo.id,
                status=status,
                files_modified=files_modified,
                tests_created=tests_created,
                lines_changed=lines_changed,
                test_passed=test_passed,
                knowledge_stored=knowledge_stored,
                error_message=None,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"TODO {todo.id} implementation {status}. Files modified: {len(files_modified)}, Tests: {len(tests_created)}")
            
        except Exception as e:
            logger.error(f"Failed to implement TODO {todo.id}: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = RealImplementationResult(
                todo_id=todo.id,
                status="failure",
                files_modified=[],
                tests_created=[],
                lines_changed=0,
                test_passed=False,
                knowledge_stored=False,
                error_message=str(e),
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )
        
        self.results.append(result)
        return result
    
    async def _store_knowledge(self, 
                              todo: TodoItem,
                              implementation: Dict[str, Any],
                              test_result: Dict[str, Any],
                              success: bool) -> bool:
        """Store knowledge about the implementation"""
        
        try:
            knowledge_content = {
                "todo_category": todo.category,
                "complexity": todo.estimated_complexity,
                "implementation_approach": implementation.get("implementation", ""),
                "files_modified": implementation.get("files_modified", []),
                "tests_created": test_result.get("tests_created", []),
                "test_passed": test_result.get("passed", False),
                "success": success
            }
            
            knowledge_type = "TODO_IMPLEMENTATION_SUCCESS" if success else "TODO_IMPLEMENTATION_FAILURE"
            
            stored = await self.mcp.store_knowledge(
                knowledge_type=knowledge_type,
                content=json.dumps(knowledge_content),
                context={
                    "file_path": todo.file_path,
                    "line_number": todo.line_number,
                    "todo_content": todo.content
                },
                confidence=0.9 if success else 0.5
            )
            
            return stored
            
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            return False
    
    async def batch_implement(self, 
                            todos: List[TodoItem],
                            max_parallel: int = 1) -> List[RealImplementationResult]:
        """Implement multiple TODOs - one at a time for safety"""
        
        results = []
        
        for i, todo in enumerate(todos):
            logger.info(f"Processing TODO {i+1}/{len(todos)}")
            result = await self.implement_todo_for_real(todo)
            results.append(result)
            
            # Stop if we get too many failures
            if len([r for r in results if r.status == "failure"]) > 3:
                logger.warning("Too many failures, stopping batch processing")
                break
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a report of actual implementations"""
        
        total = len(self.results)
        successful = len([r for r in self.results if r.status == "success"])
        partial = len([r for r in self.results if r.status == "partial"])
        failed = len([r for r in self.results if r.status == "failure"])
        
        total_files_modified = set()
        total_tests_created = set()
        total_lines_changed = 0
        
        for result in self.results:
            total_files_modified.update(result.files_modified)
            total_tests_created.update(result.tests_created)
            total_lines_changed += result.lines_changed
        
        report = {
            "summary": {
                "total_attempted": total,
                "successful": successful,
                "partial": partial,
                "failed": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "files_modified": len(total_files_modified),
                "tests_created": len(total_tests_created),
                "lines_changed": total_lines_changed,
                "total_duration": sum(r.duration_seconds for r in self.results),
                "average_duration": sum(r.duration_seconds for r in self.results) / total if total > 0 else 0
            },
            "files_modified": list(total_files_modified),
            "tests_created": list(total_tests_created),
            "successes": [r.to_dict() for r in self.results if r.status == "success"],
            "failures": [r.to_dict() for r in self.results if r.status == "failure"],
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def validate_implementation(self, result: RealImplementationResult) -> bool:
        """Validate that an implementation actually happened"""
        
        # Check that files were actually modified
        if not result.files_modified:
            logger.warning(f"TODO {result.todo_id} claims success but no files modified")
            return False
        
        # Check that the files exist and were recently modified
        for file_path in result.files_modified:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Modified file {file_path} does not exist")
                return False
            
            # Check modification time
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if (datetime.now() - mtime).total_seconds() > 300:  # More than 5 minutes old
                logger.warning(f"File {file_path} was not recently modified")
                return False
        
        return True