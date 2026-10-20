# KIVI RAG LangChain

A local-first, test-driven SQL agent built with **Python**, **LangChain**, **PostgreSQL**, and **Ollama**.

The application accepts natural-language questions about a PostgreSQL database, determines which read-only SQL query is required, executes it through a validated tool, and presents the result as a natural-language answer.

This project does not rebuild LangChain’s agent framework from scratch. It uses existing LangChain and Ollama integrations while providing a controlled, object-oriented application layer for configuration, SQL safety, database access, error handling, testing, and dependency assembly.

---

## Project Goals

The SQL agent is designed to:

1. Receive a natural-language database question.
2. Inspect the available PostgreSQL schema.
3. Determine which information is required.
4. Generate an appropriate read-only SQL query.
5. Validate the SQL before execution.
6. Execute the query through a controlled LangChain tool.
7. Interpret the returned rows.
8. Produce a useful natural-language answer.
9. Preserve execution information for testing and debugging.

The system is intended to be:

- local-first;
- read-only by default;
- modular;
- testable;
- configurable;
- easy to extend;
- independent of cloud-hosted language models.

---

## Technology Stack

- **Python 3.11+**
- **LangChain**
- **LangChain Core**
- **LangChain Community**
- **LangChain Ollama**
- **Ollama**
- **PostgreSQL**
- **SQLAlchemy**
- **psycopg**
- **pytest**
- **setuptools**

---

## Design Principles

### Use Existing Integrations

LangChain already provides useful building blocks for:

- model integration;
- structured tools;
- agent execution;
- message handling;
- SQL database abstraction;
- prompt construction.

The project uses these components instead of rebuilding their underlying mechanics.

Our own code focuses on application-specific concerns such as:

- read-only SQL validation;
- controlled SQL execution;
- typed configuration;
- dependency assembly;
- predictable response objects;
- application-specific exceptions;
- testability;
- command-line access.

---

### Red–Green–Refactor

Development follows the **Red–Green–Refactor** cycle:

1. **Red** — write a failing unit test.
2. **Green** — implement the minimum code needed to pass.
3. **Refactor** — improve the design while keeping all tests green.

Each meaningful application module has a corresponding test module.

---

### Defense in Depth

Model-generated SQL must not be trusted by default.

The application therefore uses several layers of protection:

1. The system prompt instructs the model to generate read-only SQL.
2. SQL is sent through `SQLQueryValidator`.
3. Only validated SQL is passed to the database.
4. The database should be accessed through a restricted PostgreSQL role.
5. PostgreSQL should independently enforce read-only access and timeouts.

Application-level validation is not a replacement for database permissions.

---

## Project Structure

```text
kivi-rag-langchain/
├── src/
│   └── deep_sql_agent/
│       ├── __init__.py
│       ├── agent.py
│       ├── agent_factory.py
│       ├── application.py
│       ├── cli.py
│       ├── database.py
│       ├── exceptions.py
│       ├── models.py
│       ├── prompts.py
│       ├── schema.py
│       ├── service.py
│       ├── settings.py
│       ├── sql_validation.py
│       └── tools.py
├── tests/
│   ├── test_agent.py
│   ├── test_agent_factory.py
│   ├── test_application.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_models.py
│   ├── test_prompts.py
│   ├── test_schema.py
│   ├── test_service.py
│   ├── test_settings.py
│   ├── test_sql_validation.py
│   └── test_tools.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## Architecture

```mermaid
flowchart TD
    User[User Question] --> CLI[CLI]
    CLI --> AppFactory[ApplicationFactory]
    AppFactory --> Settings[AppSettings]
    AppFactory --> Service[AgentService]

    Service --> DBConnector[DatabaseConnector]
    Service --> ModelFactory[OllamaModelFactory]
    Service --> SchemaProvider[SQLSchemaProvider]
    Service --> ExecutionTool[SQLExecutionTool]
    Service --> AgentFactory[SQLAgentFactory]

    DBConnector --> SQLDatabase[LangChain SQLDatabase]
    SQLDatabase --> PostgreSQL[(PostgreSQL)]

    ModelFactory --> Ollama[ChatOllama]
    SchemaProvider --> SQLDatabase

    AgentFactory --> PromptBuilder[AgentPromptBuilder]
    AgentFactory --> Ollama
    AgentFactory --> ExecutionTool
    AgentFactory --> LangChainAgent[LangChain Agent]

    LangChainAgent --> ExecutionTool
    ExecutionTool --> Validator[SQLQueryValidator]
    Validator -->|Valid| SQLDatabase
    Validator -->|Invalid| ValidationError[SQLValidationError]

    PostgreSQL --> LangChainAgent
    LangChainAgent --> Adapter[LangChainAgentAdapter]
    Adapter --> SQLAgent[SQLAgent]
    SQLAgent --> Response[AgentResponse]
    Response --> CLI
```

---

## Runtime Flow

When the following command is executed:

```bash
deep-sql-agent "How many customers are there?"
```

the application performs these steps:

1. `cli.py` parses the command-line question.
2. `AppSettings.from_env()` loads runtime configuration.
3. `ApplicationFactory` creates the application dependencies.
4. `AgentService` creates or reuses the configured SQL agent.
5. `DatabaseConnector` creates a LangChain `SQLDatabase`.
6. `SQLSchemaProvider` retrieves schema context.
7. `OllamaModelFactory` creates the local chat model.
8. `AgentPromptBuilder` creates the SQL-agent instructions.
9. `SQLExecutionTool` is exposed as a LangChain structured tool.
10. `SQLAgentFactory` assembles the LangChain agent.
11. The agent receives the user’s question.
12. Generated SQL is validated by `SQLQueryValidator`.
13. Valid SQL is executed against PostgreSQL.
14. The agent interprets the returned data.
15. `SQLAgent` normalizes the result into an `AgentResponse`.
16. The CLI prints the final answer.

---

## Components

### `settings.py`

Defines the immutable `AppSettings` configuration object.

Configuration includes:

- PostgreSQL connection URI;
- Ollama base URL;
- Ollama model name;
- model temperature.

Settings can be created directly or loaded from environment variables.

```python
from deep_sql_agent.settings import AppSettings

settings = AppSettings(
    database_uri=(
        "postgresql+psycopg://"
        "reader:password@localhost:5432/example"
    ),
    ollama_base_url="http://localhost:11434",
    ollama_model="qwen3:latest",
    temperature=0.0,
)
```

---

### `application.py`

`ApplicationFactory` creates the complete application from `AppSettings`.

It constructs:

- `DatabaseConnector`;
- `OllamaModelFactory`;
- `SQLQueryValidator`;
- `AgentPromptBuilder`;
- `AgentService`.

This keeps dependency assembly out of the CLI and other user interfaces.

---

### `database.py`

`DatabaseConnector` wraps LangChain’s SQL database abstraction.

It is responsible for:

- validating the database URI;
- creating `SQLDatabase`;
- testing connectivity with `SELECT 1`;
- translating construction failures into `DatabaseError`.

---

### `models.py`

`OllamaModelFactory` creates the LangChain `ChatOllama` model.

It centralizes:

- model name;
- Ollama server URL;
- temperature;
- configuration validation;
- model-construction error handling.

---

### `schema.py`

`SQLSchemaProvider` retrieves database metadata.

It can:

- list usable tables;
- retrieve schema context for all available tables;
- retrieve schema information for selected tables.

This component isolates schema inspection from agent orchestration.

---

### `sql_validation.py`

`SQLQueryValidator` checks model-generated SQL before execution.

It currently rejects:

- non-string values;
- empty SQL;
- multiple SQL statements;
- non-read-only statements;
- destructive SQL keywords.

Examples of rejected operations include:

- `INSERT`;
- `UPDATE`;
- `DELETE`;
- `DROP`;
- `ALTER`;
- `TRUNCATE`;
- `CREATE`;
- `GRANT`;
- `REVOKE`;
- `MERGE`;
- `CALL`;
- `EXECUTE`.

The validator returns a `ValidationResult`:

```python
ValidationResult(
    is_valid=True,
    reason="",
)
```

It can also raise `SQLValidationError` through its exception-based interface.

The current validator is an application guardrail, not a full PostgreSQL parser. Database-level read-only enforcement remains required.

---

### `tools.py`

`SQLExecutionTool` is the controlled SQL execution boundary.

Its execution flow is:

```text
SQL query
  → SQLQueryValidator
  → reject unsafe SQL
  → SQLDatabase.run(...)
  → return database result
```

The class can be converted into a LangChain `StructuredTool`:

```python
langchain_tool = execution_tool.as_langchain_tool()
```

The exposed tool is named:

```text
safe_sql_execution
```

---

### `prompts.py`

`AgentPromptBuilder` stores the version-controlled SQL-agent instructions.

The system prompt instructs the model to:

- use only the supplied schema and database results;
- avoid inventing tables or columns;
- generate read-only SQL;
- avoid database modifications;
- use `safe_sql_execution`;
- avoid claiming that unexecuted SQL succeeded;
- report insufficient schema context;
- prefer focused queries.

Prompt construction is kept separate from agent creation so that prompt behavior can be tested independently.

---

### `agent_factory.py`

`SQLAgentFactory` assembles:

- the Ollama chat model;
- the system prompt;
- the safe SQL tool;
- the LangChain agent.

`LangChainAgentAdapter` translates between the application’s executor interface and LangChain’s message-based interface.

Application input:

```python
{
    "user_question": "How many customers are there?"
}
```

LangChain input:

```python
{
    "messages": [
        {
            "role": "user",
            "content": "How many customers are there?",
        }
    ]
}
```

The adapter normalizes the returned message sequence into an output and intermediate steps.

---

### `agent.py`

`SQLAgent` is the stable application wrapper around the configured LangChain agent.

It:

- validates the natural-language question;
- invokes the executor;
- validates the executor result;
- normalizes intermediate steps;
- returns an `AgentResponse`;
- wraps execution failures in `AgentExecutionError`.

The response model currently contains:

```python
AgentResponse(
    answer="There are 42 customers.",
    intermediate_steps=[],
    success=True,
    error_message="",
)
```

---

### `service.py`

`AgentService` is the main application facade.

It assembles the runtime agent from:

- database connection;
- database schema;
- Ollama model;
- SQL validator;
- execution tool;
- prompt builder;
- agent factory.

The configured agent is cached after the first question and reused for later questions.

The public interface is:

```python
response = service.answer(
    "How many customers are there?"
)
```

---

### `cli.py`

The CLI provides terminal access to the application.

It:

- parses a natural-language question;
- loads configuration from the environment;
- creates the application;
- invokes the agent;
- prints the final answer;
- returns an appropriate process exit code.

---

### `exceptions.py`

Defines application-specific exceptions, including:

- `AgentError`;
- `DatabaseError`;
- `ModelError`;
- `SQLValidationError`;
- `AgentConfigurationError`;
- `AgentExecutionError`.

These exceptions keep higher-level code independent from arbitrary low-level library errors.

---

## Installation

### 1. Create a virtual environment

```bash
python -m venv env
source env/bin/activate
```

### 2. Install the project

For development, install the repository in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Alternatively, install the dependency file first:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 3. Install or start Ollama

Verify that Ollama is available:

```bash
ollama --version
ollama list
```

Pull the configured model if necessary:

```bash
ollama pull qwen3:latest
```

Start the Ollama service if it is not already running:

```bash
ollama serve
```

---

## Configuration

The application reads its runtime configuration from environment variables.

### Required variable

```bash
export DEEP_SQL_DATABASE_URI='postgresql+psycopg://reader:password@localhost:5432/example'
```

### Optional variables

```bash
export DEEP_SQL_OLLAMA_BASE_URL='http://localhost:11434'
export DEEP_SQL_OLLAMA_MODEL='qwen3:latest'
export DEEP_SQL_TEMPERATURE='0.0'
```

### Configuration reference

| Variable | Required | Default | Description |
|---|---:|---|---|
| `DEEP_SQL_DATABASE_URI` | Yes | None | SQLAlchemy-compatible PostgreSQL connection URI |
| `DEEP_SQL_OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `DEEP_SQL_OLLAMA_MODEL` | No | `qwen3:latest` | Ollama chat model |
| `DEEP_SQL_TEMPERATURE` | No | `0.0` | Model temperature between `0` and `2` |

Environment variables exported with `export` remain available in the current shell and processes started from it. They are normally removed when the shell session ends.

Do not commit real database passwords to the repository.

---

## PostgreSQL Security

Use a dedicated read-only PostgreSQL account.

Example:

```sql
CREATE ROLE deep_sql_reader
    LOGIN
    PASSWORD 'replace-this-password';

GRANT CONNECT
    ON DATABASE example
    TO deep_sql_reader;

GRANT USAGE
    ON SCHEMA public
    TO deep_sql_reader;

GRANT SELECT
    ON ALL TABLES IN SCHEMA public
    TO deep_sql_reader;

ALTER DEFAULT PRIVILEGES
    IN SCHEMA public
    GRANT SELECT ON TABLES
    TO deep_sql_reader;

ALTER ROLE deep_sql_reader
    SET default_transaction_read_only = on;

ALTER ROLE deep_sql_reader
    SET statement_timeout = '15s';
```

Adjust schemas and table permissions to match the target database.

For stronger isolation, grant access only to the tables that the agent actually needs.

---

## Running the CLI

Show help:

```bash
deep-sql-agent --help
```

Ask a database question:

```bash
deep-sql-agent "How many customers are there?"
```

Ask for an aggregate explanation:

```bash
deep-sql-agent \
    "Which items sold the most, and how do their sales compare?"
```

The command returns exit code `0` on success and `1` when application execution fails.

---

## Running Tests

Run the complete suite:

```bash
pytest
```

Run with more detail:

```bash
pytest -v
```

Run one module:

```bash
pytest tests/test_sql_validation.py
```

Run one test:

```bash
pytest tests/test_tools.py::test_run_validates_query_before_execution
```

The project’s `pyproject.toml` configures `src` as the Python import path for pytest.

If necessary, it can also be supplied explicitly:

```bash
PYTHONPATH=src pytest
```

---

## Testing Strategy

Unit tests isolate external systems wherever possible.

Mocks are used for:

- PostgreSQL access;
- LangChain database objects;
- Ollama model creation;
- LangChain agent construction;
- agent invocation;
- CLI application creation.

Each major module has a corresponding test module:

```text
src/deep_sql_agent/database.py
tests/test_database.py

src/deep_sql_agent/models.py
tests/test_models.py

src/deep_sql_agent/schema.py
tests/test_schema.py

src/deep_sql_agent/sql_validation.py
tests/test_sql_validation.py

src/deep_sql_agent/tools.py
tests/test_tools.py

src/deep_sql_agent/prompts.py
tests/test_prompts.py

src/deep_sql_agent/agent.py
tests/test_agent.py

src/deep_sql_agent/agent_factory.py
tests/test_agent_factory.py

src/deep_sql_agent/service.py
tests/test_service.py

src/deep_sql_agent/settings.py
tests/test_settings.py

src/deep_sql_agent/application.py
tests/test_application.py

src/deep_sql_agent/cli.py
tests/test_cli.py
```

Live integration tests should be kept separate from deterministic unit tests.

---

## Development Roadmap

### Phase 1: Foundation

- [x] Create the `src` package structure
- [x] Configure setuptools and pytest
- [x] Add application-specific exceptions
- [x] Add read-only SQL validation
- [x] Add SQL validation tests
- [x] Add LangChain database connector
- [x] Add database connector tests

### Phase 2: LangChain and Ollama Integration

- [x] Add Ollama model factory
- [x] Add schema provider
- [x] Add validated SQL execution tool
- [x] Add LangChain structured-tool adapter
- [x] Add version-controlled prompt builder
- [x] Add normalized agent response
- [x] Add LangChain agent adapter
- [x] Add SQL agent factory

### Phase 3: Application Assembly

- [x] Add application service
- [x] Add immutable settings
- [x] Add environment-based configuration
- [x] Add application factory
- [x] Add command-line interface
- [x] Add CLI entry point
- [x] Add unit tests for all application components

### Phase 4: Integration and Hardening

- [ ] Add repeatable PostgreSQL integration tests
- [ ] Add repeatable Ollama integration tests
- [ ] Add disposable test-database setup
- [ ] Add table allowlists
- [ ] Add schema filtering
- [ ] Add configurable query limits
- [ ] Add query timeouts
- [ ] Add PostgreSQL-aware SQL parsing
- [ ] Add structured application logging
- [ ] Add SQL execution audit information
- [ ] Add configurable maximum result size
- [ ] Add dedicated query metadata to `AgentResponse`
- [ ] Add pgvector-aware schema reflection
- [ ] Evaluate migration from deprecated integration packages
- [ ] Add a web or graphical user interface

---

## Planned Hardening

The current safety layer is intentionally conservative but still requires improvement before use with sensitive databases.

Planned improvements include:

- PostgreSQL-aware SQL parsing;
- explicit schema and table allowlists;
- automatic result limits;
- execution timeouts;
- returned-row limits;
- query-complexity controls;
- audit logging;
- structured query traces;
- restricted schema reflection;
- dedicated integration tests;
- safer handling of database-specific functions.

---

## Package Dependencies

Current runtime and development dependencies include:

```text
pytest
langchain
langchain-community
langchain-ollama
sqlalchemy
psycopg
psycopg-binary
```

Databases using PostgreSQL `vector` columns may also require:

```text
pgvector
```

Install it with:

```bash
python -m pip install pgvector
```

---

## Contributing

When adding or changing behavior:

1. Identify the responsible module.
2. Add or update its unit tests.
3. Run the tests and confirm the new test fails for the intended reason.
4. Implement the smallest correct change.
5. Run the complete test suite.
6. Refactor while preserving behavior.
7. Update this README when architecture, configuration, or usage changes.

Avoid combining unrelated architectural changes in one commit.

---

## Current Status

The core application path is implemented:

```text
Environment configuration
  → dependency assembly
  → PostgreSQL schema inspection
  → Ollama model creation
  → LangChain agent creation
  → validated SQL execution
  → normalized response
  → CLI output
```
