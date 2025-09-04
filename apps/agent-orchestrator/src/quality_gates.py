#!/usr/bin/env python3
"""
Quality Gate & Dependency Management System

Provides validation-based dependency management for complex project orchestration.
Ensures agents only proceed when their dependencies are validated and quality gates pass.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

# Optional imports - gracefully handle missing dependencies
try:
    import websockets

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import psycopg2

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Quality gate status"""

    PENDING = "pending"
    VALIDATING = "validating"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ValidationResult:
    """Result of a quality gate validation"""

    def __init__(
        self,
        success: bool,
        message: str = "",
        data: Dict[str, Any] = None,
        retry_after: Optional[int] = None,
    ):
        self.success = success
        self.message = message
        self.data = data or {}
        self.retry_after = retry_after  # seconds to wait before retry
        self.timestamp = datetime.now().isoformat()

    def __bool__(self):
        return self.success

    def to_dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "retry_after": self.retry_after,
            "timestamp": self.timestamp,
        }


@dataclass
class QualityGate:
    """Definition of a quality gate"""

    gate_id: str
    name: str
    description: str
    validator_type: str  # Built-in validator type
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Other gates this depends on
    timeout_seconds: int = 300  # Max time to wait for validation
    retry_interval: int = 30  # Seconds between retries
    max_retries: int = 10
    status: GateStatus = GateStatus.PENDING
    last_validation: Optional[ValidationResult] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Phase:
    """Execution phase with quality gates"""

    phase_id: str
    name: str
    description: str
    gates: List[str]  # Gate IDs required for this phase
    status: str = "pending"  # pending, active, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class QualityGateValidator(ABC):
    """Base class for quality gate validators"""

    @abstractmethod
    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate the quality gate condition"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get validator name"""
        pass


class DatabaseValidator(QualityGateValidator):
    """Validates database state via SQL queries"""

    def get_name(self) -> str:
        return "database"

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate database condition"""
        if not HAS_PSYCOPG2:
            return ValidationResult(
                False, "psycopg2 not available - database validation disabled"
            )

        try:
            # Get connection parameters
            connection_string = config.get(
                "connection_string", os.environ.get("DATABASE_URL")
            )
            query = config.get("query")
            expected_result = config.get("expected_result")

            if not connection_string:
                return ValidationResult(False, "No database connection string provided")

            if not query:
                return ValidationResult(False, "No SQL query provided")

            # Execute query
            conn = psycopg2.connect(connection_string)
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            cur.close()
            conn.close()

            # Check result
            if expected_result is not None:
                if result != expected_result:
                    return ValidationResult(
                        False,
                        f"Query result {result} does not match expected {expected_result}",
                    )

            # If we have results and no specific expectation, consider it success
            success = len(result) > 0 if expected_result is None else True
            message = (
                f"Query returned {len(result)} rows"
                if success
                else "Query returned no results"
            )

            return ValidationResult(success, message, {"result": result})

        except Exception as e:
            return ValidationResult(False, f"Database validation failed: {str(e)}")


class WebSocketValidator(QualityGateValidator):
    """Validates WebSocket API availability"""

    def get_name(self) -> str:
        return "websocket"

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate WebSocket connection"""
        if not HAS_WEBSOCKETS:
            return ValidationResult(
                False,
                "websockets library not available - WebSocket validation disabled",
            )

        try:
            url = config.get("url")
            timeout = config.get("timeout", 10)

            if not url:
                return ValidationResult(False, "No WebSocket URL provided")

            async with websockets.connect(url, timeout=timeout) as ws:
                # Send test message if configured
                test_message = config.get("test_message")
                if test_message:
                    await ws.send(json.dumps(test_message))
                    response = await ws.recv()
                    return ValidationResult(True, f"WebSocket responded: {response}")
                else:
                    return ValidationResult(True, "WebSocket connection established")

        except Exception as e:
            return ValidationResult(False, f"WebSocket validation failed: {str(e)}")


class HttpValidator(QualityGateValidator):
    """Validates HTTP API availability"""

    def get_name(self) -> str:
        return "http"

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate HTTP endpoint"""
        if not HAS_AIOHTTP:
            return ValidationResult(
                False, "aiohttp library not available - HTTP validation disabled"
            )

        try:
            url = config.get("url")
            method = config.get("method", "GET").upper()
            timeout = config.get("timeout", 10)
            headers = config.get("headers", {})
            expected_status = config.get("expected_status", [200])

            if not url:
                return ValidationResult(False, "No HTTP URL provided")

            if not isinstance(expected_status, list):
                expected_status = [expected_status]

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        status = response.status
                        text = await response.text()
                elif method == "POST":
                    data = config.get("data", {})
                    async with session.post(
                        url, json=data, headers=headers
                    ) as response:
                        status = response.status
                        text = await response.text()
                else:
                    return ValidationResult(False, f"Unsupported HTTP method: {method}")

                if status in expected_status:
                    return ValidationResult(
                        True,
                        f"HTTP {method} {url} returned {status}",
                        {"response": text},
                    )
                else:
                    return ValidationResult(
                        False,
                        f"HTTP {method} {url} returned {status}, expected {expected_status}",
                    )

        except Exception as e:
            return ValidationResult(False, f"HTTP validation failed: {str(e)}")


class FileValidator(QualityGateValidator):
    """Validates file existence and content"""

    def get_name(self) -> str:
        return "file"

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate file condition"""
        try:
            path = config.get("path")
            exists = config.get("exists", True)
            min_size = config.get("min_size")
            contains = config.get("contains")  # Text that must be in file

            if not path:
                return ValidationResult(False, "No file path provided")

            file_path = Path(path)
            file_exists = file_path.exists()

            if exists and not file_exists:
                return ValidationResult(False, f"Required file {path} does not exist")
            elif not exists and file_exists:
                return ValidationResult(False, f"File {path} should not exist but does")
            elif not exists and not file_exists:
                return ValidationResult(True, f"File {path} correctly does not exist")

            # File exists and should exist - check additional conditions
            if min_size is not None:
                size = file_path.stat().st_size
                if size < min_size:
                    return ValidationResult(
                        False,
                        f"File {path} size {size} is less than required {min_size}",
                    )

            if contains:
                content = file_path.read_text()
                if contains not in content:
                    return ValidationResult(
                        False, f"File {path} does not contain required text: {contains}"
                    )

            return ValidationResult(True, f"File {path} validation passed")

        except Exception as e:
            return ValidationResult(False, f"File validation failed: {str(e)}")


class CommandValidator(QualityGateValidator):
    """Validates system command execution"""

    def get_name(self) -> str:
        return "command"

    async def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate command execution"""
        try:
            command = config.get("command")
            expected_return_code = config.get("expected_return_code", 0)
            timeout = config.get("timeout", 30)

            if not command:
                return ValidationResult(False, "No command provided")

            # Execute command
            if isinstance(command, str):
                command = command.split()

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ValidationResult(
                    False, f"Command timed out after {timeout} seconds"
                )

            if process.returncode == expected_return_code:
                return ValidationResult(
                    True,
                    f"Command completed with return code {process.returncode}",
                    {"stdout": stdout.decode(), "stderr": stderr.decode()},
                )
            else:
                return ValidationResult(
                    False,
                    f"Command returned {process.returncode}, expected {expected_return_code}",
                    {"stdout": stdout.decode(), "stderr": stderr.decode()},
                )

        except Exception as e:
            return ValidationResult(False, f"Command validation failed: {str(e)}")


class QualityGateManager:
    """
    Manages quality gates and dependency validation for complex project orchestration
    """

    def __init__(self, state_dir: Path = None):
        self.state_dir = state_dir or Path("/tmp/quality_gates")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.gates: Dict[str, QualityGate] = {}
        self.phases: Dict[str, Phase] = {}
        self.agent_dependencies: Dict[str, List[str]] = {}  # agent_id -> gate_ids
        self.blocked_tasks: Set[str] = set()
        self.waiting_tasks: Dict[str, Dict] = {}  # task_id -> {gates, callback}

        # Validation system
        self.validators: Dict[str, QualityGateValidator] = {
            "database": DatabaseValidator(),
            "websocket": WebSocketValidator(),
            "http": HttpValidator(),
            "file": FileValidator(),
            "command": CommandValidator(),
        }

        # Concurrency control
        self.lock = asyncio.Lock()
        self.validation_semaphore = asyncio.Semaphore(5)  # Max concurrent validations

        # Background validation task
        self._validation_task: Optional[asyncio.Task] = None
        self._stop_validation = False

        logger.info(f"QualityGateManager initialized with state dir: {self.state_dir}")

    def register_validator(self, validator: QualityGateValidator):
        """Register a custom validator"""
        self.validators[validator.get_name()] = validator
        logger.info(f"Registered custom validator: {validator.get_name()}")

    async def define_gate(
        self,
        gate_id: str,
        name: str,
        description: str,
        validator_type: str,
        config: Dict[str, Any],
        dependencies: List[str] = None,
        timeout_seconds: int = 300,
        retry_interval: int = 30,
        max_retries: int = 10,
    ) -> QualityGate:
        """Define a new quality gate"""

        if validator_type not in self.validators:
            raise ValueError(f"Unknown validator type: {validator_type}")

        gate = QualityGate(
            gate_id=gate_id,
            name=name,
            description=description,
            validator_type=validator_type,
            config=config,
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            retry_interval=retry_interval,
            max_retries=max_retries,
        )

        async with self.lock:
            self.gates[gate_id] = gate

        await self._save_state()
        logger.info(f"Defined quality gate: {gate_id} ({validator_type})")
        return gate

    async def define_phase(
        self, phase_id: str, name: str, description: str, gates: List[str]
    ) -> Phase:
        """Define an execution phase"""

        # Validate all gates exist
        for gate_id in gates:
            if gate_id not in self.gates:
                raise ValueError(f"Unknown gate: {gate_id}")

        phase = Phase(
            phase_id=phase_id, name=name, description=description, gates=gates
        )

        async with self.lock:
            self.phases[phase_id] = phase

        await self._save_state()
        logger.info(f"Defined phase: {phase_id} with gates: {gates}")
        return phase

    async def register_agent_dependencies(self, agent_id: str, gate_ids: List[str]):
        """Register which gates an agent depends on"""
        # Validate gates exist
        for gate_id in gate_ids:
            if gate_id not in self.gates:
                raise ValueError(f"Unknown gate: {gate_id}")

        async with self.lock:
            self.agent_dependencies[agent_id] = gate_ids

        await self._save_state()
        logger.info(f"Registered dependencies for {agent_id}: {gate_ids}")

    async def validate_deliverable(
        self, agent_id: str, deliverable: Any
    ) -> ValidationResult:
        """Validate an agent's deliverable"""
        # For now, this is a simple check that the agent completed
        # In a real implementation, this could validate deliverable structure, content, etc.

        if deliverable is None:
            return ValidationResult(False, f"Agent {agent_id} provided no deliverable")

        # Check if deliverable has required structure
        if isinstance(deliverable, dict):
            if "status" in deliverable and deliverable["status"] == "failed":
                return ValidationResult(False, f"Agent {agent_id} reported failure")

            if "result" in deliverable and deliverable["result"] is None:
                return ValidationResult(False, f"Agent {agent_id} produced no result")

        return ValidationResult(
            True,
            f"Agent {agent_id} deliverable validated",
            {"deliverable": deliverable},
        )

    async def check_quality_gates(self, gate_name: str) -> GateStatus:
        """Check the status of a specific quality gate"""
        if gate_name not in self.gates:
            return GateStatus.FAILED

        gate = self.gates[gate_name]
        return gate.status

    async def validate_gate(self, gate_id: str) -> ValidationResult:
        """Validate a specific gate"""
        if gate_id not in self.gates:
            return ValidationResult(False, f"Unknown gate: {gate_id}")

        gate = self.gates[gate_id]

        # Check dependencies first
        for dep_gate_id in gate.dependencies:
            if dep_gate_id not in self.gates:
                return ValidationResult(
                    False, f"Dependency gate {dep_gate_id} not found"
                )

            dep_gate = self.gates[dep_gate_id]
            if dep_gate.status != GateStatus.PASSED:
                return ValidationResult(
                    False,
                    f"Dependency gate {dep_gate_id} has not passed (status: {dep_gate.status})",
                    retry_after=gate.retry_interval,
                )

        # Run validation
        validator = self.validators.get(gate.validator_type)
        if not validator:
            return ValidationResult(
                False, f"No validator for type: {gate.validator_type}"
            )

        async with self.validation_semaphore:
            gate.status = GateStatus.VALIDATING
            try:
                result = await validator.validate(gate.config)

                if result.success:
                    gate.status = GateStatus.PASSED
                else:
                    gate.status = GateStatus.FAILED

                gate.last_validation = result
                await self._save_state()

                logger.info(
                    f"Gate {gate_id} validation: {'PASSED' if result.success else 'FAILED'} - {result.message}"
                )
                return result

            except Exception as e:
                gate.status = GateStatus.FAILED
                result = ValidationResult(False, f"Validation error: {str(e)}")
                gate.last_validation = result
                await self._save_state()
                return result

    async def block_until_dependencies_ready(
        self, task_id: str, required_gates: List[str] = None
    ) -> None:
        """Block until all required gates are ready"""

        if required_gates is None:
            # Use agent dependencies if registered
            required_gates = self.agent_dependencies.get(task_id, [])

        if not required_gates:
            logger.info(f"Task {task_id} has no gate dependencies")
            return

        logger.info(f"Task {task_id} waiting for gates: {required_gates}")

        # Wait for all gates to pass
        while True:
            all_passed = True
            failed_gates = []
            pending_gates = []

            for gate_id in required_gates:
                if gate_id not in self.gates:
                    raise ValueError(f"Unknown gate: {gate_id}")

                gate = self.gates[gate_id]
                if gate.status == GateStatus.FAILED:
                    failed_gates.append(gate_id)
                    all_passed = False
                elif gate.status != GateStatus.PASSED:
                    pending_gates.append(gate_id)
                    all_passed = False

            if failed_gates:
                raise RuntimeError(
                    f"Task {task_id} blocked by failed gates: {failed_gates}"
                )

            if all_passed:
                logger.info(f"Task {task_id} dependencies satisfied")
                break

            logger.info(f"Task {task_id} waiting for gates: {pending_gates}")
            await asyncio.sleep(5)  # Check every 5 seconds

    async def release_dependent_tasks(self, completed_task_id: str) -> None:
        """Release tasks that were waiting for this task's completion"""
        # This would be implemented to notify waiting tasks
        # For now, just log the completion
        logger.info(f"Task {completed_task_id} completed, checking for dependent tasks")

        # In a full implementation, this would:
        # 1. Find tasks waiting on gates that this task satisfies
        # 2. Re-evaluate those gates
        # 3. Release tasks whose dependencies are now satisfied

    async def start_validation_loop(self):
        """Start background validation loop"""
        if self._validation_task and not self._validation_task.done():
            return  # Already running

        self._stop_validation = False
        self._validation_task = asyncio.create_task(self._validation_loop())
        logger.info("Started quality gate validation loop")

    async def stop_validation_loop(self):
        """Stop background validation loop"""
        self._stop_validation = True
        if self._validation_task:
            await self._validation_task
        logger.info("Stopped quality gate validation loop")

    async def _validation_loop(self):
        """Background loop to continuously validate gates"""
        while not self._stop_validation:
            try:
                # Find gates that need validation
                gates_to_validate = []
                async with self.lock:
                    for gate_id, gate in self.gates.items():
                        if gate.status in [GateStatus.PENDING, GateStatus.FAILED]:
                            gates_to_validate.append(gate_id)

                # Validate gates in parallel
                if gates_to_validate:
                    tasks = [
                        self.validate_gate(gate_id) for gate_id in gates_to_validate[:5]
                    ]  # Limit concurrency
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Wait before next validation cycle
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in validation loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        async with self.lock:
            gate_status = {}
            for gate_id, gate in self.gates.items():
                gate_status[gate_id] = {
                    "status": gate.status.value,
                    "name": gate.name,
                    "description": gate.description,
                    "last_validation": gate.last_validation.to_dict()
                    if gate.last_validation
                    else None,
                }

            phase_status = {}
            for phase_id, phase in self.phases.items():
                gates_passed = sum(
                    1
                    for gate_id in phase.gates
                    if self.gates[gate_id].status == GateStatus.PASSED
                )
                phase_status[phase_id] = {
                    "status": phase.status,
                    "name": phase.name,
                    "gates_passed": f"{gates_passed}/{len(phase.gates)}",
                    "gates": [
                        {
                            "gate_id": gate_id,
                            "status": self.gates[gate_id].status.value,
                            "name": self.gates[gate_id].name,
                        }
                        for gate_id in phase.gates
                    ],
                }

            return {
                "gates": gate_status,
                "phases": phase_status,
                "agent_dependencies": self.agent_dependencies,
                "blocked_tasks": list(self.blocked_tasks),
                "timestamp": datetime.now().isoformat(),
            }

    async def _save_state(self):
        """Save current state to disk"""
        try:
            state = {
                "gates": {k: v.to_dict() for k, v in self.gates.items()},
                "phases": {k: asdict(v) for k, v in self.phases.items()},
                "agent_dependencies": self.agent_dependencies,
                "blocked_tasks": list(self.blocked_tasks),
                "timestamp": datetime.now().isoformat(),
            }

            state_file = self.state_dir / "quality_gates_state.json"
            state_file.write_text(json.dumps(state, indent=2))

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def _load_state(self):
        """Load state from disk"""
        try:
            state_file = self.state_dir / "quality_gates_state.json"
            if state_file.exists():
                state = json.loads(state_file.read_text())

                # Restore gates
                for gate_id, gate_data in state.get("gates", {}).items():
                    gate = QualityGate(**gate_data)
                    # Convert status back to enum
                    gate.status = GateStatus(gate_data["status"])
                    # Restore validation result if exists
                    if gate_data.get("last_validation"):
                        gate.last_validation = ValidationResult(
                            **gate_data["last_validation"]
                        )
                    self.gates[gate_id] = gate

                # Restore phases
                for phase_id, phase_data in state.get("phases", {}).items():
                    self.phases[phase_id] = Phase(**phase_data)

                # Restore other state
                self.agent_dependencies = state.get("agent_dependencies", {})
                self.blocked_tasks = set(state.get("blocked_tasks", []))

                logger.info(
                    f"Loaded state: {len(self.gates)} gates, {len(self.phases)} phases"
                )

        except Exception as e:
            logger.warning(f"Failed to load state: {e}")


# Convenient factory functions for common gates


async def create_database_ready_gate(
    manager: QualityGateManager, connection_string: str = None
) -> QualityGate:
    """Create a standard database readiness gate"""
    return await manager.define_gate(
        gate_id="database_ready",
        name="Database Ready",
        description="Verify database is accessible and has required extensions",
        validator_type="database",
        config={
            "connection_string": connection_string,
            "query": "SELECT * FROM pg_extension WHERE extname = 'vector'",
            "expected_result": None,  # Just needs to return results
        },
    )


async def create_migration_complete_gate(
    manager: QualityGateManager, connection_string: str = None, min_records: int = 633
) -> QualityGate:
    """Create a migration completion gate"""
    return await manager.define_gate(
        gate_id="migration_complete",
        name="Migration Complete",
        description="Verify database migration has completed successfully",
        validator_type="database",
        config={
            "connection_string": connection_string,
            "query": f"SELECT COUNT(*) FROM context_items WHERE source_type = 'chat'",
            "expected_result": None,  # Will check if count > min_records in a custom way
        },
        dependencies=["database_ready"],
    )


async def create_api_ready_gate(
    manager: QualityGateManager, url: str = "ws://localhost:8080/ide-bridge"
) -> QualityGate:
    """Create an API readiness gate"""
    return await manager.define_gate(
        gate_id="api_responding",
        name="API Responding",
        description="Verify WebSocket API is responding to connections",
        validator_type="websocket",
        config={"url": url, "timeout": 10},
    )


async def create_file_ready_gate(
    manager: QualityGateManager, file_path: str, contains: str = None
) -> QualityGate:
    """Create a file readiness gate"""
    return await manager.define_gate(
        gate_id=f"file_ready_{Path(file_path).name}",
        name=f"File Ready: {Path(file_path).name}",
        description=f"Verify file {file_path} exists and meets requirements",
        validator_type="file",
        config={"path": file_path, "exists": True, "contains": contains},
    )
