# agent-shell-contract report

- Adapter: `pydantic-ai-harness`
- Started: `2026-06-27T09:59:25Z`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Python: `3.12.11`
- Duration: `2.4639s`

## Summary

- `PASS`: 7
- `FAIL`: 1
- `SKIP`: 1

## Fixture Results

### timeout-child-pipe - PASS

timeout returned without hanging on child pipes

Details:
- result: exit=None timed_out=True duration=0.520s

### timeout-process-tree - PASS

timeout terminated the owned process tree

Details:
- result: exit=None timed_out=True duration=0.518s
- child_pid: 23857

### background-server-lifecycle - PASS

background start/check/stop closed the owned port

Details:
- handle: BackgroundHandle(id='5c9a4cb6132f', pid=None, command='/Users/iliasorokin/.cache/uv/builds-v0/.tmpT9tGkd/bin/python -c \'import http.server\nimport socketserver\nsocketserver.TCPServer.allow_reuse_address = True\nwith socketserver.TCPServer(("127.0.0.1", 56000), http.server.SimpleHTTPRequestHandler) as server:\n    print("ASC_SERVER_READY 56000", flush=True)\n    server.serve_forever()\'', raw='Started background command: \'/Users/iliasorokin/.cache/uv/builds-v0/.tmpT9tGkd/bin/python -c \\\'import http.server\\nimport socketserver\\nsocketserver.TCPServer.allow_reuse_address = True\\nwith socketserver.TCPServer(("127.0.0.1", 56000), http.server.SimpleHTTPRequestHandler) as server:\\n    print("ASC_SERVER_READY 56000", flush=True)\\n    server.serve_forever()\\\'\'\nID: 5c9a4cb6132f')
- bg_status: BackgroundStatus(running=True, stdout='ASC_SERVER_READY 56000', stderr='', exit_code=None, raw='[status: running]\n[stdout]\nASC_SERVER_READY 56000\n')
- stop: exit=-15 timed_out=False duration=0.001s
- port: 56000

### output-before-exit - PASS

stdout, stderr, and exit status survived

Details:
- result: exit=7 timed_out=False duration=0.022s

### output-after-kill - FAIL

bounded pre-kill output was lost

Details:
- result: exit=None timed_out=True duration=1.008s

### cwd-isolation - PASS

adapter declares sticky cwd support; command behavior recorded

Details:
- before: exit=0 timed_out=False duration=0.040s
- cd_result: exit=0 timed_out=False duration=0.006s
- after: exit=0 timed_out=False duration=0.021s

### env-boundary - PASS

explicit env boundary excluded host sentinel

Details:
- result: exit=0 timed_out=False duration=0.040s

### pty-detection - PASS

observed PTY behavior matched adapter declaration

Details:
- result: exit=0 timed_out=False duration=0.024s

### windows-tree-termination - SKIP

Windows-only fixture skipped on this host
