"""
OpenAI Security Module - Data Sanitization and Audit Logging

Implements comprehensive security patterns per 2025 OpenAI API standards.
"""

import re
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataSanitizer:
    """
    Enhanced data sanitization for OpenAI API calls.
    Removes PII, secrets, and sensitive information.
    """
    
    # PII Detection Patterns
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'ipv4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'ipv6': r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',
    }
    
    # Secret Detection Patterns
    SECRET_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)[\s]*[:=][\s]*["\']?([a-zA-Z0-9_-]+)["\']?',
        'bearer_token': r'(?i)bearer[\s]+([a-zA-Z0-9_.-]+)',
        'password': r'(?i)(password|passwd|pwd)[\s]*[:=][\s]*["\']?([^\s"\']+)["\']?',
        'aws_key': r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)[\s]*[:=][\s]*["\']?([a-zA-Z0-9/+=]+)["\']?',
        'github_token': r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}',
        'openai_key': r'sk-[a-zA-Z0-9]{48}',
        'private_key': r'-----BEGIN (?:RSA )?PRIVATE KEY-----',
    }
    
    @classmethod
    def sanitize_input(cls, user_input: str) -> str:
        """
        Remove PII and secrets from input text.
        
        Args:
            user_input: Raw input text
            
        Returns:
            Sanitized text with sensitive data redacted
        """
        if not user_input:
            return user_input
        
        sanitized = user_input
        
        # Remove PII
        for pattern_name, pattern in cls.PII_PATTERNS.items():
            matches = re.finditer(pattern, sanitized, re.IGNORECASE)
            for match in matches:
                replacement = f'[REDACTED_{pattern_name.upper()}]'
                sanitized = sanitized.replace(match.group(), replacement)
                logger.debug(f"Redacted {pattern_name}: {match.group()[:4]}...")
        
        # Remove secrets
        for pattern_name, pattern in cls.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, sanitized)
            for match in matches:
                # For patterns with groups, replace the secret part only
                if match.groups():
                    full_match = match.group()
                    secret_part = match.group(1) if len(match.groups()) == 1 else match.group(2)
                    replacement = full_match.replace(secret_part, f'[REDACTED_{pattern_name.upper()}]')
                    sanitized = sanitized.replace(full_match, replacement)
                else:
                    replacement = f'[REDACTED_{pattern_name.upper()}]'
                    sanitized = sanitized.replace(match.group(), replacement)
                logger.debug(f"Redacted {pattern_name}")
        
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize a dictionary structure.
        
        Args:
            data: Dictionary potentially containing sensitive data
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        sensitive_keys = {
            'password', 'secret', 'token', 'key', 'api_key', 'apikey',
            'authorization', 'auth', 'credential', 'private'
        }
        
        for key, value in data.items():
            # Check if key name suggests sensitive data
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_input(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


class AuditLogger:
    """
    Comprehensive audit logging for OpenAI API interactions.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs (defaults to ./.audit_logs)
        """
        self.log_dir = Path(log_dir or ".audit_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create daily log file
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"openai_audit_{today}.jsonl"
        
        logger.info(f"Audit logging to: {self.log_file}")
    
    def log_request(
        self,
        model: str,
        input_data: Any,
        sanitized_input: Any,
        request_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Log an API request.
        
        Args:
            model: Model being used
            input_data: Original input (not logged)
            sanitized_input: Sanitized version for logging
            request_id: Optional request identifier
            **kwargs: Additional metadata
            
        Returns:
            Generated request ID
        """
        if not request_id:
            request_id = f"req_{int(time.time() * 1000)}"
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "api_request",
            "request_id": request_id,
            "model": model,
            "input_length": len(str(input_data)),
            "sanitized_input": sanitized_input[:1000] if isinstance(sanitized_input, str) else str(sanitized_input)[:1000],
            "metadata": kwargs
        }
        
        self._write_log(log_entry)
        return request_id
    
    def log_response(
        self,
        request_id: str,
        success: bool,
        response_data: Optional[Any] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        """
        Log an API response.
        
        Args:
            request_id: Request identifier
            success: Whether the request succeeded
            response_data: Response data (if successful)
            error: Error message (if failed)
            **kwargs: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "api_response",
            "request_id": request_id,
            "success": success,
            "error": error,
            "metadata": kwargs
        }
        
        if success and response_data:
            # Log response metadata without sensitive content
            if hasattr(response_data, 'id'):
                log_entry["response_id"] = response_data.id
            if hasattr(response_data, 'model'):
                log_entry["response_model"] = response_data.model
            if hasattr(response_data, 'usage'):
                log_entry["usage"] = response_data.usage
        
        self._write_log(log_entry)
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any]
    ):
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            severity: Severity level (low, medium, high, critical)
            details: Event details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security_event",
            "security_event_type": event_type,
            "severity": severity,
            "details": DataSanitizer.sanitize_dict(details)
        }
        
        self._write_log(log_entry)
        
        # Also log to standard logger for high severity events
        if severity in ["high", "critical"]:
            logger.warning(f"Security event: {event_type} - {details}")
    
    def _write_log(self, entry: Dict[str, Any]):
        """Write a log entry to the audit file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_request_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve request history from audit logs.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            model: Filter by model name
            
        Returns:
            List of matching log entries
        """
        entries = []
        
        # Read all log files in the directory
        for log_file in self.log_dir.glob("openai_audit_*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        
                        # Apply filters
                        if entry.get("event_type") != "api_request":
                            continue
                        
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if start_time and entry_time < start_time:
                            continue
                        if end_time and entry_time > end_time:
                            continue
                        if model and entry.get("model") != model:
                            continue
                        
                        entries.append(entry)
                        
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
        
        return sorted(entries, key=lambda x: x["timestamp"])


class SecurityEnforcer:
    """
    Enforces security policies for OpenAI API usage.
    """
    
    def __init__(self, sanitizer: DataSanitizer, audit_logger: AuditLogger):
        """
        Initialize security enforcer.
        
        Args:
            sanitizer: Data sanitizer instance
            audit_logger: Audit logger instance
        """
        self.sanitizer = sanitizer
        self.audit_logger = audit_logger
    
    def secure_api_call(
        self,
        api_function: callable,
        input_data: Any,
        model: str,
        **kwargs
    ) -> Any:
        """
        Execute an API call with comprehensive security measures.
        
        Args:
            api_function: The API function to call
            input_data: Input data for the API
            model: Model being used
            **kwargs: Additional parameters for the API call
            
        Returns:
            API response
            
        Raises:
            Various exceptions with security context
        """
        # Sanitize input
        if isinstance(input_data, str):
            sanitized_input = self.sanitizer.sanitize_input(input_data)
        elif isinstance(input_data, dict):
            sanitized_input = self.sanitizer.sanitize_dict(input_data)
        else:
            sanitized_input = input_data
        
        # Log request
        request_id = self.audit_logger.log_request(
            model=model,
            input_data=input_data,
            sanitized_input=sanitized_input,
            **kwargs
        )
        
        try:
            # Add security instructions
            if 'instructions' in kwargs:
                kwargs['instructions'] += "\n\nIMPORTANT: Do not generate or reference any real API keys, passwords, or sensitive data."
            
            # Execute API call with sanitized input
            response = api_function(sanitized_input, model=model, **kwargs)
            
            # Log successful response
            self.audit_logger.log_response(
                request_id=request_id,
                success=True,
                response_data=response
            )
            
            return response
            
        except Exception as e:
            # Log failed response
            self.audit_logger.log_response(
                request_id=request_id,
                success=False,
                error=str(e)
            )
            
            # Check for security-related errors
            error_str = str(e).lower()
            if any(term in error_str for term in ['forbidden', 'unauthorized', 'denied']):
                self.audit_logger.log_security_event(
                    event_type="access_denied",
                    severity="high",
                    details={"error": str(e), "model": model}
                )
            
            raise