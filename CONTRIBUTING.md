# Contributing

Thanks for your interest in contributing to the Gainsight Customer Communities MCP Server! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git

### Setup

```bash
git clone https://github.com/graemerycyk/gainsight-community-mcp.git
cd gainsight-community-mcp
pip install -e ".[dev]"
```

This installs the project in editable mode with test dependencies (`pytest`, `pytest-asyncio`, `respx`).

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Specific test file
pytest tests/test_client.py
```

All tests use mocked HTTP responses — no API credentials are needed to run them.

## Making Changes

### Branch Naming

- `feature/short-description` — new tools, capabilities, or integrations
- `fix/short-description` — bug fixes
- `docs/short-description` — documentation updates

### Code Style

- Use type annotations for all function signatures
- Follow existing patterns in `client.py` and `server.py`
- Keep tool docstrings descriptive — they are exposed to AI agents as tool descriptions

### Adding a New MCP Tool

1. **Add an API method** in `src/client.py`:
   ```python
   async def get_user(self, user_id: int) -> Any:
       """Get a user by ID.  GET /v2/users/{id}"""
       return await self._request("GET", f"/v2/users/{user_id}")
   ```

2. **Add a tool function** in `src/server.py`:
   ```python
   @mcp.tool()
   async def get_user(user_id: int) -> str:
       """Retrieve a community member's profile.

       Args:
           user_id: The numeric ID of the user.
       """
       client = _get_client()
       result = await client.get_user(user_id)
       return json.dumps(result, indent=2)
   ```

3. **Add tests** in both test files:
   - `tests/test_client.py` — mock the HTTP request with `respx`
   - `tests/test_server.py` — mock the client with `AsyncMock`

4. **Update documentation**:
   - Add the tool to the Available Tools section in `README.md`
   - Update `AGENTS.md` with usage guidance
   - Update `CLAUDE.md` if there are new patterns or gotchas

### Testing Guidelines

- Every new API method needs a test in `test_client.py` with mocked HTTP via `respx`
- Every new tool function needs a test in `test_server.py` with a mocked client
- Tests should verify both the happy path and parameter transformation
- Use `_mock_token()` helper in client tests to mock the OAuth2 flow

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. Make your changes
3. Ensure all tests pass (`pytest`)
4. Update documentation as needed
5. Submit a pull request with a clear description of the changes

### PR Description Template

```
## What

Brief description of the change.

## Why

Motivation or issue being addressed.

## Testing

How the change was tested.
```

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include your Python version, OS, and any relevant error output
- For API-related issues, include the region you're using (EU/US)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
