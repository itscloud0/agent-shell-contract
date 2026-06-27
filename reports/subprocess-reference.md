# agent-shell-contract report

- Adapter: `subprocess-reference`
- Started: `2026-06-27T09:55:33Z`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Python: `3.9.6`
- Duration: `2.443s`

## Summary

- `PASS`: 8
- `SKIP`: 1

## Fixture Results

### timeout-child-pipe - PASS

timeout returned without hanging on child pipes

Details:
- result: exit=-15 timed_out=True duration=0.504s

### timeout-process-tree - PASS

timeout terminated the owned process tree

Details:
- result: exit=-15 timed_out=True duration=0.504s
- child_pid: 93026

### background-server-lifecycle - PASS

background start/check/stop closed the owned port

Details:
- handle: BackgroundHandle(id='bg-1', pid=93162, command='/Applications/Xcode.app/Contents/Developer/usr/bin/python3 -c \'import http.server\nimport socketserver\nsocketserver.TCPServer.allow_reuse_address = True\nwith socketserver.TCPServer(("127.0.0.1", 55581), http.server.SimpleHTTPRequestHandler) as server:\n    print("ASC_SERVER_READY 55581", flush=True)\n    server.serve_forever()\'', raw='')
- bg_status: BackgroundStatus(running=True, stdout='ASC_SERVER_READY 55581\n', stderr='', exit_code=None, raw='')
- stop: exit=-15 timed_out=False duration=0.004s
- port: 55581

### output-before-exit - PASS

stdout, stderr, and exit status survived

Details:
- result: exit=7 timed_out=False duration=0.017s

### output-after-kill - PASS

bounded pre-kill output remained available

Details:
- result: exit=-15 timed_out=True duration=1.004s

### cwd-isolation - PASS

cwd stayed isolated across commands

Details:
- before: exit=0 timed_out=False duration=0.017s
- cd_result: exit=0 timed_out=False duration=0.004s
- after: exit=0 timed_out=False duration=0.016s

### env-boundary - PASS

explicit env boundary excluded host sentinel

Details:
- result: exit=0 timed_out=False duration=0.046s

### pty-detection - PASS

observed PTY behavior matched adapter declaration

Details:
- result: exit=0 timed_out=False duration=0.018s

### windows-tree-termination - SKIP

Windows-only fixture skipped on this host
