# tree-climber

Tree Climber is a comprehensive static analysis framework for generating Control Flow Graphs (CFGs) and performing dataflow analysis on source code. It supports multiple programming languages through Tree-sitter parsers and provides both programmatic APIs and interactive web visualization.

## Features

- **Control Flow Graph Generation**: Build CFGs from source code for C and Java
- **Dataflow Analysis**: Perform def-use chain analysis and reaching definitions
- **Web Visualization**: Interactive CFG visualization with React frontend
- **FastAPI Backend**: RESTful API for CFG generation and analysis
- **Extensible Architecture**: Visitor pattern design for easy language extension

## Supported Languages

- **C**: Full CFG generation with control structures, loops, and functions
- **Java**: CFG generation for Java language constructs
- **Extensible**: Framework designed to easily add new language support

## Architecture

### Core Components

- **CFG Builder**: Generates control flow graphs using visitor pattern
- **Dataflow Solver**: Implements iterative dataflow analysis algorithms
- **AST Utils**: Tree-sitter integration and AST manipulation utilities
- **Visualization**: Web-based interactive CFG visualization

### Analysis Capabilities

- **Control Flow Analysis**: Statement-level CFG construction
- **Def-Use Chains**: Variable definition and usage tracking
- **Reaching Definitions**: Forward dataflow propagation
- **Extensible Framework**: Support for custom dataflow analyses

## Installation

This project uses `uv` for Python dependency management and `bun` for frontend dependencies.

### Prerequisites

- Python 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- [bun](https://bun.sh/) for frontend dependencies

### Setup

1. Clone the repository:
```bash
git clone https://github.com/bstee615/tree-climber
cd tree-climber
```

2. Install Python dependencies:
```bash
uv sync
```

3. (For web frontend) Install frontend dependencies:
```bash
cd src/tree_climber/viz/frontend
bun install
```

4. (For CLI) Install CLI dependencies:
```bash
source .venv/bin/activate
uv pip install -e .
sudo apt install -y graphviz graphviz-dev
```

## Usage

### CLI

Run the CLI against a file or directory. Use the flags below to pick which graphs to generate and how to render them.
Try `uv run -m tree_climber.cli --help` to see examples and help.
If installed as a command, replace `uv run -m tree_climber.cli` with `tree-climber`.

### Command Line Testing

Run CFG generation tests:
```bash
# Test C language CFG generation
uv run src/tree_climber/cfg/test_c.py

# Test Java language CFG generation  
uv run src/tree_climber/cfg/test_java.py
```

### Web Application

The project includes a full-stack web application with FastAPI backend and React frontend.

#### Start the Backend Server

```bash
# Run FastAPI server with hot reload
uv run -m uvicorn tree_climber.viz.app:app --reload --host 0.0.0.0 --port 8000

# Or use the VS Code task: "Run FastAPI Server"
```

#### Start the Frontend

```bash
# Navigate to frontend directory
cd src/tree_climber/viz/frontend

# Start development server
bun dev

# Or use the VS Code task: "Run Frontend"
```

#### Access the Application Locally

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

#### API Endpoints

The FastAPI backend provides the following endpoints:

- `POST /parse` - Parse source code and return CFG in JSON format
- `POST /analyze/def-use` - Perform def-use chain analysis
- `POST /analyze/reaching-definitions` - Perform reaching definitions analysis
- `GET /health` - Health check endpoint

## Limitations

Currently, only basic program constructs are supported. I am working to make the parsing more robust and complete.

See the full list of features handled and planned in the [Limitations section of this doc](./docs/extending-languages.md).

## Development

### Adding New Languages

1. Create a new visitor class in `src/tree_climber/cfg/languages/`
2. Implement language-specific CFG construction logic
3. Register the language in the CFG builder
4. Add test cases in the `test/` directory

### Adding New Analyses

1. Create a new analysis class in `src/tree_climber/dataflow/analyses/`
2. Implement the dataflow problem interface
3. Add API endpoints in `src/tree_climber/viz/app.py`
4. Update frontend to display analysis results

### Frontend Development

The frontend is built with:
- **React**: UI framework
- **Cytoscape.js**: Graph visualization
- **Monaco Editor**: Code editing
- **Vite**: Build tool and dev server

### Backend Development

The backend uses:
- **FastAPI**: Web framework
- **Tree-sitter**: Source code parsing
- **Pydantic**: Data validation

### CLI Development

The CLI uses:
- **Typer**: Terminal display and argument parsing
- **GraphViz**: Graph visualization

## Documentation

For detailed technical documentation, see the `docs/` directory:
