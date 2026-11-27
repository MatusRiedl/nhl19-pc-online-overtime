"""Overtime as an MCP server: `OvertimeNHL19.exe --mcp [--game-dir DIR] [--save-dir DIR]` (or `python -m
overtime_roster.mcp`). An AI client (Claude Desktop, Claude Code, any MCP client) starts it and talks to it over stdin
and stdout; the tools are in tools.py, the protocol in protocol.py, the facts in docs/notes/mcp.md."""
import argparse
import json
import os
import sys

NAME = 'overtime-nhl19'
TITLE = 'Overtime NHL 19'


def command(frozen=None, executable=None, env=None):
    """[program, args...] an AI client runs to start this server on this PC."""
    env = os.environ if env is None else env
    frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
    executable = executable or sys.executable
    if env.get('APPIMAGE'):                 # the Linux AppImage: its own path, not the mounted copy's
        return [env['APPIMAGE'], '--mcp']
    if frozen:
        return [executable, '--mcp']
    return [executable, '-m', 'overtime_roster.mcp']


def config(frozen=None, executable=None, env=None):
    """The client settings for this PC: Claude Desktop's mcpServers entry and Claude Code's command line."""
    env = os.environ if env is None else env
    frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
    cmd = command(frozen, executable, env)
    entry = {'command': cmd[0], 'args': cmd[1:]}
    extra = ''
    if not frozen and not env.get('APPIMAGE'):      # from the source: Python finds the package through PYTHONPATH
        top = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        entry['env'] = {'PYTHONPATH': top}
        extra = f'--env "PYTHONPATH={top}" ' if ' ' in top else f'--env PYTHONPATH={top} '
    desktop = json.dumps({'mcpServers': {'overtime': entry}}, indent=2)
    code = f'claude mcp add --transport stdio {extra}overtime -- ' + ' '.join(f'"{x}"' if ' ' in x else x for x in cmd)
    return {'desktop': desktop, 'code': code, 'command': cmd}


def main(argv=None):
    """Serve until the client closes stdin. Returns the exit code."""
    argv = sys.argv[1:] if argv is None else list(argv)
    inp = getattr(sys.stdin, 'buffer', None)
    out = getattr(sys.stdout, 'buffer', None)
    if inp is None or out is None:          # started by a double click: no client on the other end
        return 2
    sys.stdout = sys.stderr                 # stdout carries messages only: every print goes to the log
    p = argparse.ArgumentParser(prog='OvertimeNHL19 --mcp', add_help=False)
    p.add_argument('--mcp', action='store_true')
    p.add_argument('--game-dir')
    p.add_argument('--save-dir')
    a, _rest = p.parse_known_args(argv)
    from .. import VERSION
    from .protocol import Server
    from .tools import INSTRUCTIONS, OvertimeTools

    def log(text):
        try:
            print(text, file=sys.stderr, flush=True)
        except (OSError, ValueError):       # no stderr to write to
            pass
    log(f'{TITLE} MCP server {VERSION}: waiting for a client on stdin.')
    tools = OvertimeTools(a.game_dir, a.save_dir, log)
    return Server(NAME, TITLE, VERSION, tools.tools(), INSTRUCTIONS, log).run(inp, out)
