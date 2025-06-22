# FastAPI CFG Server Documentation

**Created:** 2025-06-22  
**Author:** AI Assistant  
**Status:** Completed  

## Overview

A FastAPI server that provides RESTful endpoints for parsing source code and returning Control Flow Graphs (CFGs) in JSON format. This server serves as the backend for the Tree Sprawler visualization tool.

## API Endpoints

### Root Endpoint

**GET /** - API information and health check

```bash
curl http://localhost:8001/
```

**Response:**
```json
{
  "message": "Tree Sprawler CFG API",
  "version": "1.0.0",
  "supported_languages": ["c", "java"],
  "endpoints": {
    "/parse": "POST - Parse source code and return CFG in JSON format",
    "/health": "GET - Health check endpoint"
  }
}
```

### Health Check

**GET /health** - Service health status

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Parse Source Code

**POST /parse** - Parse source code and return CFG in JSON format

**Request Body:**
```json
{
  "source_code": "int foo() { return 42; }",
  "language": "c"
}
```

**Response:**
```json
{
  "success": true,
  "cfg": {
    "function_name": "foo",
    "entry_node_ids": [0],
    "exit_node_ids": [1],
    "nodes": {
      "0": {
        "id": 0,
        "node_type": "ENTRY",
        "source_text": "foo",
        "successors": [2],
        "predecessors": [],
        "edge_labels": {},
        "metadata": {
          "function_calls": [],
          "variable_definitions": [],
          "variable_uses": []
        }
      },
      "1": {
        "id": 1,
        "node_type": "EXIT",
        "source_text": "foo",
        "successors": [],
        "predecessors": [2],
        "edge_labels": {},
        "metadata": {
          "function_calls": [],
          "variable_definitions": [],
          "variable_uses": []
        }
      },
      "2": {
        "id": 2,
        "node_type": "RETURN",
        "source_text": "return 42;",
        "successors": [1],
        "predecessors": [0],
        "edge_labels": {},
        "metadata": {
          "function_calls": [],
          "variable_definitions": [],
          "variable_uses": []
        }
      }
    }
  },
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "cfg": null,
  "error": "Error message describing what went wrong"
}
```

## Supported Languages

- **C** (`"c"`) - Full support for C language constructs
- **Java** (`"java"`) - Full support for Java language constructs

## CFG Node Types

The following node types are supported in the CFG representation:

- `ENTRY` - Function entry point
- `EXIT` - Function exit point
- `STATEMENT` - Regular statement
- `CONDITION` - Conditional expression
- `LOOP_HEADER` - Loop header/condition
- `BREAK` - Break statement
- `CONTINUE` - Continue statement
- `RETURN` - Return statement
- `SWITCH_HEAD` - Switch statement header
- `CASE` - Case label
- `DEFAULT` - Default case label
- `LABEL` - Labeled statement
- `GOTO` - Goto statement

## Usage Examples

### Example 1: Simple Function

```bash
curl -X POST "http://localhost:8001/parse" \
     -H "Content-Type: application/json" \
     -d '{
       "source_code": "int add(int a, int b) { return a + b; }",
       "language": "c"
     }'
```

### Example 2: Function with Control Flow

```bash
curl -X POST "http://localhost:8001/parse" \
     -H "Content-Type: application/json" \
     -d '{
       "source_code": "int max(int a, int b) { if (a > b) return a; else return b; }",
       "language": "c"
     }'
```

### Example 3: Using Python requests

```python
import requests

code = """
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}
"""

response = requests.post(
    "http://localhost:8001/parse",
    json={
        "source_code": code,
        "language": "c"
    }
)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        cfg = result["cfg"]
        print(f"Function: {cfg['function_name']}")
        print(f"Nodes: {len(cfg['nodes'])}")
    else:
        print(f"Error: {result['error']}")
```

## Running the Server

### Development Mode

```bash
cd /path/to/tree-sprawler
python -m uvicorn src.tree_sprawler.viz.app:app --reload --host 0.0.0.0 --port 8001
```

### Production Mode

```bash
cd /path/to/tree-sprawler
python -m uvicorn src.tree_sprawler.viz.app:app --host 0.0.0.0 --port 8001
```

### Using the Python script

```bash
cd /path/to/tree-sprawler
python src/tree_sprawler/viz/app.py
```

## Dependencies

The server requires the following Python packages:

- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `tree-sitter<0.21.0` - Parse tree generation
- `tree-sitter-languages>=1.10.2` - Language support

## Error Handling

The server handles the following error scenarios:

1. **Unsupported Language**: Returns HTTP 400 with error message
2. **Parsing Errors**: Returns HTTP 200 with `success: false` and error message
3. **Invalid Request**: Returns HTTP 422 for malformed JSON
4. **Server Errors**: Returns HTTP 500 for internal server errors

## Integration with Frontend

The server is designed to work with the React frontend located in `src/tree_sprawler/viz/frontend/`. The frontend uses the `/parse` endpoint to:

1. Send source code from the Monaco editor
2. Receive CFG data in JSON format
3. Render the CFG using Cytoscape.js
4. Update the visualization in real-time as code changes

## Configuration

The server runs on `localhost:8001` by default. This can be changed by modifying the `DEFAULT_PORT` and `DEFAULT_HOST` constants in `src/tree_sprawler/viz/app.py`.

## Security Considerations

- The server accepts source code input and executes parsing operations
- Input validation is performed via Pydantic models
- No user authentication is currently implemented (development server)
- CORS is not explicitly configured (may need adjustment for production)

## Testing

A test script is provided at `test_api.py` to verify the server functionality:

```bash
python test_api.py
```

This script tests both the root endpoint and the parse endpoint with sample C code.

## Troubleshooting

### Common Issues

1. **Tree-sitter library errors**: Ensure tree-sitter-languages is properly installed
2. **Port conflicts**: Change the port if 8001 is already in use
3. **Module import errors**: Ensure the package is installed in development mode

### Debug Mode

To enable debug logging, set the logging level to DEBUG in the application:

```python
logging.basicConfig(level=logging.DEBUG)
```

## API Versioning

Current API version is `1.0.0`. Future versions will maintain backward compatibility where possible.
