# src/deep_sql_agent/models.py

from __future__ import annotations

from typing import Any

from langchain_ollama import ChatOllama

from deep_sql_agent.exceptions import ModelError


class OllamaModelFactory:
    """Creates LangChain Ollama model instances."""

    def __init__(
        self,
        model: str = "qwen3:latest",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ) -> None:
        self._validate_non_empty_string(model, "model")
        self._validate_non_empty_string(base_url, "base_url")
        self._validate_temperature(temperature)

        self.model = model
        self.base_url = base_url
        self.temperature = float(temperature)

    def create_chat_model(self) -> ChatOllama:
        try:
            return ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
            )
        except Exception as exc:
            raise ModelError(
                "Failed to create Ollama chat model."
            ) from exc

    @staticmethod
    def _validate_non_empty_string(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string."
            )

    @staticmethod
    def _validate_temperature(value: Any) -> None:
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
            or value > 2
        ):
            raise ValueError(
                "temperature must be a number between 0 and 2."
            )