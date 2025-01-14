import json
from time import time
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, ConfigDict, Field

from agno.media import ImageInput
from agno.utils.log import logger


class MessageReferences(BaseModel):
    """References added to user message"""

    # The query used to retrieve the references.
    query: str
    # References (from the vector database or function calls)
    references: Optional[List[Dict[str, Any]]] = None
    # Time taken to retrieve the references.
    time: Optional[float] = None


class Message(BaseModel):
    """Message sent to the Model"""

    # The role of the message author.
    # One of system, developer, user, assistant, or tool.
    role: str
    # The contents of the message.
    content: Optional[Union[List[Any], str]] = None
    # An optional name for the participant.
    # Provides the model information to differentiate between participants of the same role.
    name: Optional[str] = None
    # Tool call that this message is responding to.
    tool_call_id: Optional[str] = None
    # The tool calls generated by the model, such as function calls.
    tool_calls: Optional[List[Dict[str, Any]]] = None

    # Additional modalities
    audio: Optional[Any] = None
    images: Optional[Sequence[ImageInput]] = None
    videos: Optional[Sequence[Any]] = None

    # --- Data not sent to the Model API ---
    # The name of the tool called
    tool_name: Optional[str] = None
    # Arguments passed to the tool
    tool_args: Optional[Any] = None
    # The error of the tool call
    tool_call_error: Optional[bool] = None
    # If True, the agent will stop executing after this tool call.
    stop_after_tool_call: bool = False
    # When True, the message will be added to the agent's memory.
    add_to_agent_memory: bool = True
    # Metrics for the message.
    metrics: Dict[str, Any] = Field(default_factory=dict)
    # The references added to the message for RAG
    references: Optional[MessageReferences] = None
    # The Unix timestamp the message was created.
    created_at: int = Field(default_factory=lambda: int(time()))

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def get_content_string(self) -> str:
        """Returns the content as a string."""
        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, list):
            import json

            return json.dumps(self.content)
        return ""

    def to_dict(self) -> Dict[str, Any]:
        _dict = self.model_dump(
            exclude_none=True,
            include={"role", "content", "audio", "name", "tool_call_id", "tool_calls"},
        )
        # Manually add the content field even if it is None
        if self.content is None:
            _dict["content"] = None

        return _dict

    def log(self, level: Optional[str] = None):
        """Log the message to the console

        @param level: The level to log the message at. One of debug, info, warning, or error.
            Defaults to debug.
        """
        _logger = logger.debug
        if level == "debug":
            _logger = logger.debug
        elif level == "info":
            _logger = logger.info
        elif level == "warning":
            _logger = logger.warning
        elif level == "error":
            _logger = logger.error

        _logger(f"============== {self.role} ==============")
        if self.name:
            _logger(f"Name: {self.name}")
        if self.tool_call_id:
            _logger(f"Tool call Id: {self.tool_call_id}")
        if self.content:
            if isinstance(self.content, str) or isinstance(self.content, list):
                _logger(self.content)
            elif isinstance(self.content, dict):
                _logger(json.dumps(self.content, indent=2))
        if self.tool_calls:
            _logger(f"Tool Calls: {json.dumps(self.tool_calls, indent=2)}")
        if self.images:
            _logger(f"Images added: {len(self.images)}")
        if self.videos:
            _logger(f"Videos added: {len(self.videos)}")
        if self.audio:
            if isinstance(self.audio, dict):
                _logger(f"Audio files added: {len(self.audio)}")
                if "id" in self.audio:
                    _logger(f"Audio ID: {self.audio['id']}")
                elif "data" in self.audio:
                    _logger("Message contains raw audio data")
            else:
                _logger(f"Audio file added: {self.audio}")

    def content_is_valid(self) -> bool:
        """Check if the message content is valid."""

        return self.content is not None and len(self.content) > 0
