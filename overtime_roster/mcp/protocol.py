"""The MCP server's protocol: JSON-RPC 2.0 over newline-delimited UTF-8 (the stdio transport, MCP 2025-11-25 and the
revisions before it; docs/notes/mcp.md). No SDK: the server answers initialize, ping, tools/list and tools/call, and
nothing else. Every line it writes is one JSON-RPC message; anything else goes to stderr."""
import json
import sys
import traceback

VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05')     # the newest first
PARSE, INVALID, NO_METHOD, BAD_PARAMS, INTERNAL = -32700, -32600, -32601, -32602, -32603


class ToolError(Exception):
    """A tool that could not do what was asked: the sentence goes back as the tool's result with isError (refused
    values, no roster open), not as a JSON-RPC error."""


class Tool:
    def __init__(self, name, title, description, schema, fn, read_only=False, destructive=False):
        self.name, self.title, self.description, self.schema, self.fn = name, title, description, schema, fn
        self.read_only, self.destructive = read_only, destructive

    def listed(self):
        return {'name': self.name, 'title': self.title, 'description': self.description, 'inputSchema': self.schema,
                'annotations': {'title': self.title, 'readOnlyHint': self.read_only,
                                'destructiveHint': self.destructive, 'idempotentHint': self.read_only,
                                'openWorldHint': False}}


def text_result(data, error=False):
    """A tools/call result: the data as JSON text (and as structuredContent when it is an object)."""
    if isinstance(data, str):
        out = {'content': [{'type': 'text', 'text': data}]}
    else:
        out = {'content': [{'type': 'text', 'text': json.dumps(data, ensure_ascii=False, indent=1)}]}
        if isinstance(data, dict):
            out['structuredContent'] = data
    if error:
        out['isError'] = True
    return out


class Server:
    def __init__(self, name, title, version, tools, instructions='', log=None):
        self.info = {'name': name, 'title': title, 'version': version}
        self.tools = {t.name: t for t in tools}
        self.order = [t.name for t in tools]
        self.instructions = instructions
        self.log = log or (lambda text: print(text, file=sys.stderr, flush=True))

    # --- one message ---------------------------------------------------------------------------------------------
    def handle(self, msg):
        """The reply to one decoded message, or None (a notification, or a reply from the client)."""
        if not isinstance(msg, dict) or msg.get('jsonrpc') != '2.0':
            return error(msg.get('id') if isinstance(msg, dict) else None, INVALID, 'Not a JSON-RPC 2.0 message.')
        method = msg.get('method')
        if 'id' not in msg:             # a notification (notifications/initialized, cancelled...): no reply
            return None
        ident = msg['id']
        if not isinstance(method, str):
            return None if ('result' in msg or 'error' in msg) else error(ident, INVALID, 'No method.')
        params = msg.get('params') or {}
        if not isinstance(params, dict):
            return error(ident, BAD_PARAMS, 'params must be an object.')
        if method == 'initialize':
            asked = params.get('protocolVersion')
            result = {'protocolVersion': asked if asked in VERSIONS else VERSIONS[0],
                      'capabilities': {'tools': {'listChanged': False}}, 'serverInfo': dict(self.info)}
            if self.instructions:
                result['instructions'] = self.instructions
            return ok(ident, result)
        if method == 'ping':
            return ok(ident, {})
        if method == 'tools/list':
            return ok(ident, {'tools': [self.tools[n].listed() for n in self.order]})
        if method == 'tools/call':
            return self.call(ident, params)
        return error(ident, NO_METHOD, f'Method not found: {method}')

    def call(self, ident, params):
        name, args = params.get('name'), params.get('arguments') or {}
        tool = self.tools.get(name)
        if tool is None:
            return error(ident, BAD_PARAMS, f'Unknown tool: {name}')
        if not isinstance(args, dict):
            return error(ident, BAD_PARAMS, 'arguments must be an object.')
        wrong = check_args(tool.schema, args)
        if wrong:
            return ok(ident, text_result(f'{name}: {wrong}', error=True))
        try:
            return ok(ident, text_result(tool.fn(**args)))
        except ToolError as err:
            return ok(ident, text_result(str(err), error=True))
        except Exception as err:        # noqa: BLE001 (the server keeps answering)
            self.log(traceback.format_exc())
            return ok(ident, text_result(f'Overtime could not do that: {err}', error=True))

    # --- the stdio loop ------------------------------------------------------------------------------------------
    def run(self, inp, out):
        """Read messages from the binary stream `inp` until it ends; write each reply as one line to `out`."""
        for raw in inp:
            line = raw.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode('utf-8'))
            except (UnicodeDecodeError, ValueError):
                reply = error(None, PARSE, 'Not JSON.')
            else:
                reply = error(None, INVALID, 'Batches are not taken.') if isinstance(msg, list) else self.handle(msg)
            if reply is not None:
                out.write(encode(reply))
                out.flush()
        return 0


TYPES = {'string': (str,), 'integer': (int,), 'number': (int, float), 'boolean': (bool,), 'array': (list,),
         'object': (dict,)}


def check_args(schema, args):
    """The first thing wrong with a call's arguments against the tool's top-level schema (names, required ones, the
    JSON type of each), or ''. The tools check the values themselves."""
    props = schema.get('properties') or {}
    extra = sorted(set(args) - set(props))
    if extra:
        return f"it takes no {', '.join(extra)} (it takes {', '.join(props) or 'no arguments'})."
    missing = [k for k in schema.get('required') or () if k not in args]
    if missing:
        return f"{', '.join(missing)} missing."
    for key, value in args.items():
        want = props[key].get('type')
        if value is None or want not in TYPES:
            continue
        if not isinstance(value, TYPES[want]) or (isinstance(value, bool) and want in ('integer', 'number')):
            return f'{key} must be a{"n" if want[0] in "aio" else ""} {want}.'
    return ''


def ok(ident, result):
    return {'jsonrpc': '2.0', 'id': ident, 'result': result}


def error(ident, code, message):
    return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': code, 'message': message}}


def encode(msg):
    """One message as one line of UTF-8 (json escapes every newline inside strings)."""
    return (json.dumps(msg, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
