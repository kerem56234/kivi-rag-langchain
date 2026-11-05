# Kivi-Ki (KiKi)
Die Kivi-Ki ist ein experimentelles Code-Projekt, welches mithilfe eines lokalen KI-Modells Kivi-Kundendaten analysiert.

## Funktionsweise
Eine Frage wird als Input angenommen und an KiKi weitergegeben. KiKi überlegt sich, welche Daten für die Frage relevant sein könnten und formuliert eine SQL-Abfrage. KiKi holt sich die Daten und formuliert eine Antwort auf die Frage oder argumentiert, warum die zugrunde liegenden Daten nicht ausreichen, um die Frage sinnvoll zu beantworten.

## Technologien
Die lokale Ki läuft auf einem Ollama-Server. In unserer Testumgebung haben wir Ollama auf einer Intel Arc Pro B70 mit 32GB Grafikspeicher laufen lassen. Qwen3.8:27b hat sich als das zuverlässigste Modell für unsere Anwendung ergeben.
Die Ki-Anwendung nutzt die Langchain Python-Bibliothek für Schnittstellen und Tool-Aufrufe.
Die Anwendung wurde in Python geschrieben.

## UML
```mermaid
classDiagram
    direction LR

    class CLI {
        +main(argv) int
    }

    class AppSettings {
        +database_uri: str
        +ollama_base_url: str
        +ollama_model: str
        +temperature: float
        +from_env() AppSettings
    }

    class ApplicationFactory {
        +create_service(settings) AgentService
        +from_environment() AgentService
    }

    class AgentService {
        -agent
        +build_agent() SQLAgent
        +answer(question) AgentResponse
    }

    class DatabaseConnector {
        +create_sql_database() SQLDatabase
        +test_connection(database) bool
    }

    class SQLSchemaProvider {
        +get_table_names() list
        +get_schema_context() str
        +get_table_info(table_names) str
    }

    class OllamaModelFactory {
        +create_chat_model() ChatOllama
    }

    class AgentPromptBuilder {
        +build_system_prompt(schema) str
        +build_chat_prompt(schema) ChatPromptTemplate
    }

    class SQLQueryValidator {
        +validate(query) ValidationResult
        +is_read_only(query) bool
        +reject_dangerous_sql(query)
    }

    class SQLExecutionTool {
        +run(query) str
        +as_langchain_tool() BaseTool
    }

    class SQLAgentFactory {
        +create(schema_context) SQLAgent
    }

    class LangChainAgentAdapter {
        +invoke(inputs) dict
    }

    class SQLAgent {
        +answer(question) AgentResponse
    }

    class AgentResponse {
        +answer: str
        +intermediate_steps: list
        +success: bool
        +error_message: str
    }

    CLI --> ApplicationFactory
    ApplicationFactory --> AppSettings
    ApplicationFactory --> AgentService
    AgentService --> DatabaseConnector
    AgentService --> SQLSchemaProvider
    AgentService --> OllamaModelFactory
    AgentService --> SQLExecutionTool
    AgentService --> SQLAgentFactory
    SQLAgentFactory --> AgentPromptBuilder
    SQLAgentFactory --> LangChainAgentAdapter
    SQLAgentFactory --> SQLAgent
    SQLExecutionTool --> SQLQueryValidator
    SQLAgent --> AgentResponse
```
# Konfiguration
Vor Benutzung müssen folgende Umgebungsvariablen gesetzt werden:
## Datenbank URI
Nach folgendem Format: 
``` bash
export DEEP_SQL_DATABASE_URI='postgresql+psycopg://reader:password@localhost:5432/your_database'
```
## Ollama 
### Ollama URL
Standard:
```bash
export DEEP_SQL_OLLAMA_BASE_URL='http://localhost:11434'
```
### Ollama Model
z.B. mit qwen3.8:latest
```bash
export DEEP_SQL_OLLAMA_MODEL='qwen3.8:latest'
```
### Ollama Temperatur
Konfiguriert wie "kreativ" das Modell ist, für diese Anwendung ist 0,0 empfohlen. 
```bash
export DEEP_SQL_TEMPERATURE='0.0'
```
## Tabellen
Hier werden die Tabellen ausgewählt, die übergeben werden sollen. Je mehr Tabellen übergeben werden, umso mehr wird der Kontext des Modells ausgelastet. Eine präzise Wahl der Tabellen für den jeweiligen Anwendungsfall ist sinnvoll.
**Beispiel**: Eine Auswahl von Tabellen für Finanzfragen (kivitendo-erp)
```bash
export DEEP_SQL_INCLUDE_TABLES='customer, invoice, orderitems, order_statuses, business, ar, ap'
```
# Aufruf
Das Programm kann nach Installation mit `deep-sql-agent` aufgerufen werden, mit folgenden Parametern:
```bash
deep-sql-agent  --debug[optional] <user prompt>
```
*--debug* loggt Informationen und kann beim Debugging helfen.



