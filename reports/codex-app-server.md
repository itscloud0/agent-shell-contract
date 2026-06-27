# agent-shell-contract report

- Adapter: `codex-app-server`
- Started: `2026-06-27T09:59:08Z`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Python: `3.9.6`
- Duration: `2.4555s`

## Summary

- `PASS`: 8
- `SKIP`: 1

## Fixture Results

### timeout-child-pipe - PASS

timeout returned without hanging on child pipes

Details:
- result: exit=124 timed_out=True duration=0.514s

### timeout-process-tree - PASS

timeout terminated the owned process tree

Details:
- result: exit=124 timed_out=True duration=0.506s
- child_pid: 21685

### background-server-lifecycle - PASS

background start/check/stop closed the owned port

Details:
- handle: BackgroundHandle(id='asc-40e36094c9f54f7cb28f52832a0852ac', pid=None, command='/Applications/Xcode.app/Contents/Developer/usr/bin/python3 -c \'import http.server\nimport socketserver\nsocketserver.TCPServer.allow_reuse_address = True\nwith socketserver.TCPServer(("127.0.0.1", 55968), http.server.SimpleHTTPRequestHandler) as server:\n    print("ASC_SERVER_READY 55968", flush=True)\n    server.serve_forever()\'', raw='')
- bg_status: BackgroundStatus(running=True, stdout='ASC_SERVER_READY 55968\n', stderr='', exit_code=None, raw='')
- stop: exit=-1 timed_out=False duration=0.013s
- port: 55968

### output-before-exit - PASS

stdout, stderr, and exit status survived

Details:
- result: exit=7 timed_out=False duration=0.025s

### output-after-kill - PASS

bounded pre-kill output remained available

Details:
- result: exit=124 timed_out=True duration=1.008s

### cwd-isolation - PASS

cwd stayed isolated across commands

Details:
- before: exit=0 timed_out=False duration=0.024s
- cd_result: exit=0 timed_out=False duration=0.013s
- after: exit=0 timed_out=False duration=0.025s

### env-boundary - PASS

explicit env boundary excluded host sentinel

Details:
- result: exit=0 timed_out=False duration=0.038s

### pty-detection - PASS

observed PTY behavior matched adapter declaration

Details:
- result: exit=0 timed_out=False duration=0.023s

### windows-tree-termination - SKIP

Windows-only fixture skipped on this host
