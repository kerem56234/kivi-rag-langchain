# src/deep_sql_agent/agent.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from deep_sql_agent.exceptions import AgentExecutionError


@dataclass(frozen=True)
class AgentResponse:
    """Normalized response returned by the SQL agent."""

    answer: str
    intermediate_steps: list[Any] = field(default_factory=list)
    success: bool = True
    error_message: str = ""


class SQLAgent:
    """Runs a configured LangChain agent executor."""

    def __init__(self, executor: Any) -> None:
        if executor is None:
            raise ValueError("executor must not be None.")

        self._executor = executor

    def answer(self, question: str) -> AgentResponse:
        """Run the agent for one natural-language database question."""
        self._validate_question(question)

        try:
            result = self._executor.invoke(
                {"user_question": question}
            )
        except Exception as exc:
            raise AgentExecutionError(
                "SQL agent failed to produce an answer."
            ) from exc

        if not isinstance(result, dict):
            raise AgentExecutionError(
                "SQL agent did not return a valid output."
            )

        output = result.get("output")

        if not isinstance(output, str) or not output.strip():
            raise AgentExecutionError(
                "SQL agent did not return a valid output."
            )

        intermediate_steps = result.get("intermediate_steps", [])

        if intermediate_steps is None:
            intermediate_steps = []

        return AgentResponse(
            answer=output,
            intermediate_steps=list(intermediate_steps),
            success=True,
            error_message="",
        )

    @staticmethod
    def _validate_question(question: Any) -> None:
        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                "question must be a non-empty string."
            )