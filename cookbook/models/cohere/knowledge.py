"""Run `pip install duckduckgo-search sqlalchemy pgvector pypdf openai cohere` to install dependencies."""

from agno.agent import Agent
from agno.models.cohere import CohereChat
from agno.knowledge.pdf import PDFUrlKnowledgeBase
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector(table_name="recipes", db_url=db_url),
)
knowledge_base.load(recreate=False)  # Comment out after first run

agent = Agent(
    model=CohereChat(id="command-r-08-2024"),
    knowledge=knowledge_base,
    use_tools=True,
    show_tool_calls=True,
)
agent.print_response("How to make Thai curry?", markdown=True)
