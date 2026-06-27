# Security and Safety

`agent-shell-contract` runs local shell commands by design. It is a conformance suite for shell-runner semantics, not a sandbox or security boundary.

## Fixture Safety Model

- Fixtures create temporary directories through the Python standard library.
- Fixtures start only owned child processes.
- Fixtures bind only loopback ports selected by the OS.
- Cleanup targets only handles or process groups created by the active fixture run.
- No fixture reads `.env`, private keys, tokens, browser profiles, or unrelated project files.
- No fixture uses broad process-name killing such as `pkill node` or `killall`.

## Known Limits

- POSIX process-group cleanup is tested locally. Windows process-tree cleanup is represented by a fixture but requires Windows CI or manual validation before claiming support.
- Adapters can expose real bugs in shell runners, including leaked children or open ports. Run in a disposable working directory when testing an unknown adapter.
- Reports can include command output. Review reports before attaching them to public issues.

## Reporting Issues

When filing a security issue, include the adapter name, fixture name, operating system, Python version, and whether any owned process or port was left alive.

