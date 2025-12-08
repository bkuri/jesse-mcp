# Jesse MCP Development Guidelines

## Build/Lint/Test Commands

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run single test
pytest tests/test_server.py::test_server

# Lint code
flake8 jesse_mcp/

# Format code
black jesse_mcp/

# Type checking
mypy jesse_mcp/
```

## Code Style Guidelines

### Imports & Formatting
- Use `black` for code formatting
- Import order: stdlib → third-party → local imports
- Use `typing` for all function signatures
- Maximum line length: 88 characters (black default)

### Naming Conventions
- Classes: `PascalCase` (e.g., `JesseMCPServer`)
- Functions/variables: `snake_case` (e.g., `get_jesse_wrapper`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `JESSE_AVAILABLE`)
- Private members: prefix with underscore (`_internal_method`)

### Error Handling
- Use try/except blocks for optional imports
- Log warnings with `logger.warning()` when dependencies unavailable
- Return `None` or empty dict for failed operations
- Use `Optional[T]` typing for nullable returns

### Testing
- Use `pytest-asyncio` for async tests
- Test files: `test_*.py` in tests/ directory
- Mark async tests with `@pytest.mark.asyncio`
- Use descriptive test names and print statements for debugging

## Common Development Workflow

For MCP server development workflow, including automatic synchronization to MetaMCP, see: **../MCP_DEVELOPMENT.md**

This includes:
- Git hook + rsync setup for automatic sync
- MetaMCP integration and container restart
- Troubleshooting and maintenance guidelines
- Complete development cycle instructions