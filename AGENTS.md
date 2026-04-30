# Jesse MCP Development Guidelines

MCP server exposing Jesse's algorithmic trading framework to LLM agents. 46 tools across 6 phases.

## External References

- **jessegpt.md** - Strategy writing, indicators, Jesse workflow
- **docs/jesse-rest-api.md** - Full REST API payload structures

## Build/Lint/Test

```bash
pip install -e .                # Install editable
pytest                           # Run tests
pytest -v -s tests/test_x.py     # Verbose with print
flake8 jesse_mcp/ && black jesse_mcp/ && mypy jesse_mcp/  # Lint/format/typecheck
python -m jesse_mcp              # Run server (stdio)
python -m jesse_mcp --transport http --port 8000  # Run server (HTTP)
```

## Code Style

- **Formatting**: black (88 chars), double quotes
- **Imports**: stdlib → third-party → local (blank lines between)
- **Types**: Use `typing` module (`Dict[str, Any]`, `Optional[T]`, etc.)
- **Naming**: `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE_CASE` constants
- **Errors**: Return `{"error": str(e), "error_type": type(e).__name__}` from tools
- **Logging**: `logger = logging.getLogger("jesse-mcp.phase3")`, emoji prefixes (✅❌⚠️)

## Jesse REST API Gotchas

These are the common mistakes that cause silent failures:

1. **`warm_up_candles` in `config`** - NOT at root level
2. **`exchanges` requires `balance`** - Missing balance causes errors
3. **ID must be valid UUID** - Use `str(uuid.uuid4())`
4. **Symbol format**: `BTC-USDT` with hyphen
5. **Date format**: `YYYY-MM-DD` string
6. **Strategy name**: Case-sensitive, must match class exactly

See `docs/jesse-rest-api.md` for full payload structures.

## Architecture Patterns

### Lazy Initialization (allows testing without Jesse)
```python
jesse = None
_initialized = False

def _initialize_dependencies():
    global jesse, _initialized
    if _initialized: return
    # ... init logic
    _initialized = True
```

### Singleton with Getter
```python
_optimizer_instance = None

def get_optimizer(use_mock=None) -> Phase3Optimizer:
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = Phase3Optimizer(use_mock=use_mock)
    return _optimizer_instance
```

### MCP Tool Pattern
```python
@mcp.tool
def backtest(...) -> dict:
    try:
        return result
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}
```

## Live Trading (Phase 6)

| Tool | Mode |
|------|------|
| `live_start_paper_trading` | Safe |
| `live_start_live_trading` | ⚠️ Requires `"I UNDERSTAND THE RISKS"` |
| `live_cancel_session`, `live_get_*` | Safe |

**Safety**: Max position 10%, daily loss 5%, drawdown 15%, auto-stop on limit.

## Strategy Creation (Phase 7)

| Tool | Purpose |
|------|---------|
| `strategy_create` | Create with iterative validation |
| `strategy_create_status` | Poll async job |
| `strategy_delete` | Requires `confirm=True` |

**Validation**: syntax → imports → structure → methods → indicators → dry-run

## Development Workflow

For mcproxy sync setup, see **../MCP_DEVELOPMENT.md**

## Landing the Plane

Work is NOT complete until `git push` succeeds:

```bash
git pull --rebase
bd sync
git push
git status  # MUST show "up to date with origin"
```

1. File issues for remaining work
2. Run quality gates (tests, linters)
3. Update/close issues
4. **PUSH** (mandatory)
5. Clean up stashes, prune branches
6. Hand off context for next session

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
