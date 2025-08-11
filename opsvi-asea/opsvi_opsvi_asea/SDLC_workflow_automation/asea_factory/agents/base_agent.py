import openai
from asea_factory.utils.logger import get_logger
from asea_factory.agents._model_utils import (
    get_agent_model,
    get_agent_tokens,
    make_openai_request,
)


class BaseAgent:
    """Base class for all SDLC agents with common functionality"""

    def __init__(self, agent_name, config, debug=True):
        self.agent_name = agent_name
        self.config = config
        self.logger = get_logger(f"{agent_name}Agent", debug)
        self.model = get_agent_model(config, agent_name.lower())
        self.max_tokens = get_agent_tokens(config, agent_name.lower())
        self.openai_api_key = self.config.get_env("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key)

    def make_request(self, messages, **kwargs):
        """Make an OpenAI request with automatic parameter handling"""
        return make_openai_request(
            self.client, self.model, messages, self.max_tokens, **kwargs
        )

    def create_system_message(self, content):
        """Create a system message"""
        return {"role": "system", "content": content}

    def create_user_message(self, content):
        """Create a user message"""
        return {"role": "user", "content": content}

    def log_request(self, operation, input_data):
        """Log the start of an operation"""
        self.logger.debug(f"{operation}: {input_data}")

    def log_response(self, operation, response):
        """Log the response from an operation"""
        self.logger.debug(f"{operation} completed successfully")

    def handle_error(self, operation, error):
        """Handle and log errors"""
        self.logger.error(f"{operation} failed: {str(error)}")
        raise error
