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
        self._validate_dependency(
            database_connector,
            "database_connector",
        )
        self._validate_dependency(
            model_factory,
            "model_factory",
        )
        self._validate_dependency(
            validator,
            "validator",
        )
        self._validate_dependency(
            prompt_builder,
            "prompt_builder",
        )

        self._database_connector = database_connector
        self._model_factory = model_factory
        self._validator = validator
        self._prompt_builder = prompt_builder
        self._agent = None

    def build_agent(self) -> Any:
        """Assemble and return the configured SQL agent."""
        database = (
            self._database_connector.create_sql_database()
        )
        model = self._model_factory.create_chat_model()

        schema_provider = SQLSchemaProvider(database)
        schema_context = schema_provider.get_schema_context()

        execution_tool = SQLExecutionTool(
            database=database,
            validator=self._validator,
        )

        agent_factory = SQLAgentFactory(
            model=model,
            execution_tool=execution_tool,
            prompt_builder=self._prompt_builder,
        )

        return agent_factory.create(schema_context)

    def answer(self, question: str) -> AgentResponse:
        """Answer a natural-language database question."""
        if self._agent is None:
            self._agent = self.build_agent()

        return self._agent.answer(question)

    @staticmethod
    def _validate_dependency(
        value: Any,
        name: str,
    ) -> None:
        if value is None:
            raise ValueError(f"{name} must not be None.")