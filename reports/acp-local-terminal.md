# agent-shell-contract report

- Adapter: `acp-local-terminal`
- Started: `2026-06-27T09:59:09Z`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Python: `3.12.11`
- Duration: `2.3984s`

## Summary

- `PASS`: 8
- `SKIP`: 1

## Fixture Results

### timeout-child-pipe - PASS

timeout returned without hanging on child pipes

Details:
- result: exit=-15 timed_out=True duration=0.506s

### timeout-process-tree - PASS

timeout terminated the owned process tree

Details:
- result: exit=-15 timed_out=True duration=0.505s
- child_pid: 21895

### background-server-lifecycle - PASS

background start/check/stop closed the owned port

Details:
- handle: BackgroundHandle(id='terminal-3', pid=None, command='/Users/iliasorokin/.cache/uv/builds-v0/.tmp7uQVly/bin/python -c \'import http.server\nimport socketserver\nsocketserver.TCPServer.allow_reuse_address = True\nwith socketserver.TCPServer(("127.0.0.1", 55973), http.server.SimpleHTTPRequestHandler) as server:\n    print("ASC_SERVER_READY 55973", flush=True)\n    server.serve_forever()\'', raw='')
- bg_status: BackgroundStatus(running=True, stdout='ASC_SERVER_READY 55973\n', stderr='', exit_code=None, raw='')
- stop: exit=-15 timed_out=False duration=0.002s
- port: 55973

### output-before-exit - PASS

stdout, stderr, and exit status survived

Details:
- result: exit=7 timed_out=False duration=0.019s

### output-after-kill - PASS

bounded pre-kill output remained available

Details:
- result: exit=-15 timed_out=True duration=1.005s

### cwd-isolation - PASS

cwd stayed isolated across commands

Details:
- before: exit=0 timed_out=False duration=0.043s
- cd_result: exit=0 timed_out=False duration=0.004s
- after: exit=0 timed_out=False duration=0.017s

### env-boundary - PASS

explicit env boundary excluded host sentinel

Details:
- result: exit=0 timed_out=False duration=0.021s

### pty-detection - PASS

observed PTY behavior matched adapter declaration

Details:
- result: exit=0 timed_out=False duration=0.018s

### windows-tree-termination - SKIP

Windows-only fixture skipped on this host
