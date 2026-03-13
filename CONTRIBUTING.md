# Contributing

Thank you for considering a contribution to azure-mcp-agent-starter.

## Before you start

- Read [.github/copilot-instructions.md](.github/copilot-instructions.md) — it is the single source of truth for conventions in this repo.
- Check open issues before opening a new one.
- For significant changes, open an issue first to discuss the approach.

## Development setup

```bash
git clone https://github.com/RajAnandakumar-msft/azure-mcp-agent-starter.git
cd azure-mcp-agent-starter/agent_app
pip install -r requirements.txt
```

## Code standards

| Area | Standard |
|---|---|
| Language | Python 3.10+ |
| Type hints | Required on all functions and methods |
| Formatting | Ruff — run `ruff format .` before committing |
| Linting | Ruff — run `ruff check .` and fix all warnings |
| Line length | 88 characters |
| Quotes | Double quotes |
| Naming | `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants |

## Testing

Run all tests before submitting a PR:

```bash
pytest agent_app/tests/ -v
pytest tests/ -v
```

Coverage must not regress. Minimum coverage is 40% for this starter kit.

## Adding a new MCP server

The preferred path requires no Python changes:

1. Add an entry to `mcp_servers.yaml`.
2. If the server returns a non-standard response shape, register an adapter in `agent_app/normalization/normalizer.py`.
3. Add a tool function in `agent_app/tools.py`.
4. Add tests in `agent_app/tests/`.

See `examples/README.md` for full guidance.

## Pull request checklist

- [ ] `ruff format .` and `ruff check .` pass with no errors
- [ ] All existing tests pass (`pytest agent_app/tests/ -v`)
- [ ] New code has tests; coverage has not regressed
- [ ] No secrets committed (check `.env` is in `.gitignore`)
- [ ] PR description explains *what* and *why*

## Security

- Never hardcode secrets — env vars only.
- Validate all user inputs before passing them to LLMs.
- Validate URL inputs to prevent SSRF.
- Do not use `shell=True` in subprocess calls.

If you discover a security vulnerability, please report it privately rather than opening a public issue.
