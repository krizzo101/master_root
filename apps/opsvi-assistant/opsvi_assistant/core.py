"""Core assistant functionality."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs"))

from opsvi_llm.providers import (
    AnthropicProvider, 
    AnthropicConfig,
    BaseLLMProvider,
    LLMRequestError
)


@dataclass
class ConversationHistory:
    """Manages conversation history."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    max_messages: int = 100
    
    def add_message(self, role: str, content: str):
        """Add a message to history."""
        self.messages.append({"role": role, "content": content})
        
        # Trim history if too long
        if len(self.messages) > self.max_messages:
            # Keep system message if present
            if self.messages[0]["role"] == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_messages-1):]
            else:
                self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get conversation messages."""
        return self.messages.copy()
    
    def clear(self):
        """Clear conversation history."""
        # Keep system message if present
        if self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []


class Assistant:
    """AI Assistant using OPSVI libraries."""
    
    def __init__(self, provider: str = "anthropic", config: Optional[Dict] = None):
        """Initialize the assistant.
        
        Args:
            provider: LLM provider to use
            config: Optional configuration dict
        """
        self.provider_name = provider
        self.config = config or {}
        self.provider = self._create_provider(provider)
        self.history = ConversationHistory()
        self.total_tokens = 0
        self.message_count = 0
        
        # Set system prompt
        self.history.add_message(
            "system",
            "You are a helpful AI assistant powered by OPSVI libraries. "
            "You provide clear, accurate, and helpful responses."
        )
    
    def _create_provider(self, provider: str) -> BaseLLMProvider:
        """Create LLM provider instance."""
        if provider == "anthropic":
            config = AnthropicConfig(**self.config)
            return AnthropicProvider(config)
        elif provider == "openai":
            # Import OpenAI provider when implemented
            raise NotImplementedError("OpenAI provider not yet implemented")
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @property
    def default_model(self) -> str:
        """Get default model name."""
        return self.provider.config.model
    
    def ask(self, question: str, model: Optional[str] = None) -> str:
        """Ask a single question.
        
        Args:
            question: The question to ask
            model: Optional model override
            
        Returns:
            The assistant's response
        """
        try:
            response = self.provider.chat({
                "messages": [
                    {"role": "user", "content": question}
                ],
                "model": model
            })
            
            self.message_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.get('total_tokens', 0)
            
            return response.content
            
        except LLMRequestError as e:
            return f"Error: {str(e)}"
    
    def chat(self, message: str) -> str:
        """Chat with conversation history.
        
        Args:
            message: User message
            
        Returns:
            Assistant response
        """
        self.history.add_message("user", message)
        
        try:
            response = self.provider.chat({
                "messages": self.history.get_messages()
            })
            
            self.history.add_message("assistant", response.content)
            self.message_count += 1
            
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.get('total_tokens', 0)
            
            return response.content
            
        except LLMRequestError as e:
            return f"Error: {str(e)}"
    
    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code from description.
        
        Args:
            description: What the code should do
            language: Programming language
            
        Returns:
            Generated code
        """
        prompt = f"""Generate {language} code for the following requirement:
{description}

Requirements:
- Clean, readable code
- Proper error handling
- Include docstrings/comments
- Follow {language} best practices

Return ONLY the code, no explanations."""
        
        try:
            response = self.provider.chat({
                "messages": [
                    {"role": "system", "content": f"You are an expert {language} programmer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3  # Lower temperature for code generation
            })
            
            self.message_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.get('total_tokens', 0)
            
            # Extract code from response
            code = response.content
            
            # Remove markdown code blocks if present
            if "```" in code:
                lines = code.split("\n")
                code_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                
                code = "\n".join(code_lines)
            
            return code.strip()
            
        except LLMRequestError as e:
            return f"# Error generating code: {str(e)}"
    
    def check_code(self, code: str, filename: str = "code.py") -> List[str]:
        """Check code for issues.
        
        Args:
            code: Code to check
            filename: Optional filename for context
            
        Returns:
            List of issues found
        """
        prompt = f"""Analyze the following {filename} code for issues:

```
{code}
```

Check for:
- Syntax errors
- Logic errors
- Security issues
- Performance problems
- Best practice violations

Return a JSON array of issues found, or empty array if none.
Format: ["issue 1", "issue 2", ...]"""
        
        try:
            response = self.provider.chat({
                "messages": [
                    {"role": "system", "content": "You are a code review expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            })
            
            self.message_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.get('total_tokens', 0)
            
            # Parse JSON response
            try:
                content = response.content
                # Extract JSON if wrapped in other text
                if "[" in content and "]" in content:
                    start = content.index("[")
                    end = content.rindex("]") + 1
                    json_str = content[start:end]
                    issues = json.loads(json_str)
                    return issues
                else:
                    return []
            except (json.JSONDecodeError, ValueError):
                return [response.content]  # Return as single issue if not JSON
                
        except LLMRequestError as e:
            return [f"Error checking code: {str(e)}"]
    
    def improve_code(self, code: str, filename: str = "code.py") -> str:
        """Suggest improvements for code.
        
        Args:
            code: Code to improve
            filename: Optional filename for context
            
        Returns:
            Improvement suggestions
        """
        prompt = f"""Review the following {filename} code and suggest improvements:

```
{code}
```

Focus on:
- Code organization and structure
- Performance optimizations
- Error handling improvements
- Code readability
- Best practices

Provide specific, actionable suggestions."""
        
        try:
            response = self.provider.chat({
                "messages": [
                    {"role": "system", "content": "You are a senior software engineer providing code review."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            })
            
            self.message_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.get('total_tokens', 0)
            
            return response.content
            
        except LLMRequestError as e:
            return f"Error: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get assistant status.
        
        Returns:
            Status dictionary
        """
        return {
            "provider": self.provider_name,
            "model": self.default_model,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "history_length": len(self.history.messages)
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "provider": self.provider_name,
            "model": self.provider.config.model,
            "temperature": getattr(self.provider.config, 'temperature', None),
            "max_tokens": getattr(self.provider.config, 'max_tokens', None)
        }
    
    def set_provider(self, provider: str):
        """Change LLM provider.
        
        Args:
            provider: New provider name
        """
        self.provider_name = provider
        self.provider = self._create_provider(provider)
    
    def set_model(self, model: str):
        """Change model.
        
        Args:
            model: Model name
        """
        self.provider.config.model = model
    
    def set_temperature(self, temperature: float):
        """Set temperature.
        
        Args:
            temperature: Temperature value (0-1)
        """
        if hasattr(self.provider.config, 'temperature'):
            self.provider.config.temperature = temperature
    
    def clear_history(self):
        """Clear conversation history."""
        self.history.clear()