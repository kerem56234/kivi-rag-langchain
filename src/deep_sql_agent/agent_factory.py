# src/deep_sql_agent/agent_factory.py

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from deep_sql_agent.agent import SQLAgent
from deep_sql_agent.exceptions import AgentConfigurationError


class LangChainAgentAdapter:
    """Adapts a LangChain agent graph to the SQLAgent executor contract."""

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

        return {
            "output": final_answer,
            "intermediate_steps": list(messages[:-1]),
        }

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