from pydantic import BaseModel
from typing import Any

class WsIncoming(BaseModel):
    type: str
    text: str = ""
    session_id: str = ""
    language: str = "en"
    data: dict = {}

class WsOutgoing(BaseModel):
    type: str
    text: str = ""
    session_id: str = ""
    message: str = ""
    full_text: str = ""
    data: dict[str, Any] = {}