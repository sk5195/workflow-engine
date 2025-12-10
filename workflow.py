from typing import Dict, Callable, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from ..models.state import WorkflowState, NodeStatus

class NodeType(str, Enum):
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"

class Node(BaseModel):
    """Represents a node in the workflow."""
    node_id: str
    node_type: NodeType = NodeType.TASK
    function: str  # Name of the function to call
    next_nodes: Dict[str, str] = Field(default_factory=dict)  # condition -> node_id
    
    class Config:
        arbitrary_types_allowed = True

class WorkflowDefinition(BaseModel):
    """Defines a workflow with nodes and edges."""
    name: str
    entry_point: str  # ID of the entry node
    nodes: Dict[str, Node] = Field(default_factory=dict)

class WorkflowEngine:
    """Executes workflows based on their definitions."""
    
    def __init__(self):
        self.registry = {}  # function name -> callable
        self.workflows: Dict[str, WorkflowDefinition] = {}
    
    def register_function(self, func: Callable):
        """Register a function to be used in workflows."""
        self.registry[func.__name__] = func
        return func
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition."""
        self.workflows[workflow.name] = workflow
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        initial_state: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """Execute a workflow with the given initial state."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
            
        workflow = self.workflows[workflow_name]
        state = WorkflowState(data=initial_state or {})
        
        current_node_id = workflow.entry_point
        
        while current_node_id:
            if current_node_id not in workflow.nodes:
                raise ValueError(f"Node '{current_node_id}' not found in workflow")
                
            node = workflow.nodes[current_node_id]
            state.current_node = node.node_id
            state.status = NodeStatus.RUNNING
            
            try:
                # Get the function from registry
                if node.function not in self.registry:
                    raise ValueError(f"Function '{node.function}' not found in registry")
                
                func = self.registry[node.function]
                
                # Execute the function
                result = await func(state) if hasattr(func, '__await__') else func(state)
                
                # Update state with result if it's a dictionary
                if isinstance(result, dict):
                    state.update_state(**result)
                
                state.status = NodeStatus.COMPLETED
                state.add_log(f"Node '{node.node_id}' completed successfully")
                
                # Determine next node
                next_node_id = None
                if node.node_type == NodeType.CONDITION:
                    # For condition nodes, use the result to determine next node
                    condition_result = str(bool(result)).lower()
                    next_node_id = node.next_nodes.get(condition_result)
                elif node.next_nodes:
                    # For regular nodes, use the 'default' next node or first available
                    next_node_id = node.next_nodes.get('default') or next(iter(node.next_nodes.values()))
                
                current_node_id = next_node_id
                
            except Exception as e:
                state.status = NodeStatus.FAILED
                state.add_log(f"Error in node '{node.node_id}': {str(e)}", "ERROR")
                raise
                
        state.current_node = None
        return state

# Global workflow engine instance
workflow_engine = WorkflowEngine()
