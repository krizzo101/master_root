from typing import Any, Dict

import openai

from src.shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIAudioInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Audio API (Whisper, TTS).
    Reference: https://platform.openai.com/docs/api-reference/audio

    This interface provides both synchronous and asynchronous methods for all audio endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def create_transcription(self, audio_file: bytes, **kwargs) -> Dict[str, Any]:
        """
        Transcribe audio into text.
        POST /v1/audio/transcriptions
        """
        try:
            response = openai.Audio.transcribe(file=audio_file, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def create_translation(self, audio_file: bytes, **kwargs) -> Dict[str, Any]:
        """
        Translate audio into English.
        POST /v1/audio/translations
        """
        try:
            response = openai.Audio.translate(file=audio_file, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def create_speech(self, input_text: str, **kwargs) -> bytes:
        """
        Generate spoken audio from text.
        POST /v1/audio/speech
        """
        try:
            response = openai.Audio.create(input=input_text, **kwargs)
            return response.content if hasattr(response, "content") else response
        except Exception as e:
            self._handle_error(e)

    async def acreate_transcription(
        self, audio_file: bytes, **kwargs
    ) -> Dict[str, Any]:
        """
        Async: Transcribe audio into text.
        POST /v1/audio/transcriptions
        """
        try:
            response = await openai.Audio.atranscribe(file=audio_file, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_translation(self, audio_file: bytes, **kwargs) -> Dict[str, Any]:
        """
        Async: Translate audio into English.
        POST /v1/audio/translations
        """
        try:
            response = await openai.Audio.atranslate(file=audio_file, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_speech(self, input_text: str, **kwargs) -> bytes:
        """
        Async: Generate spoken audio from text.
        POST /v1/audio/speech
        """
        try:
            response = await openai.Audio.acreate(input=input_text, **kwargs)
            return response.content if hasattr(response, "content") else response
        except Exception as e:
            self._handle_error(e)
