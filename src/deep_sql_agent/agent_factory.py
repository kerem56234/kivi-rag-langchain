# src/deep_sql_agent/agent_factory.py

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage

from deep_sql_agent.agent import SQLAgent
from deep_sql_agent.exceptions import AgentConfigurationError


class LangChainAgentAdapter:
    """Adapts a LangChain agent graph to the SQLAgent executor contract."""

    SAFE_SQL_TOOL_NAME = "safe_sql_execution"

    def __init__(self, langchain_agent: Any) -> None:
        if langchain_agent is None:
            raise ValueError("langchain_agent must not be None.")

        self._langchain_agent = langchain_agent

    def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Invoke LangChain and normalize its message-based result."""
        user_question = inputs["user_question"]

        result = self._langchain_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_question,
                    }
                ]
            }
        )

        messages = self._extract_messages(result)
        final_message = messages[-1]
        final_answer = getattr(final_message, "content", None)

        if not isinstance(final_answer, str) or not final_answer.strip():
            raise AgentConfigurationError(
                "LangChain agent did not return a valid final answer."
            )

        if not self._has_completed_safe_sql_execution(messages):
            raise AgentConfigurationError(
                "The agent answered without executing "
                "safe_sql_execution."
            )

        return {
            "output": final_answer,
            "intermediate_steps": list(messages[:-1]),
        }

    @classmethod
    def _has_completed_safe_sql_execution(
        cls,
        messages: list[Any],
    ) -> bool:
        safe_call_ids = cls._collect_safe_sql_call_ids(messages)
        completed_call_ids = cls._collect_completed_tool_call_ids(
            messages
        )

        return bool(safe_call_ids.intersection(completed_call_ids))

    @classmethod
    def _collect_safe_sql_call_ids(
        cls,
        messages: list[Any],
    ) -> set[str]:
        safe_call_ids: set[str] = set()

        for message in messages:
            tool_calls = getattr(message, "tool_calls", None)

            if not isinstance(tool_calls, (list, tuple)):
                continue

            for tool_call in tool_calls:
                tool_name = cls._tool_call_value(
                    tool_call,
                    "name",
                )
                tool_call_id = cls._tool_call_value(
                    tool_call,
                    "id",
                )

                if (
                    tool_name == cls.SAFE_SQL_TOOL_NAME
                    and isinstance(tool_call_id, str)
                    and tool_call_id
                ):
                    safe_call_ids.add(tool_call_id)

        return safe_call_ids

    @staticmethod
    def _collect_completed_tool_call_ids(
        messages: list[Any],
    ) -> set[str]:
        completed_call_ids: set[str] = set()

        for message in messages:
            if not isinstance(message, ToolMessage):
                continue

            tool_call_id = getattr(
                message,
                "tool_call_id",
                None,
            )

            if isinstance(tool_call_id, str) and tool_call_id:
                completed_call_ids.add(tool_call_id)

        return completed_call_ids

    @staticmethod
    def _tool_call_value(
        tool_call: Any,
        field_name: str,
    ) -> Any:
        if isinstance(tool_call, dict):
            return tool_call.get(field_name)

        return getattr(tool_call, field_name, None)

    @staticmethod
    def _extract_messages(result: Any) -> list[Any]:
        if not isinstance(result, dict):
            raise AgentConfigurationError(
                "LangChain agent did not return a valid message result."
            )

        messages = result.get("messages")

        if not isinstance(messages, (list, tuple)) or not messages:
            raise AgentConfigurationError(
                "LangChain agent did not return a valid message result."
            )

        return list(messages)


class SQLAgentFactory:
    """Assembles the model, prompt, and safe tool into a SQLAgent."""

    def __init__(
        self,
        model: Any,
        execution_tool: Any,
        prompt_builder: Any,
    ) -> None:
        self._validate_dependency(model, "model")
        self._validate_dependency(execution_tool, "execution_tool")
        self._validate_dependency(prompt_builder, "prompt_builder")

        self._model = model
        self._execution_tool = execution_tool
        self._prompt_builder = prompt_builder

    def create(self, schema_context: str) -> SQLAgent:
        """Create the configured LangChain agent and application wrapper."""
        try:
            system_prompt = self._prompt_builder.build_system_prompt(
                schema_context
            )
            langchain_tool = self._execution_tool.as_langchain_tool()

            langchain_agent = create_agent(
                model=self._model,
                tools=[langchain_tool],
                system_prompt=system_prompt,
            )

            adapter = LangChainAgentAdapter(langchain_agent)
            return SQLAgent(executor=adapter)

        except Exception as exc:
            raise AgentConfigurationError(
                "Failed to create LangChain SQL agent."
            ) from exc

    @staticmethod
    def _validate_dependency(value: Any, name: str) -> None:
        if value is None:
            raise ValueError(f"{name} must not be None.")