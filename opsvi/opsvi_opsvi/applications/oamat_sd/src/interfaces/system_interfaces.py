"""
System Interface Contracts

ABC interfaces for system-level components including configuration
and error handling with adaptive capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.applications.oamat_sd.src.models.data_models import SystemError


class ISystemConfigurationManager(ABC):
    """Interface for adaptive system configuration management"""

    @abstractmethod
    async def load_configuration_adaptively(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load configuration adapted to current execution context

        Must adapt configuration based on context analysis,
        not use static configuration loading.
        """
        pass

    @abstractmethod
    async def validate_configuration_intelligently(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently validate configuration completeness and correctness

        Must use contextual validation approaches,
        not static validation rules.
        """
        pass

    @abstractmethod
    async def optimize_configuration_dynamically(
        self, config: Dict[str, Any], performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically optimize configuration based on performance data

        Must generate optimization strategies based on analysis,
        not use predefined optimization patterns.
        """
        pass


class IErrorHandlingManager(ABC):
    """Interface for intelligent error handling and recovery"""

    @abstractmethod
    async def analyze_error_intelligently(
        self, error: SystemError, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently analyze errors using contextual information

        Must analyze errors contextually to understand root causes,
        not use static error categorization.
        """
        pass

    @abstractmethod
    async def generate_recovery_strategy(
        self, error_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate intelligent recovery strategies based on error analysis

        Must create novel recovery approaches,
        not select from predefined recovery patterns.
        """
        pass

    @abstractmethod
    async def implement_adaptive_circuit_breaker(
        self, component: str, error_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Implement adaptive circuit breaker patterns

        Must adapt circuit breaker behavior based on error pattern analysis,
        not use static circuit breaker configurations.
        """
        pass

    @abstractmethod
    async def learn_from_errors(
        self, error_history: List[SystemError]
    ) -> Dict[str, Any]:
        """
        Learn from error patterns to improve future error handling

        Must generate insights and improvements from error analysis,
        not use static error handling approaches.
        """
        pass
