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
        raise NotImplementedError

    @classmethod
    def from_environment(cls) -> AgentService:
        raise NotImplementedError