# src/deep_sql_agent/agent_factory.py

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from deep_sql_agent.agent import SQLAgent


class LangChainAgentAdapter:
    """Adapts a LangChain agent graph to the SQLAgent executor contract."""

    def __init__(self, langchain_agent: Any) -> None:
        raise NotImplementedError

    def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class SQLAgentFactory:
    """Assembles the model, prompt, and safe tool into a SQLAgent."""

    def __init__(
        self,
        model: Any,
        execution_tool: Any,
        prompt_builder: Any,
    ) -> None:
        raise NotImplementedError

    def create(self, schema_context: str) -> SQLAgent:
        raise NotImplementedError