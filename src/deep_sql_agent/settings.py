# src/deep_sql_agent/settings.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Validated application configuration."""

    database_uri: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:latest"
    temperature: float = 0.0

    def __post_init__(self) -> None:
        raise NotImplementedError

    @classmethod
    def from_env(cls) -> "AppSettings":
        raise NotImplementedError