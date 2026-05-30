import sys
import json
import os
import hashlib

# Force sys.stdin and sys.stdout to use UTF-8 to prevent encoding crashes on Windows
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stdin.encoding != 'utf-8':
        sys.stdin.reconfigure(encoding='utf-8')
except Exception as e:
    sys.stderr.write(f"[Log] Failed to reconfigure encoding: {str(e)}\n")
    sys.stderr.flush()

def send_response(response):
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def log_error(msg):
    sys.stderr.write(f"[Log] {msg}\n")
    sys.stderr.flush()

def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def main():
    log_error("Dataset Translation MCP Server started.")
    while True:
        req_id = None
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            # Parse request
            try:
                request = json.loads(line)
            except Exception as pe:
                log_error(f"JSON Parse Error: {str(pe)} | Line: {line[:100]}")
                continue
                
            method = request.get("method")
            req_id = request.get("id")

            # Handle MCP Handshake (Initialize Protocol)
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": request.get("params", {}).get("protocolVersion", "2024-11-05"),
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "dataset-local-manager",
                            "version": "1.0.0"
                        }
                    }
                }
                send_response(response)
                continue

            elif method == "notifications/initialized":
                # Handshake complete
                continue

            # 1. Register tools with Antigravity CLI
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "dataset_get_batch",
                                "description": "Get a batch of untranslated records from input_file by checking output_file. Uses MD5 hash of 'output' (Vietnamese text) as ID.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "input_file": {"type": "string", "description": "Absolute path to source JSONL file"},
                                        "output_file": {"type": "string", "description": "Absolute path to target JSONL file"},
                                        "batch_size": {"type": "integer", "default": 10, "description": "Number of records to fetch"}
                                    },
                                    "required": ["input_file", "output_file"]
                                }
                            },
                            {
                                "name": "dataset_append_translations",
                                "description": "Append newly translated records directly to output_file.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "output_file": {"type": "string", "description": "Absolute path to target JSONL file"},
                                        "translations": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "topic": {"type": "string"},
                                                    "instruction": {"type": "string"},
                                                    "input": {"type": "string", "description": "The English translation"},
                                                    "output": {"type": "string", "description": "The original Vietnamese text"}
                                                },
                                                "required": ["topic", "instruction", "input", "output"]
                                            }
                                        }
                                    },
                                    "required": ["output_file", "translations"]
                                }
                            }
                        ]
                    }
                }
                send_response(response)

            # 2. Handle tool execution requests
            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})

                if name == "dataset_get_batch":
                    input_file = arguments.get("input_file")
                    output_file = arguments.get("output_file")
                    batch_size = arguments.get("batch_size", 10)

                    # Gather MD5 hashes of already translated records
                    processed_hashes = set()
                    if os.path.exists(output_file):
                        with open(output_file, "r", encoding="utf-8") as f:
                            for line_out in f:
                                if line_out.strip():
                                    try:
                                        data = json.loads(line_out)
                                        vi_content = data.get("output", "")
                                        en_content = data.get("input", "")
                                        if vi_content and en_content and en_content != "[TRANSLATION FAILED]":
                                            processed_hashes.add(get_md5(vi_content.strip()))
                                    except:
                                        continue

                    # Read pending records
                    batch = []
                    if os.path.exists(input_file):
                        with open(input_file, "r", encoding="utf-8") as f:
                            for line_in in f:
                                if line_in.strip():
                                    try:
                                        data = json.loads(line_in)
                                        vi_content = data.get("output", "")
                                        if vi_content:
                                            vi_hash = get_md5(vi_content.strip())
                                            if vi_hash not in processed_hashes:
                                                batch.append({
                                                    "topic": data.get("topic", ""),
                                                    "instruction": data.get("instruction", ""),
                                                    "output": vi_content
                                                })
                                                if len(batch) >= batch_size:
                                                    break
                                    except:
                                        continue

                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(batch, ensure_ascii=False)}]
                        }
                    }
                    send_response(response)

                elif name == "dataset_append_translations":
                    output_file = arguments.get("output_file")
                    translations = arguments.get("translations", [])

                    with open(output_file, "a", encoding="utf-8") as f:
                        for item in translations:
                            # Re-order key as requested: topic must be first
                            ordered_item = {
                                "topic": item.get("topic", ""),
                                "instruction": item.get("instruction", ""),
                                "input": item.get("input", ""),
                                "output": item.get("output", "")
                            }
                            f.write(json.dumps(ordered_item, ensure_ascii=False) + "\n")

                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": "Successfully saved translations."}]
                        }
                    }
                    send_response(response)
                else:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method/Tool '{name}' not found"}
                    })
            else:
                # Other methods that are not tools/list or tools/call
                if req_id is not None:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method '{method}' not implemented"}
                    })
        except Exception as e:
            log_error(f"Execution Error: {str(e)}")
            if req_id is not None:
                try:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal Server Error: {str(e)}"
                        }
                    })
                except Exception as se:
                    log_error(f"Failed to send error response: {str(se)}")

if __name__ == "__main__":
    main()
