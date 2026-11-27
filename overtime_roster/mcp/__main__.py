"""python -m overtime_roster.mcp [--game-dir DIR] [--save-dir DIR]: the MCP server over stdio."""
import sys

from . import main

if __name__ == '__main__':
    sys.exit(main())
