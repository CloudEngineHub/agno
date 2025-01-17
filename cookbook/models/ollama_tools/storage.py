"""Run `pip install duckduckgo-search sqlalchemy ollama` to install dependencies."""

from agno.agent import Agent
from agno.models.ollama import OllamaTools
from agno.storage.agent.postgres import PostgresDbAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

agent = Agent(
    model=OllamaTools(id="llama3.1:8b"),
    storage=PostgresDbAgentStorage(table_name="agent_sessions", db_url=db_url),
    tools=[DuckDuckGoTools()],
    add_history_to_messages=True,
)
agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")
