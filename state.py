from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowState(BaseModel):
    """Represents the state that flows through the workflow."""
    data: Dict[str, Any] = Field(default_factory=dict)
    current_node: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    execution_log: list = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_log(self, message: str, level: str = "INFO"):
        self.execution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        })
    
    def update_state(self, **updates):
        self.data.update(updates)
