# Workflow Engine

A simple workflow engine for building agent workflows with FastAPI. This project provides a flexible way to define and execute workflows with different nodes, conditional branching, and state management.

## Features

- Define workflows with nodes and edges
- Support for different node types (task, condition, loop)
- State management with execution logging
- RESTful API for workflow management
- Built-in code review workflow example
- Asynchronous execution

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd workflow_engine
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API documentation: http://localhost:8000/docs
- Alternative documentation: http://localhost:8000/redoc

## Example: Code Review Workflow

This project includes a built-in code review workflow that demonstrates the engine's capabilities. The workflow includes the following steps:

1. Extract functions from the input code
2. Analyze function complexity
3. Detect potential issues
4. Suggest improvements
5. Repeat until quality threshold is met

### Running the Code Review Workflow

1. Start the server if not already running.
2. Send a POST request to run the workflow:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/workflows/run/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "workflow_name": "code_review",
    "initial_state": {
      "code": "def example():\n    # This is a simple function\n    print(\"Hello, world!\")\n    # TODO: Add more functionality\n    return 42"
    }
  }'
```

3. Check the workflow status:

```bash
curl 'http://localhost:8000/api/v1/workflows/state/{run_id}'
```

## API Endpoints

- `POST /api/v1/workflows/` - Create a new workflow
- `POST /api/v1/workflows/run/` - Run a workflow
- `GET /api/v1/workflows/state/{run_id}` - Get workflow execution state
- `GET /api/v1/workflows/` - List all registered workflows
- `GET /api/v1/functions/` - List all registered functions

## Project Structure

```
workflow_engine/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py    # API endpoints
│   │   └── schemas.py      # Pydantic models for API
│   ├── core/
│   │   ├── __init__.py
│   │   └── workflow.py     # Workflow engine implementation
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py        # State management
│   └── main.py             # FastAPI application
├── tests/                  # Test files
├── requirements.txt        # Project dependencies
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
