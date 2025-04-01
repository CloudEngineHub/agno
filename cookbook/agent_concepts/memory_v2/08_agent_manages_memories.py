"""
This example shows how to use the Memory class to create a persistent memory.

Every time you run this, the `Memory` object will be re-initialized from the DB.
"""

from typing import List
from agno.agent.agent import Agent
from agno.memory_v2.db.memory.sqlite import SqliteMemoryDb
from agno.memory_v2.db.schema import MemoryRow
from agno.memory_v2.memory import Memory
from agno.models.google.gemini import Gemini

memory_db = SqliteMemoryDb(table_name="memory", db_file="tmp/memory.db")

# No need to set the model, it gets set by the agent to the agent's model
memory = Memory(
    memory_db=memory_db
)

john_doe_id = "john_doe@example.com"

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    memory=memory,
    enable_agentic_memory=True,
    user_id=john_doe_id
)

agent.print_response("My name is John Doe and I like to hike in the mountains on weekends.", stream=True)

agent.print_response("What are my hobbies?", stream=True)

memories = memory.get_user_memories(user_id=john_doe_id)
print("John Doe's memories:")
for i, m in enumerate(memories):
    print(f"{i}: {m.memory}")