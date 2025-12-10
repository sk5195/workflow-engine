from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
import uuid
import asyncio
from ..core.workflow import workflow_engine, WorkflowDefinition, Node, NodeType
from . import schemas

router = APIRouter()

# In-memory storage for workflow runs
workflow_runs: Dict[str, Dict[str, Any]] = {}

@router.post("/workflows/", response_model=schemas.WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow: schemas.WorkflowCreate):
    """Register a new workflow definition."""
    try:
        # Convert Pydantic models to internal models
        nodes = {}
        for node_id, node_data in workflow.nodes.items():
            nodes[node_id] = Node(
                node_id=node_data.node_id,
                node_type=NodeType(node_data.node_type),
                function=node_data.function,
                next_nodes=node_data.next_nodes
            )
        
        workflow_def = WorkflowDefinition(
            name=workflow.name,
            entry_point=workflow.entry_point,
            nodes=nodes
        )
        
        workflow_engine.register_workflow(workflow_def)
        
        return {
            "name": workflow_def.name,
            "entry_point": workflow_def.entry_point,
            "nodes": {k: v.dict() for k, v in workflow_def.nodes.items()}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}"
        )

@router.post("/workflows/run/", response_model=schemas.WorkflowRunResponse)
async def run_workflow(run_request: schemas.WorkflowRunRequest):
    """Execute a workflow with the given initial state."""
    run_id = str(uuid.uuid4())
    
    # Store initial run info
    workflow_runs[run_id] = {
        "status": "running",
        "state": None,
        "task": None
    }
    
    async def execute():
        try:
            state = await workflow_engine.execute_workflow(
                workflow_name=run_request.workflow_name,
                initial_state=run_request.initial_state
            )
            workflow_runs[run_id]["state"] = state
            workflow_runs[run_id]["status"] = "completed"
        except Exception as e:
            workflow_runs[run_id]["error"] = str(e)
            workflow_runs[run_id]["status"] = "failed"
    
    # Start the workflow execution in the background
    task = asyncio.create_task(execute())
    workflow_runs[run_id]["task"] = task
    
    return {
        "run_id": run_id,
        "status": "started",
        "state": {
            "data": run_request.initial_state,
            "current_node": None,
            "status": "pending",
            "execution_log": [],
            "metadata": {}
        }
    }

@router.get("/workflows/state/{run_id}", response_model=schemas.WorkflowStateResponse)
async def get_workflow_state(run_id: str):
    """Get the current state of a workflow run."""
    if run_id not in workflow_runs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run with ID {run_id} not found"
        )
    
    run = workflow_runs[run_id]
    
    if run["state"] is None and run["status"] == "running":
        return {
            "data": {},
            "current_node": None,
            "status": "running",
            "execution_log": [{"timestamp": "", "level": "INFO", "message": "Workflow is still running"}],
            "metadata": {}
        }
    
    if "error" in run:
        return {
            "data": run["state"].data if run["state"] else {},
            "current_node": run["state"].current_node if run["state"] else None,
            "status": "error",
            "execution_log": [
                {
                    "timestamp": "",
                    "level": "ERROR",
                    "message": f"Workflow failed: {run['error']}"
                }
            ],
            "metadata": {}
        }
    
    if run["state"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workflow state is not available"
        )
    
    return {
        "data": run["state"].data,
        "current_node": run["state"].current_node,
        "status": run["state"].status.value,
        "execution_log": run["state"].execution_log,
        "metadata": run["state"].metadata
    }

@router.get("/workflows/", response_model=List[str])
async def list_workflows():
    """List all registered workflow names."""
    return list(workflow_engine.workflows.keys())

@router.get("/functions/", response_model=List[str])
async def list_functions():
    """List all registered function names."""
    return list(workflow_engine.registry.keys())
