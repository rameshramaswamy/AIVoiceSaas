from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    START = "start"
    SAY = "say"           # AI speaks
    LISTEN = "listen"     # Wait for user input
    DECISION = "decision" # Branch based on LLM analysis/Sentiment
    TOOL = "tool"         # Execute function (Calendar, SMS)
    TRANSFER = "transfer" # Bridge to human
    HANGUP = "hangup"

class NodeData(BaseModel):
    # 'Say' specific
    text: Optional[str] = None 
    # 'Decision' specific
    condition_prompt: Optional[str] = None # e.g., "Did the user say yes or no?"
    options: Optional[List[str]] = None    # ["yes", "no"]
    # 'Tool' specific
    tool_name: Optional[str] = None
    
class Node(BaseModel):
    id: str
    type: NodeType
    data: NodeData
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0}) # For UI

class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None # Matches 'options' in Decision node (e.g., "yes")

class Workflow(BaseModel):
    id: str
    name: str
    nodes: List[Node]
    edges: List[Edge]
    
    # Validation logic would go here to ensure graph is connected