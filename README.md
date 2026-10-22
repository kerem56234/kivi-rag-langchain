# KIVI Deep SQL Agent

A local-first, read-only natural-language SQL agent for PostgreSQL.

The application uses LangChain and a local Ollama model to translate natural-language questions into SQL, validate and execute the SQL, and return a natural-language answer based on database results.

## Project status

The project currently supports:

- PostgreSQL through SQLAlchemy and `psycopg`
- Local chat models through Ollama
- LangChain agent and structured-tool integration
- Read-only SQL validation
- Controlled SQL execution through `safe_sql_execution`
- Explicit table selection to keep schema context manageable
- Disabled schema sample rows by default
- Debug logging through the CLI
- Environment-based configuration
- A test-driven `src/` package layout

For large databases, **an explicit table allowlist is currently required in practice**. Loading every table can create an oversized model prompt, increase startup and inference time, and cause Ollama to truncate relevant schema information.

---

## Architecture

```text
CLI
  → AppSettings
  → ApplicationFactory
  → AgentService
      → DatabaseConnector
      → SQLSchemaProvider
      → OllamaModelFactory
      → SQLExecutionTool
      → AgentPromptBuilder
      → SQLAgentFactory
      → LangChain agent
      → SQLAgent
  → AgentResponse
```

The query path is:

```text
Natural-language question
  → LangChain agent
  → model creates a safe_sql_execution tool call
  → SQLQueryValidator
  → SQLDatabase.run(...)
  → PostgreSQL
  → tool result
  → model-generated explanation
  → CLI output
```

### Main modules

| Module | Responsibility |
|---|---|
| `settings.py` | Validates environment and application configuration |
| `application.py` | Builds application dependencies from settings |
| `service.py` | Assembles and caches the SQL agent |
| `database.py` | Creates LangChain `SQLDatabase` instances |
| `schema.py` | Retrieves usable table names and schema information |
| `models.py` | Creates the Ollama `ChatOllama` model |
| `prompts.py` | Builds the SQL-agent system prompt |
| `sql_validation.py` | Enforces application-level read-only SQL rules |
| `tools.py` | Validates and executes SQL through `safe_sql_execution` |
| `agent_factory.py` | Builds and adapts the LangChain agent |
| `agent.py` | Exposes a stable application-facing response interface |
| `logging_config.py` | Configures normal/debug logging and safe log helpers |
| `cli.py` | Implements the `deep-sql-agent` command |
| `exceptions.py` | Defines application-specific exceptions |

---

## Requirements

- Python 3.11 or newer
- PostgreSQL
- Ollama
- An Ollama model with tool-calling support
- A PostgreSQL account with read-only permissions

The default model is:

```text
qwen3:latest
```

A different model can be selected through environment configuration.

---

## Installation

Create and activate a virtual environment:

```bash
python -m venv env
source env/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Alternatively, install the dependencies directly:

```bash
python -m pip install -r requirements.txt
```

Confirm that Ollama is running:

```bash
ollama list
```

Pull the configured model if necessary:

```bash
ollama pull qwen3:latest
```

---

## Configuration

The application is configured with environment variables.

### `DEEP_SQL_DATABASE_URI`

**Required.**

A SQLAlchemy-compatible PostgreSQL connection URI:

```bash
export DEEP_SQL_DATABASE_URI='postgresql+psycopg://reader:password@localhost:5432/database_name'
```

Use a dedicated read-only database account.

### `DEEP_SQL_OLLAMA_BASE_URL`

Optional.

Default:

```text
http://localhost:11434
```

Example:

```bash
export DEEP_SQL_OLLAMA_BASE_URL='http://localhost:11434'
```

### `DEEP_SQL_OLLAMA_MODEL`

Optional.

Default:

```text
qwen3:latest
```

Example:

```bash
export DEEP_SQL_OLLAMA_MODEL='qwen3:latest'
```

### `DEEP_SQL_TEMPERATURE`

Optional.

Default:

```text
0.0
```

The accepted range is:


$$
0 \leq t \leq 2
$$


Example:

```bash
export DEEP_SQL_TEMPERATURE='0.0'
```

### `DEEP_SQL_INCLUDE_TABLES`

Optional in configuration, but strongly recommended for large databases.

This is a comma-separated allowlist of tables that LangChain may reflect and expose to the model:

```bash
export DEEP_SQL_INCLUDE_TABLES='delivery_orders,delivery_order_items,customer,record_links'
```

Table names must:

- Be comma-separated
- Be valid unquoted SQL identifiers
- Contain only letters, digits, and underscores
- Begin with a letter or underscore
- Be unique
- Exist in the configured database

If a question requires a table outside the allowlist, add the table and run the CLI again.

### Complete example

```bash
export DEEP_SQL_DATABASE_URI='postgresql+psycopg://reader:password@localhost:5432/kivi'
export DEEP_SQL_OLLAMA_BASE_URL='http://localhost:11434'
export DEEP_SQL_OLLAMA_MODEL='qwen3:latest'
export DEEP_SQL_TEMPERATURE='0.0'
export DEEP_SQL_INCLUDE_TABLES='delivery_orders,delivery_order_items,customer,parts'
```

Variables set with `export` apply to the current shell session.

Do not commit database credentials to version control.

---

## Usage

Ask one natural-language question:

```bash
deep-sql-agent "How many customers are there?"
```

Questions can also be supplied as separate shell arguments:

```bash
deep-sql-agent How many customers are there?
```

Quote questions when they contain shell-special characters.

### Example with selected tables

```bash
export DEEP_SQL_INCLUDE_TABLES='delivery_orders,delivery_order_items,customer'

deep-sql-agent \
  "Haben Kunden elektrische Kabel bestellt?"
```

The agent can only reason about tables included in the current allowlist.

---

## Debug mode

Enable detailed diagnostics with `--debug`:

```bash
deep-sql-agent --debug \
  "Schau dir die Tabelle delivery_orders an und sag mir, was du findest."
```

Debug mode provides:

- Timestamped logs
- Dependency request information
- Captured Python warnings
- Complete exception tracebacks
- Chained database, LangChain, and agent errors

Normal mode prints concise user-facing errors:

```bash
deep-sql-agent "Question"
```

Debug mode prints detailed diagnostics to standard error:

```bash
deep-sql-agent --debug "Question"
```

SQLAlchemy engine statement logging is intentionally kept at `WARNING` to avoid printing hundreds of schema-reflection statements.

Review debug logs before sharing them because they may contain database names, table names, SQL statements, or returned data.

---

## Schema-context behavior

LangChain’s `SQLDatabase` is created with sample rows disabled:

```python
SQLDatabase.from_uri(
    database_uri,
    sample_rows_in_table_info=0,
)
```

This prevents automatic sample rows from every reflected table from being added to the model prompt.

When `DEEP_SQL_INCLUDE_TABLES` is configured, it is passed to LangChain as `include_tables`:

```python
SQLDatabase.from_uri(
    database_uri,
    sample_rows_in_table_info=0,
    include_tables=[
        "delivery_orders",
        "delivery_order_items",
        "customer",
    ],
)
```

### Why table selection matters

Large databases can contain hundreds of tables. Passing all schemas to the model can:

- Exceed the model server’s input limit
- Cause silent prompt truncation
- Remove relevant table definitions or instructions
- Increase model latency
- Increase schema-reflection time
- Reduce SQL accuracy
- Confuse the model with unrelated tables

An unrestricted run previously generated approximately 48,000 prompt tokens while the active Ollama request accepted approximately 16,000 input tokens. Ollama therefore truncated the prompt before inference.

The explicit allowlist prevents this when it is configured appropriately.

### Current limitation

Table selection is manual.

The application does not yet:

1. List tables dynamically for the model
2. Select relevant tables from the user question
3. Fetch only those schemas
4. Build a question-specific schema context

Dynamic schema discovery is a planned improvement.

---

## SQL safety model

The application has multiple intended safety layers.

### Application validation

`SQLQueryValidator` currently:

- Accepts queries beginning with `SELECT` or `WITH`
- Rejects empty and non-string input
- Rejects multiple semicolon-separated statements
- Rejects common data-modification and schema-changing keywords

Blocked keywords include:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE
MERGE
CALL
EXECUTE
```

### Validator limitations

The validator is based on regular expressions and basic statement splitting. It is not a complete PostgreSQL parser.

It may not correctly handle:

- Semicolons in string literals
- SQL comments
- Writable common table expressions
- Side-effecting functions
- All PostgreSQL-specific commands
- Dangerous keywords appearing as ordinary string data

### Database permissions

Application validation must not be the only security boundary.

Use a dedicated PostgreSQL role with:

- `CONNECT` only to the required database
- `USAGE` only on required schemas
- `SELECT` only on required tables
- `default_transaction_read_only = on`
- A statement timeout
- No owner or superuser privileges

---

## Testing

Run all tests:

```bash
pytest
```

Run a focused module:

```bash
pytest tests/test_database.py -q
```

Run the schema-context-related tests:

```bash
pytest \
  tests/test_settings.py \
  tests/test_database.py \
  tests/test_application.py \
  -q
```

The project follows Red–Green–Refactor:

1. **RED** — add a failing test
2. **GREEN** — implement the minimum required behavior
3. **REFACTOR** — improve the design while preserving passing tests

External systems are mocked in unit tests, including:

- PostgreSQL
- LangChain `SQLDatabase`
- Ollama model construction
- LangChain agent creation and invocation

Live integration testing remains necessary because mocked tests cannot fully reproduce model behavior, prompt truncation, tool calling, or PostgreSQL dialect errors.

---

## Development workflow

Before beginning work:

```bash
git status
git switch main
git pull --ff-only
pytest -q
```

Create a focused branch:

```bash
git switch -c feature/short-description
```

Recommended branch separation:

- Logging/debug infrastructure
- Schema-context management
- Mandatory tool execution
- SQL retry behavior
- Persistent local workspace
- SQL-parser hardening

Do not combine unrelated architectural changes into one branch.

Before merging:

```bash
pytest -q
git diff --check
git status
```

---

## Known warnings

### `langchain-community` deprecation

The project currently imports:

```python
from langchain_community.utilities import SQLDatabase
```

`langchain-community` emits a deprecation warning because the package is being sunset.

This warning is currently non-fatal. Migration to an appropriate maintained integration should be investigated.

### PostgreSQL `vector` reflection

Databases using pgvector may emit:

```text
SAWarning: Did not recognize type 'vector' of column 'embedding'
```

A possible dependency fix is:

```bash
python -m pip install pgvector
```

The pgvector SQLAlchemy type may also need to be registered correctly.

An explicit table allowlist can avoid reflecting embedding tables when they are not relevant.

---

## Current limitations

- Table selection is manual through `DEEP_SQL_INCLUDE_TABLES`
- The SQL validator is regex-based rather than parser-based
- The model may generate syntactically invalid PostgreSQL
- SQL execution retries are not yet a stable application-level feature
- Full-schema reflection remains possible if no allowlist is configured
- Query cost is not estimated before execution
- A maximum row count is not universally enforced
- Schema context does not yet have a strict character or token budget
- Conversation and execution history are not persistently stored
- `AgentResponse` does not expose structured SQL/tool metadata
- Live integration coverage is limited

---

## Planned improvements

### Dynamic schema discovery

Replace static full-schema prompting with:

```text
User question
  → list allowed tables
  → select relevant tables
  → inspect selected schemas
  → generate SQL
  → validate and execute SQL
  → explain results
```

### SQL execution resilience

Planned improvements include:

- Return bounded query errors to the agent
- Permit a small number of corrective retries
- Distinguish SQL mistakes from infrastructure failures
- Record attempted and successful SQL separately

### Query hardening

Planned improvements include:

- Adopt a PostgreSQL-aware parser
- Enforce maximum row counts
- Automatically add or validate `LIMIT`
- Block side-effecting functions
- Apply statement timeouts
- Consider query-cost controls

### Local application workspace

A future local workspace may contain:

- Versioned schema snapshots
- Conversation transcripts
- Executed SQL
- Bounded tool outputs
- Errors and retry outcomes
- Database-identity metadata

Historical data should be retrieved selectively rather than inserted wholesale into every model prompt. Otherwise, persistent memory would recreate the same context-bloat problem.

### Observability

Planned observability improvements include:

- Structured lifecycle logs
- Schema table count and context-size metrics
- Model invocation timing
- Tool-call IDs
- SQL execution duration
- Result row counts
- Bounded result previews
- Query audit records

---

## Troubleshooting

### The model says a table is missing

Check the allowlist:

```bash
echo "$DEEP_SQL_INCLUDE_TABLES"
```

Add the required table:

```bash
export DEEP_SQL_INCLUDE_TABLES='existing_table,required_table'
```

Run the command again.

### Ollama truncates the prompt

Inspect the Ollama server log for:

```text
truncating input prompt
```

Reduce `DEEP_SQL_INCLUDE_TABLES` to only the tables needed for the task.

Do not treat increasing the context window as the primary solution. First remove irrelevant schema context.

### The CLI prints only a generic failure

Rerun with debug mode:

```bash
deep-sql-agent --debug "Your question"
```

Read the chained traceback from the bottom upward:

1. Application-level error
2. Agent or tool error
3. SQLAlchemy error
4. Underlying PostgreSQL or model error

### The model generates invalid SQL

Use debug mode to inspect the database error and generated SQL.

Common causes include:

- Incorrect table or column assumptions
- PostgreSQL reserved words used as aliases
- Required tables missing from the allowlist
- Ambiguous relationships
- Unsupported SQL syntax

### The agent is slow

Check:

- Whether Ollama is loading the model for the first time
- Whether too many tables are included
- Whether prompt truncation is occurring
- Whether the model is too large for the available hardware
- Whether schema reflection is repeated unnecessarily

---

## Repository layout

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
│       ├── logging_config.py
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
│   ├── test_logging_config.py
│   ├── test_models.py
│   ├── test_prompts.py
│   ├── test_schema.py
│   ├── test_service.py
│   ├── test_settings.py
│   ├── test_sql_validation.py
│   └── test_tools.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Definition of a grounded answer

For a database-fact question, successful behavior is:

1. The model creates a `safe_sql_execution` tool call
2. The tool receives read-only SQL
3. `SQLQueryValidator` approves the SQL
4. PostgreSQL executes the query
5. The tool returns actual rows
6. The model explains those rows
7. The final answer does not ask the user to execute SQL manually

A generated SQL block without successful execution is not a grounded database answer.
