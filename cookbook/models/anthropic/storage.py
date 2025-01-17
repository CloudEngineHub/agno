"""Run `pip install duckduckgo-search sqlalchemy anthropic` to install dependencies."""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.agent.postgres import PostgresDbAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20241022"),
    storage=PostgresDbAgentStorage(table_name="agent_sessions", db_url=db_url),
    tools=[DuckDuckGoTools()],
    add_history_to_messages=True,
)
agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")
