"""FastAPI server for parsing source code and returning Control Flow Graphs in JSON format.

This server provides endpoints to parse source code from various programming languages
and return their Control Flow Graph (CFG) representation in JSON format.
"""

import logging
from dataclasses import asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tree_sprawler.ast_utils import ast_node_to_dict
from tree_sprawler.cfg.builder import CFGBuilder

# Constants for supported languages
SUPPORTED_LANGUAGES = ["c", "java"]
DEFAULT_LANGUAGE = "c"

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:3000",  # React default dev server
    "http://localhost:5173",  # Vite default dev server
    "http://localhost:5174",  # Vite fallback port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tree Sprawler CFG API",
    description="Parse source code and return Control Flow Graphs in JSON format",
    version="0.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SupportedLanguage(str, Enum):
    """Enumeration of supported programming languages"""

    C = "c"
    JAVA = "java"


class ParseRequest(BaseModel):
    """Request model for parsing source code"""

    source_code: str = Field(..., description="The source code to parse")
    language: SupportedLanguage = Field(
        default=SupportedLanguage.C,
        description="The programming language of the source code",
    )


class ParseResponse(BaseModel):
    """Response model for parsed CFG and AST"""

    success: bool = Field(description="Whether the parsing was successful")
    cfg: Optional[Dict[str, Any]] = Field(
        default=None, description="The Control Flow Graph in JSON format"
    )
    ast: Optional[Dict[str, Any]] = Field(
        default=None, description="The Abstract Syntax Tree in JSON format"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if parsing failed"
    )


@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Tree Sprawler CFG API",
        "version": "1.0.0",
        "supported_languages": SUPPORTED_LANGUAGES,
        "endpoints": {
            "/parse": "POST - Parse source code and return CFG and AST in JSON format",
            "/health": "GET - Health check endpoint",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/parse", response_model=ParseResponse)
async def parse_source_code(request: ParseRequest) -> ParseResponse:
    """Parse source code and return a CFG and AST in JSON format.

    Args:
        request: ParseRequest containing source code and language

    Returns:
        ParseResponse containing the CFG and AST in JSON format or error message
    """
    try:
        logger.info(
            f"Parsing {len(request.source_code)} bytes of {request.language} code"
        )

        # Validate language support
        if request.language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.language}. "
                f"Supported languages: {SUPPORTED_LANGUAGES}",
            )

        # Create and setup CFG builder
        builder = CFGBuilder(request.language.value)
        builder.setup_parser()
        if not builder.parser:
            raise HTTPException(
                status_code=500,
                detail=f"Parser for {request.language} not set up correctly.",
            )

        # Parse source code to get AST
        tree = builder.parser.parse(bytes(request.source_code, "utf8"))
        if not tree:
            raise HTTPException(status_code=400, detail="Failed to parse source code.")

        # Convert AST to dictionary for JSON serialization
        ast_dict = asdict(ast_node_to_dict(tree.root_node))

        # Build CFG from AST
        cfg = builder.build_cfg(tree=tree)

        logger.info(
            f"CFG built successfully: function={cfg.function_name}, "
            f"nodes={len(cfg.nodes)}"
        )

        # Convert CFG to JSON-serializable dictionary
        cfg_dict = cfg.to_dict()

        return ParseResponse(success=True, cfg=cfg_dict, ast=ast_dict)

    except Exception as e:
        logger.error(f"Error parsing source code: {str(e)}")
        return ParseResponse(success=False, error=str(e))


if __name__ == "__main__":
    import uvicorn

    # Default port for the server
    DEFAULT_PORT = 8001
    DEFAULT_HOST = "0.0.0.0"

    logger.info(
        f"Starting Tree Sprawler CFG API server on {DEFAULT_HOST}:{DEFAULT_PORT}"
    )
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
