"""Zernio MCP Server."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mcp-zernio")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
