# src/deep_sql_agent/prompts.py

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


class AgentPromptBuilder:
    """Builds version-controlled prompts for the SQL agent."""

    def build_system_prompt(self, schema_context: Any) -> str:
        self._validate_schema_context(schema_context)

        return f"""\
You are a safe, read-only SQL database assistant.

Use only the database schema provided below and the results returned by
database tools. Do not invent tables, columns, relationships, or query
results.

You must follow these rules:
1. Generate only read-only SQL queries.
2. Do not modify the database in any way.
3. Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE.
4. Use the safe_sql_execution tool to execute SQL.
5. Do not claim that a query succeeded unless the tool returned a result.
6. If the schema is insufficient to answer the question, say so clearly.
7. Prefer focused queries and select only the columns needed for the answer.

Database schema:
{schema_context.strip()}
"""

    def build_chat_prompt(
        self,
        schema_context: Any,
    ) -> ChatPromptTemplate:
        system_prompt = self.build_system_prompt(schema_context)

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessagePromptTemplate.from_template(
                    "{user_question}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    @staticmethod
    def _validate_schema_context(schema_context: Any) -> None:
        if (
            not isinstance(schema_context, str)
            or not schema_context.strip()
        ):
            raise ValueError(
                "schema_context must be a non-empty string."
            )