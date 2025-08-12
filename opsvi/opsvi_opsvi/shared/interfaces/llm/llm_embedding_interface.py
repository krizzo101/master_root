"""
LLM and Embedding Shared Interface
---------------------------------
Authoritative implementation based on the official OpenAI, Anthropic, Cohere, and LlamaIndex documentation:
- https://github.com/openai/openai-python
- https://docs.anthropic.com/claude/reference
- https://docs.cohere.com/docs
- https://docs.llamaindex.ai/
Implements all core features: completion, chat, embedding, and error handling. Async stubs included for extensibility.
Version: Referenced as of July 2024
"""

import logging

logger = logging.getLogger(__name__)


class LLMEmbeddingInterface:
    """
    Authoritative shared interface for LLM completions and embedding generation across providers.
    See official docs for each provider.
    """

    def __init__(
        self,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ):
        """
        Initialize the interface for a given provider (e.g., 'openai', 'anthropic', 'cohere', 'local').
        Args:
            provider: Provider name.
            api_key: API key for the provider.
            model: Default model name.
            kwargs: Additional provider-specific options.
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            try:
                import openai

                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required. Install with `pip install openai`."
                )
        elif self.provider == "anthropic":
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with `pip install anthropic`."
                )
        elif self.provider == "cohere":
            try:
                import cohere

                self.client = cohere.Client(self.api_key)
            except ImportError:
                raise ImportError(
                    "cohere package required. Install with `pip install cohere`."
                )
        elif self.provider == "local":
            # Placeholder for local model integration (e.g., llama.cpp, transformers)
            self.client = None
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def complete(self, prompt: str, **kwargs) -> str:
        """
        Generate a text completion for the given prompt.
        See:
        - OpenAI: https://github.com/openai/openai-python
        - Anthropic: https://docs.anthropic.com/claude/reference
        - Cohere: https://docs.cohere.com/docs
        """
        try:
            if self.provider == "openai":
                resp = self.client.completions.create(
                    model=self.model or "gpt-4.1-mini",
                    prompt=prompt,
                    **kwargs,
                )
                return resp.choices[0].text
            elif self.provider == "anthropic":
                resp = self.client.completions.create(
                    model=self.model or "claude-3-opus-20240229",
                    prompt=prompt,
                    **kwargs,
                )
                return resp.completion
            elif self.provider == "cohere":
                resp = self.client.generate(
                    model=self.model or "command", prompt=prompt, **kwargs
                )
                return resp.generations[0].text
            elif self.provider == "local":
                # Implement local model completion here
                raise NotImplementedError("Local model completion not implemented.")
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Completion failed: {e}")
            raise

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        Generate a chat response given a list of messages (role/content dicts).
        See:
        - OpenAI: https://github.com/openai/openai-python
        - Anthropic: https://docs.anthropic.com/claude/reference
        - Cohere: https://docs.cohere.com/docs
        """
        try:
            if self.provider == "openai":
                resp = self.client.chat.completions.create(
                    model=self.model or "gpt-4.1-mini", messages=messages, **kwargs
                )
                return resp.choices[0].message.content
            elif self.provider == "anthropic":
                # Anthropic chat API (Claude 3)
                resp = self.client.messages.create(
                    model=self.model or "claude-3-opus-20240229",
                    messages=messages,
                    **kwargs,
                )
                return resp.content[0].text if resp.content else ""
            elif self.provider == "cohere":
                # Cohere chat API
                resp = self.client.chat(
                    model=self.model or "command", chat_history=messages, **kwargs
                )
                return resp.text
            elif self.provider == "local":
                # Implement local model chat here
                raise NotImplementedError("Local model chat not implemented.")
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    def embed(self, texts: str | list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for one or more texts.
        See:
        - OpenAI: https://github.com/openai/openai-python
        - Cohere: https://docs.cohere.com/docs
        """
        try:
            if self.provider == "openai":
                if isinstance(texts, str):
                    texts = [texts]
                resp = self.client.embeddings.create(
                    model=self.model or "text-embedding-3-small", input=texts, **kwargs
                )
                return [e.embedding for e in resp.data]
            elif self.provider == "cohere":
                resp = self.client.embed(
                    texts=texts, model=self.model or "embed-english-v3.0", **kwargs
                )
                return resp.embeddings
            elif self.provider == "anthropic":
                # Anthropic does not currently provide embeddings (as of 2024-07)
                raise NotImplementedError("Anthropic does not support embeddings.")
            elif self.provider == "local":
                # Implement local embedding here
                raise NotImplementedError("Local model embedding not implemented.")
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    # Optional: async stubs for extensibility
    async def acomplete(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Async completion not implemented.")

    async def achat(self, messages: list[dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Async chat not implemented.")

    async def aembed(self, texts: str | list[str], **kwargs) -> list[list[float]]:
        raise NotImplementedError("Async embedding not implemented.")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # OpenAI example
    llm = LLMEmbeddingInterface(
        provider="openai", api_key="sk-...", model="gpt-4.1-mini"
    )
    print("Completion:", llm.complete("Once upon a time"))
    print("Embedding:", llm.embed(["hello world", "foo bar"]))
