# tests/test_prompts.py

from langchain_core.prompts import ChatPromptTemplate
import pytest

from deep_sql_agent.prompts import AgentPromptBuilder


@pytest.fixture
def schema_context():
    return """
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """


def test_build_system_prompt_includes_schema_context(schema_context):
    builder = AgentPromptBuilder()

    prompt = builder.build_system_prompt(schema_context)

    assert schema_context.strip() in prompt


@pytest.mark.parametrize(
    "expected_instruction",
    [
        "read-only",
        "do not modify",
        "safe_sql_execution",
        "do not invent",
    ],
)
def test_build_system_prompt_contains_safety_instructions(
    schema_context,
    expected_instruction,
):
    builder = AgentPromptBuilder()

    prompt = builder.build_system_prompt(schema_context)

    assert expected_instruction in prompt.lower()


@pytest.mark.parametrize(
    "schema_context",
    [
        "",
        " ",
        "\n\t",
        None,
        123,
        [],
        {},
    ],
)
def test_build_system_prompt_rejects_invalid_schema_context(schema_context):
    builder = AgentPromptBuilder()

    with pytest.raises(
        ValueError,
        match="schema_context must be a non-empty string",
    ):
        builder.build_system_prompt(schema_context)


def test_build_chat_prompt_returns_chat_prompt_template(schema_context):
    builder = AgentPromptBuilder()

    prompt = builder.build_chat_prompt(schema_context)

    assert isinstance(prompt, ChatPromptTemplate)


def test_build_chat_prompt_formats_question_and_schema(schema_context):
    builder = AgentPromptBuilder()
    prompt = builder.build_chat_prompt(schema_context)

    messages = prompt.format_messages(
        user_question="How many customers are there?",
        agent_scratchpad=[],
    )

    assert schema_context.strip() in messages[0].content
    assert "How many customers are there?" in messages[1].content


def test_build_chat_prompt_exposes_required_input_variables(schema_context):
    builder = AgentPromptBuilder()

    prompt = builder.build_chat_prompt(schema_context)

    assert set(prompt.input_variables) == {
        "agent_scratchpad",
        "user_question",
    }