# tests/test_models.py

from unittest.mock import MagicMock, patch

import pytest

from deep_sql_agent.exceptions import ModelError
from deep_sql_agent.models import OllamaModelFactory


def test_create_chat_model_uses_langchain_chat_ollama():
    with patch("deep_sql_agent.models.ChatOllama") as chat_ollama_class:
        fake_model = MagicMock()
        chat_ollama_class.return_value = fake_model

        factory = OllamaModelFactory(
            model="qwen3:latest",
            base_url="http://localhost:11434",
            temperature=0.2,
        )

        model = factory.create_chat_model()

        assert model is fake_model
        chat_ollama_class.assert_called_once_with(
            model="qwen3:latest",
            base_url="http://localhost:11434",
            temperature=0.2,
        )


def test_constructor_uses_safe_defaults():
    factory = OllamaModelFactory()

    assert factory.model == "qwen3:latest"
    assert factory.base_url == "http://localhost:11434"
    assert factory.temperature == 0.0


@pytest.mark.parametrize(
    "model",
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
def test_constructor_rejects_invalid_model_name(model):
    with pytest.raises(ValueError, match="model must be a non-empty string"):
        OllamaModelFactory(model=model)


@pytest.mark.parametrize(
    "base_url",
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
def test_constructor_rejects_invalid_base_url(base_url):
    with pytest.raises(ValueError, match="base_url must be a non-empty string"):
        OllamaModelFactory(base_url=base_url)


@pytest.mark.parametrize(
    "temperature",
    [
        -0.1,
        2.1,
        "0.5",
        None,
        [],
        {},
    ],
)
def test_constructor_rejects_invalid_temperature(temperature):
    with pytest.raises(
        ValueError,
        match="temperature must be a number between 0 and 2",
    ):
        OllamaModelFactory(temperature=temperature)


def test_create_chat_model_wraps_model_creation_errors():
    with patch("deep_sql_agent.models.ChatOllama") as chat_ollama_class:
        original_error = RuntimeError("ollama config failed")
        chat_ollama_class.side_effect = original_error

        factory = OllamaModelFactory()

        with pytest.raises(
            ModelError,
            match="Failed to create Ollama chat model",
        ) as error:
            factory.create_chat_model()

        assert error.value.__cause__ is original_error