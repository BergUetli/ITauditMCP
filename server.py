"""
IT Audit MCP Server
===================
The main entry point. This is what you run.

This file:
1. Creates the FastMCP server
2. Registers all audit tools from tools/
3. Starts the server (stdio for local, HTTP for remote)

To run locally with Claude Desktop:
    python server.py

To run as a remote HTTP server:
    MCP_TRANSPORT=streamable-http python server.py

The server exposes tools that AI agents call. Each tool is a thin
wrapper around the audit pipeline — the real logic is in audit/pipeline.py.
"""

from fastmcp import FastMCP
from config.settings import settings

# Create the MCP server
mcp = FastMCP(
    name="IT Audit MCP Server",
    instructions="""This MCP server provides IT audit capabilities grounded in
    real frameworks (COBIT 2019, ISO 27001:2022, NIST CSF 2.0, FFIEC, SOC 2).

    It can:
    - Parse business processes into structured steps
    - Identify risks with framework references
    - Determine expected controls for identified risks
    - Assess control design effectiveness
    - Evaluate evidence for operating effectiveness
    - Generate complete audit findings
    - Map controls across frameworks

    All outputs are validated against the knowledge base — control IDs
    are verified, findings follow the 5-component structure, and confidence
    scores indicate how well-grounded each response is.

    For best results, provide:
    - The framework to ground against (e.g., "cobit_2019")
    - The industry context (e.g., "banking")
    - Detailed process descriptions or control descriptions
    """,
)

# Import and register all tools
# (tools/ module handles the registration via @mcp.tool decorators)
from tools.audit_tools import register_tools
register_tools(mcp)


if __name__ == "__main__":
    # Start the server based on configured transport
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        # Default: stdio (for Claude Desktop and local use)
        mcp.run(transport="stdio")
