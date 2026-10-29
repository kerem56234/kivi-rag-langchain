# src/deep_sql_agent/application.py

from __future__ import annotations

from deep_sql_agent.database import DatabaseConnector
from deep_sql_agent.models import OllamaModelFactory
from deep_sql_agent.prompts import AgentPromptBuilder
from deep_sql_agent.service import AgentService
from deep_sql_agent.settings import AppSettings
from deep_sql_agent.sql_validation import SQLQueryValidator


class ApplicationFactory:
    """Constructs the application from validated settings."""

    @staticmethod
    def create_service(settings: AppSettings) -> AgentService:
        if settings is None:
            raise ValueError("settings must not be None.")

        database_connector = DatabaseConnector(
            database_uri=settings.database_uri,
            include_tables=settings.include_tables,
        )
        model_factory = OllamaModelFactory(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.temperature,
        )
        validator = SQLQueryValidator(read_only=True)
        prompt_builder = AgentPromptBuilder()

        return AgentService(
            database_connector=database_connector,
            model_factory=model_factory,
            validator=validator,
            prompt_builder=prompt_builder,
        )

    @classmethod
    def from_environment(cls) -> AgentService:
        settings = AppSettings.from_env()
        return cls.create_service(settings)