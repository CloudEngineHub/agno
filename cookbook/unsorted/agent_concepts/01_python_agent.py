from pathlib import Path

from agno.agent.python import PythonAgent
from agno.file.local.csv import CsvFile
from agno.models.openai import OpenAIChat

cwd = Path(__file__).parent.resolve()
tmp = cwd.joinpath("tmp")
if not tmp.exists():
    tmp.mkdir(exist_ok=True, parents=True)

python_agent = PythonAgent(
    model=OpenAIChat(id="gpt-4o"),
    base_dir=tmp,
    files=[
        CsvFile(
            path="https://phidata-public.s3.amazonaws.com/demo_data/IMDB-Movie-Data.csv",
            description="Contains information about movies from IMDB.",
        )
    ],
    markdown=True,
    pip_install=True,
    show_tool_calls=True,
)
python_agent.print_response("What is the average rating of movies?")
