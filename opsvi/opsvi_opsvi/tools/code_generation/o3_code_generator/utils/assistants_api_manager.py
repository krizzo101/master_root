"""
OpenAI Assistants API Manager for Conversational Interactions

This module provides a high-level interface for managing OpenAI Assistants API
conversations, enabling real-time back-and-forth interactions for idea development
and other conversational workflows.
"""

import json
import time
from typing import Any

from openai import OpenAI
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Message, Run

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class AssistantsAPIManager:
    """
    Manages OpenAI Assistants API for conversational interactions.

    This class provides a high-level interface for creating assistants,
    managing threads, and conducting real-time conversations.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1") -> None:
        """
        Initialize the Assistants API Manager.

        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model to use for the assistant
        """
        self.logger = get_logger()
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.assistant: Assistant | None = None
        self.thread: Thread | None = None
        self.current_run: Run | None = None

    def create_assistant(
        self, name: str, instructions: str, tools: list[dict[str, Any]] | None = None
    ) -> Assistant:
        """
        Create a new assistant with specified configuration.

        Args:
            name: Name of the assistant
            instructions: Instructions for the assistant's behavior
            tools: List of tools to enable (code_interpreter, file_search, functions)

        Returns:
            Created assistant object
        """
        try:
            if tools is None:
                tools = []

            self.assistant = self.client.beta.assistants.create(
                name=name, instructions=instructions, model=self.model, tools=tools
            )

            self.logger.log_info(f"Created assistant: {self.assistant.id}")
            return self.assistant

        except Exception as e:
            self.logger.log_error(f"Failed to create assistant: {e}")
            raise

    def create_thread(self) -> Thread:
        """
        Create a new conversation thread.

        Returns:
            Created thread object
        """
        try:
            self.thread = self.client.beta.threads.create()
            self.logger.log_info(f"Created thread: {self.thread.id}")
            return self.thread

        except Exception as e:
            self.logger.log_error(f"Failed to create thread: {e}")
            raise

    def add_message(self, content: str, role: str = "user") -> Message:
        """
        Add a message to the current thread.

        Args:
            content: Message content
            role: Message role (user/assistant)

        Returns:
            Created message object
        """
        if not self.thread:
            raise ValueError("No thread available. Call create_thread() first.")

        try:
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

            self.logger.log_debug(f"Added {role} message: {message.id}")
            return message

        except Exception as e:
            self.logger.log_error(f"Failed to add message: {e}")
            raise

    def run_assistant(self) -> Run:
        """
        Run the assistant on the current thread.

        Returns:
            Run object
        """
        if not self.assistant or not self.thread:
            raise ValueError("Both assistant and thread must be created first.")

        try:
            self.current_run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id, assistant_id=self.assistant.id
            )

            self.logger.log_info(f"Started run: {self.current_run.id}")
            return self.current_run

        except Exception as e:
            self.logger.log_error(f"Failed to start run: {e}")
            raise

    def wait_for_run_completion(
        self, run: Run | None = None, timeout: int = 300
    ) -> Run:
        """
        Wait for a run to complete.

        Args:
            run: Run to wait for (defaults to current run)
            timeout: Maximum time to wait in seconds

        Returns:
            Completed run object
        """
        if run is None:
            run = self.current_run

        if not run:
            raise ValueError("No run specified or available.")

        start_time = time.time()

        while run.status in ["queued", "in_progress"]:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Run timed out after {timeout} seconds")

            time.sleep(0.5)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id, run_id=run.id
            )

        self.current_run = run
        self.logger.log_info(f"Run completed with status: {run.status}")
        return run

    def get_latest_messages(self, limit: int = 10) -> list[Message]:
        """
        Get the latest messages from the thread.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages (most recent first)
        """
        if not self.thread:
            raise ValueError("No thread available.")

        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id, limit=limit
            )

            return messages.data

        except Exception as e:
            self.logger.log_error(f"Failed to retrieve messages: {e}")
            raise

    def get_assistant_response(self) -> str | None:
        """
        Get the latest assistant response from the thread.

        Returns:
            Assistant's response text or None if no response
        """
        messages = self.get_latest_messages(limit=5)

        for message in messages:
            if message.role == "assistant" and message.content:
                # Extract text content from the first content block
                if hasattr(message.content[0], "text") and hasattr(
                    message.content[0].text, "value"
                ):
                    return message.content[0].text.value

        return None

    def handle_required_action(self, run: Run) -> Run:
        """
        Handle required actions from the assistant (e.g., function calls).

        Args:
            run: Run that requires action

        Returns:
            Updated run after handling action
        """
        if run.status != "requires_action":
            return run

        if not run.required_action:
            return run

        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            if tool_call.type == "function":
                # Handle function calls here
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # For now, we'll just acknowledge the function call
                # In a real implementation, you'd execute the function
                result = f"Function {function_name} called with arguments: {arguments}"
                tool_outputs.append({"tool_call_id": tool_call.id, "output": result})

        # Submit tool outputs back to the assistant
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=run.id, tool_outputs=tool_outputs
        )

        return run

    def start_conversation(
        self, name: str, instructions: str, initial_message: str
    ) -> str:
        """
        Start a new conversation with the assistant.

        Args:
            name: Assistant name
            instructions: Assistant instructions
            initial_message: First user message

        Returns:
            Assistant's response
        """
        try:
            # Create assistant and thread
            self.create_assistant(name, instructions)
            self.create_thread()

            # Add initial message
            self.add_message(initial_message)

            # Run assistant
            run = self.run_assistant()

            # Wait for completion and handle any required actions
            run = self.wait_for_run_completion(run)

            if run.status == "requires_action":
                run = self.handle_required_action(run)
                run = self.wait_for_run_completion(run)

            # Get response
            response = self.get_assistant_response()
            return response or "No response received"

        except Exception as e:
            self.logger.log_error(f"Failed to start conversation: {e}")
            raise

    def continue_conversation(self, message: str) -> str:
        """
        Continue an existing conversation.

        Args:
            message: User message

        Returns:
            Assistant's response
        """
        try:
            # Add user message
            self.add_message(message)

            # Run assistant
            run = self.run_assistant()

            # Wait for completion and handle any required actions
            run = self.wait_for_run_completion(run)

            if run.status == "requires_action":
                run = self.handle_required_action(run)
                run = self.wait_for_run_completion(run)

            # Get response
            response = self.get_assistant_response()
            return response or "No response received"

        except Exception as e:
            self.logger.log_error(f"Failed to continue conversation: {e}")
            raise

    def cleanup(self) -> None:
        """
        Clean up resources (delete assistant and thread).
        """
        try:
            if self.assistant:
                self.client.beta.assistants.delete(self.assistant.id)
                self.logger.log_info(f"Deleted assistant: {self.assistant.id}")

            # Note: Threads are automatically cleaned up by OpenAI
            # after a certain period, so we don't need to delete them manually

        except Exception as e:
            self.logger.log_error(f"Failed to cleanup: {e}")
            # Don't raise here as cleanup should be best-effort
