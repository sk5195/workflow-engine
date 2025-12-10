from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

# Request/Response Models
class NodeType(str, Enum):
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"

class NodeCreate(BaseModel):
    node_id: str
    node_type: NodeType = NodeType.TASK
    function: str
    next_nodes: Dict[str, str] = Field(default_factory=dict)

class WorkflowCreate(BaseModel):
    name: str
    entry_point: str
    nodes: Dict[str, NodeCreate]

class WorkflowRunRequest(BaseModel):
    workflow_name: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class WorkflowStateResponse(BaseModel):
    data: Dict[str, Any]
    current_node: Optional[str]
    status: str
    execution_log: List[LogEntry]
    metadata: Dict[str, Any]

class WorkflowRunResponse(BaseModel):
    run_id: str
    status: str
    state: WorkflowStateResponse

class WorkflowResponse(BaseModel):
    name: str
    entry_point: str
    nodes: Dict[str, Any]

class ErrorResponse(BaseModel):
    detail: str
