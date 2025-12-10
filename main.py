from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .api import endpoints, schemas
from .core.workflow import workflow_engine, WorkflowDefinition, Node, NodeType

# Create FastAPI app
app = FastAPI(
    title="Workflow Engine API",
    description="A simple workflow engine for building agent workflows",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(endpoints.router, prefix="/api/v1")

# Register some example functions for the code review workflow
@workflow_engine.register_function
def extract_functions(state):
    """Extract functions from the input code."""
    code = state.data.get("code", "")
    # This is a very simple function extractor - in a real scenario, use ast or similar
    functions = []
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('def '):
            func_name = line.split('def ')[1].split('(')[0].strip()
            functions.append({"name": func_name, "line": i+1})
    
    state.add_log(f"Extracted {len(functions)} functions from code")
    return {"extracted_functions": functions, "function_count": len(functions)}

@workflow_engine.register_function
def check_complexity(state):
    """Check complexity of the code."""
    functions = state.data.get("extracted_functions", [])
    code_lines = state.data.get("code", "").split('\n')
    
    complexity_scores = {}
    for func in functions:
        # Simple complexity check: count lines in function
        start_line = func["line"]
        end_line = len(code_lines)
        
        # Find the end of the function
        indent = len(code_lines[start_line-1]) - len(code_lines[start_line-1].lstrip())
        for i in range(start_line, len(code_lines)):
            line = code_lines[i]
            if line.strip() and len(line) - len(line.lstrip()) <= indent and not line.strip().startswith('#'):
                end_line = i
                break
        
        line_count = end_line - start_line
        complexity_scores[func["name"]] = {
            "line_count": line_count,
            "complexity": "high" if line_count > 20 else "medium" if line_count > 10 else "low"
        }
    
    state.add_log(f"Analyzed complexity for {len(complexity_scores)} functions")
    return {"complexity_analysis": complexity_scores}

@workflow_engine.register_function
def detect_issues(state):
    """Detect potential issues in the code."""
    code = state.data.get("code", "")
    issues = []
    
    # Simple issue detection
    lines = code.split('\n')
    for i, line in enumerate(lines):
        line_num = i + 1
        line = line.strip()
        
        # Check for print statements
        if line.startswith('print('):
            issues.append({
                "line": line_num,
                "type": "debug_code",
                "message": "Print statement detected - consider using proper logging",
                "severity": "low"
            })
        
        # Check for TODO/FIXME comments
        if 'TODO' in line.upper() or 'FIXME' in line.upper():
            issues.append({
                "line": line_num,
                "type": "todo",
                "message": "TODO/FIXME comment found",
                "severity": "info"
            })
    
    state.add_log(f"Detected {len(issues)} potential issues in the code")
    return {"issues": issues, "issue_count": len(issues)}

@workflow_engine.register_function
def suggest_improvements(state):
    """Suggest improvements based on code analysis."""
    suggestions = []
    complexity = state.data.get("complexity_analysis", {})
    issues = state.data.get("issues", [])
    
    # Suggest based on complexity
    for func, data in complexity.items():
        if data["complexity"] == "high":
            suggestions.append({
                "type": "refactor",
                "target": func,
                "suggestion": f"Function '{func}' is complex (lines: {data['line_count']}). Consider breaking it down into smaller functions."
            })
    
    # Suggest based on issues
    for issue in issues:
        if issue["type"] == "debug_code":
            suggestions.append({
                "type": "improvement",
                "target": f"Line {issue['line']}",
                "suggestion": "Replace print() with proper logging"
            })
    
    # Calculate quality score (simple heuristic)
    issue_count = state.data.get("issue_count", 0)
    function_count = state.data.get("function_count", 1)  # Avoid division by zero
    quality_score = max(0, 100 - (issue_count * 2) - (function_count * 5))
    
    state.add_log(f"Generated {len(suggestions)} improvement suggestions")
    return {
        "suggestions": suggestions,
        "quality_score": quality_score,
        "quality_meets_threshold": quality_score >= 70
    }

@workflow_engine.register_function
def end_workflow(state):
    """Mark the end of the workflow."""
    state.add_log("Workflow completed successfully")
    return {"status": "completed", "message": "Workflow execution finished"}

# Register the code review workflow
def register_code_review_workflow():
    """Register the code review workflow."""
    # Create nodes
    nodes = {}
    
    # Extract functions node
    extract_node = Node(
        node_id="extract_functions",
        node_type=NodeType.TASK,
        function="extract_functions",
        next_nodes={"default": "check_complexity"}
    )
    
    # Check complexity node
    complexity_node = Node(
        node_id="check_complexity",
        node_type=NodeType.TASK,
        function="check_complexity",
        next_nodes={"default": "detect_issues"}
    )
    
    # Detect issues node
    issues_node = Node(
        node_id="detect_issues",
        node_type=NodeType.TASK,
        function="detect_issues",
        next_nodes={"default": "suggest_improvements"}
    )
    
    # Suggest improvements node (conditional)
    suggest_node = Node(
        node_id="suggest_improvements",
        node_type=NodeType.CONDITION,
        function="suggest_improvements",
        next_nodes={
            "true": "end_workflow",
            "false": "extract_functions"
        }
    )
    
    # End workflow node
    end_node = Node(
        node_id="end_workflow",
        node_type=NodeType.TASK,
        function="end_workflow",
        next_nodes={}
    )
    
    # Create workflow definition
    workflow_def = WorkflowDefinition(
        name="code_review",
        entry_point="extract_functions",
        nodes={
            "extract_functions": extract_node,
            "check_complexity": complexity_node,
            "detect_issues": issues_node,
            "suggest_improvements": suggest_node,
            "end_workflow": end_node
        }
    )
    
    # Register the workflow
    workflow_engine.register_workflow(workflow_def)
    print(f"Registered workflow: {workflow_def.name}")

# Register the workflow when the app starts
@app.on_event("startup")
async def startup_event():
    register_code_review_workflow()
    print("Code review workflow registered!")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Workflow Engine API",
        "docs": "/docs",
        "version": "0.1.0"
    }
