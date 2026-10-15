# src/deep_sql_agent/service.py

from __future__ import annotations

from typing import Any

from deep_sql_agent.agent import AgentResponse
from deep_sql_agent.agent_factory import SQLAgentFactory
from deep_sql_agent.schema import SQLSchemaProvider
from deep_sql_agent.tools import SQLExecutionTool


class AgentService:
    """Composition root and public interface for the SQL agent."""

    def __init__(
        self,
        database_connector: Any,
        model_factory: Any,
        validator: Any,
        prompt_builder: Any,
    ) -> None:
        raise NotImplementedError

    def build_agent(self) -> Any:
        """Assemble and return the configured SQL agent."""
        raise NotImplementedError

    def answer(self, question: str) -> AgentResponse:
        """Answer a natural-language database question."""
        raise NotImplementedError