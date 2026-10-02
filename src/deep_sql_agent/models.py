# src/deep_sql_agent/models.py

from __future__ import annotations

from langchain_ollama import ChatOllama


class OllamaModelFactory:
    """Creates LangChain Ollama model instances."""

    def __init__(
        self,
        model: str = "qwen3:latest",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ) -> None:
        raise NotImplementedError

    def create_chat_model(self) -> ChatOllama:
        raise NotImplementedError