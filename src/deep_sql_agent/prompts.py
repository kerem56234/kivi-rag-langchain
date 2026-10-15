# src/deep_sql_agent/prompts.py

from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate


class AgentPromptBuilder:
    """Builds version-controlled prompts for the SQL agent."""

    def build_system_prompt(self, schema_context: Any) -> str:
        raise NotImplementedError

    def build_chat_prompt(
        self,
        schema_context: Any,
    ) -> ChatPromptTemplate:
        raise NotImplementedError