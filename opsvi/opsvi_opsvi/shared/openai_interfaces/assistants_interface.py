from typing import Any

from src.shared.openai_interfaces.base import OpenAIBaseInterface

ALLOWED_MODELS = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o4-mini",
]


class OpenAIAssistantsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Assistants API (OpenAI Python SDK >=1.0.0).
    Only approved models compatible with Assistants API are allowed: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o4-mini.
    All methods use self.client.beta.assistants, self.client.beta.threads, etc.
    """

    # No __init__ override; base class sets self.client

    def create_assistant(self, **kwargs) -> dict[str, Any]:
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        model = kwargs.get("model")
        if model not in ALLOWED_MODELS:
            raise ValueError(
                f"Model '{model}' is not allowed for Assistants API. Allowed: {ALLOWED_MODELS}"
            )
        try:
            response = self.client.beta.assistants.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_assistant(self, assistant_id: str) -> dict[str, Any]:
        """
        Retrieve an assistant by ID.
        GET /v1/assistants/{assistant_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.assistants.retrieve(assistant_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def modify_assistant(self, assistant_id: str, **kwargs) -> dict[str, Any]:
        """
        Modify an assistant.
        POST /v1/assistants/{assistant_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.assistants.update(assistant_id, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def delete_assistant(self, assistant_id: str) -> dict[str, Any]:
        """
        Delete an assistant.
        DELETE /v1/assistants/{assistant_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.assistants.delete(assistant_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_assistants(self) -> list[dict[str, Any]]:
        """
        List all assistants.
        GET /v1/assistants
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.assistants.list()
            return [dict(a) for a in response.data]
        except Exception as e:
            self._handle_error(e)

    def create_thread(self, **kwargs) -> dict[str, Any]:
        """
        Create a thread.
        POST /v1/threads
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_thread(self, thread_id: str) -> dict[str, Any]:
        """
        Retrieve a thread by ID.
        GET /v1/threads/{thread_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.retrieve(thread_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def modify_thread(self, thread_id: str, **kwargs) -> dict[str, Any]:
        """
        Modify a thread.
        POST /v1/threads/{thread_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.update(thread_id, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def delete_thread(self, thread_id: str) -> dict[str, Any]:
        """
        Delete a thread.
        DELETE /v1/threads/{thread_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.delete(thread_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_threads(self) -> list[dict[str, Any]]:
        """
        List all threads.
        GET /v1/threads
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.list()
            return [dict(t) for t in response.data]
        except Exception as e:
            self._handle_error(e)

    def create_message(self, thread_id: str, **kwargs) -> dict[str, Any]:
        """
        Create a message in a thread.
        POST /v1/threads/{thread_id}/messages
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.messages.create(
                thread_id=thread_id, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_messages(self, thread_id: str) -> list[dict[str, Any]]:
        """
        List all messages in a thread.
        GET /v1/threads/{thread_id}/messages
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.messages.list(thread_id=thread_id)
            return [dict(m) for m in response.data]
        except Exception as e:
            self._handle_error(e)

    def retrieve_message(self, thread_id: str, message_id: str) -> dict[str, Any]:
        """
        Retrieve a message by ID.
        GET /v1/threads/{thread_id}/messages/{message_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.messages.retrieve(
                thread_id=thread_id, message_id=message_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def run_thread(self, thread_id: str, **kwargs) -> dict[str, Any]:
        """
        Run a thread.
        POST /v1/threads/{thread_id}/runs
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.create(
                thread_id=thread_id, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_run(self, thread_id: str, run_id: str) -> dict[str, Any]:
        """
        Retrieve a run by ID.
        GET /v1/threads/{thread_id}/runs/{run_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_runs(self, thread_id: str) -> list[dict[str, Any]]:
        """
        List all runs in a thread.
        GET /v1/threads/{thread_id}/runs
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.list(thread_id=thread_id)
            return [dict(r) for r in response.data]
        except Exception as e:
            self._handle_error(e)

    def cancel_run(self, thread_id: str, run_id: str) -> dict[str, Any]:
        """
        Cancel a run.
        POST /v1/threads/{thread_id}/runs/{run_id}/cancel
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.cancel(
                thread_id=thread_id, run_id=run_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_run_steps(self, thread_id: str, run_id: str) -> list[dict[str, Any]]:
        """
        List all run steps in a run.
        GET /v1/threads/{thread_id}/runs/{run_id}/steps
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id, run_id=run_id
            )
            return [dict(s) for s in response.data]
        except Exception as e:
            self._handle_error(e)

    def retrieve_run_step(
        self, thread_id: str, run_id: str, step_id: str
    ) -> dict[str, Any]:
        """
        Retrieve a run step by ID.
        GET /v1/threads/{thread_id}/runs/{run_id}/steps/{step_id}
        """
        if not hasattr(self, "client") or self.client is None:
            raise RuntimeError(
                "OpenAIAssistantsInterface: self.client is not set. Ensure base class __init__ is called."
            )
        try:
            response = self.client.beta.threads.runs.steps.retrieve(
                thread_id=thread_id, run_id=run_id, step_id=step_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)
