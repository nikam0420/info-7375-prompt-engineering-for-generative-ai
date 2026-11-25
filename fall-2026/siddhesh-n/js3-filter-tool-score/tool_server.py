"""Read-only, stdio JSON-RPC tool server for a narrow MCP subset."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from score import score

VERSION = "2025-11-25"
FIELDS = {"title": 500, "text": 100_000}
TOOL = {
    "name": "score_posting",
    "description": "Score caller-supplied job text for Morgan's review. Matches are mentions, not requirements.",
    "inputSchema": {"type": "object", "required": list(FIELDS),
                    "additionalProperties": False,
                    "properties": {field: {"type": "string", "maxLength": limit}
                                   for field, limit in FIELDS.items()}},
    "annotations": {"readOnlyHint": True, "destructiveHint": False,
                    "idempotentHint": True, "openWorldHint": False},
}

class RpcError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

def result_for(method, params, state):
    if method == "initialize":
        if state["initialized"]:
            raise RpcError(-32600, "Already initialized")
        if not isinstance(params.get("protocolVersion"), str):
            raise RpcError(-32602, "protocolVersion required")
        state["initialized"] = True
        return {"protocolVersion": VERSION, "capabilities": {"tools": {}},
                "serverInfo": {"name": "js3-score", "version": "1.0.0"}}
    if method == "ping":
        return {}
    if method not in {"tools/list", "tools/call"}:
        raise RpcError(-32601, "Method not found")
    if not state["ready"]:
        raise RpcError(-32600, "Finish initialization first")
    if method == "tools/list":
        return {"tools": [TOOL]}
    if params.get("name") != TOOL["name"]:
        raise RpcError(-32602, "Unknown tool")
    args = params.get("arguments")
    if (not isinstance(args, dict) or set(args) != FIELDS.keys()
            or any(not isinstance(args[key], str) or len(args[key]) > limit
                   for key, limit in FIELDS.items())):
        return {"isError": True, "content": [
            {"type": "text", "text": "Expected only title and text strings within schema limits."}
        ]}
    return {"content": [{"type": "text", "text": json.dumps(score(**args))}]}

def handle(line, state):
    response = {"jsonrpc": "2.0", "id": None}
    try:
        request = json.loads(line)
        if (not isinstance(request, dict) or request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)):
            raise RpcError(-32600, "Invalid request")
        method = request["method"]
        if "id" not in request:
            if method == "notifications/initialized" and state["initialized"]:
                state["ready"] = True
            return None
        request_id = request["id"]
        if type(request_id) not in (str, int):
            raise RpcError(-32600, "Invalid request ID")
        response["id"] = request_id
        params = request.get("params", {})
        if not isinstance(params, dict):
            raise RpcError(-32602, "Expected an object for params")
        response["result"] = result_for(method, params, state)
    except json.JSONDecodeError:
        response["error"] = {"code": -32700, "message": "Parse error"}
    except RpcError as error:
        response["error"] = {"code": error.code, "message": error.message}
    return response

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", choices=["demo", "claude"])
    args = parser.parse_args()
    state = {"initialized": False, "ready": False}
    capture = nullcontext()
    if args.record:
        local = Path(__file__).resolve().parent / "local"
        local.mkdir(exist_ok=True)
        capture = (local / f"{args.record}-wire.jsonl").open("a", encoding="utf-8")
    with capture as log:
        def record(direction, line):
            if log:
                from datetime import datetime, timezone
                log.write(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
                                      "direction": direction, "line": line}) + "\n")
                log.flush()

        for line in sys.stdin:
            if len(line) > 1_000_000:
                reply = {"jsonrpc": "2.0", "id": None,
                         "error": {"code": -32600, "message": "Line too large"}}
            else:
                record("client -> server", line)
                reply = handle(line, state)
            if reply is not None:
                output = json.dumps(reply) + "\n"
                record("server -> client", output)
                print(output, end="", flush=True)

if __name__ == "__main__":
    main()
