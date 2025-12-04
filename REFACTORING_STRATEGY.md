# Jesse-MCP Package Refactoring Strategy

**Objective**: Refactor jesse-mcp into a proper Python package structure that can be:
1. Installed as a package (for future PyPI distribution)
2. Deployed with Option 2 (custom Dockerfile in MetaMCP podman container)
3. Run via entry points (e.g., `jesse-mcp` command)
4. Properly imported by other packages

**Current Status**: Flat file structure in root directory
**Target Status**: Proper Python package with clear module organization

---

## Current State Analysis

### File Structure
```
/home/bk/source/jesse-mcp/
├── server.py (main MCP server, 1200+ lines)
├── phase3_optimizer.py (1000+ lines)
├── phase4_risk_analyzer.py (1000+ lines)
├── phase5_pairs_analyzer.py (700+ lines)
├── jesse_integration.py (utility layer)
├── mock_jesse.py (mock data generation)
├── test_e2e.py, test_phase3.py, test_phase4.py, test_phase5.py, test_server.py
├── requirements.txt
└── [documentation files]
```

### Current Issues
1. **Flat structure**: All Python files in root directory
2. **Flat imports**: `from phase3_optimizer import...` (not package-aware)
3. **No entry points**: No console command, must run `python server.py`
4. **No package metadata**: No setup.py, pyproject.toml, or MANIFEST.in
5. **Tests in root**: Test files mixed with source code
6. **No __init__.py**: Missing proper Python package markers

### Current Import Pattern
```python
from jesse_integration import get_jesse_wrapper, JESSE_AVAILABLE
from phase3_optimizer import get_optimizer
from phase4_risk_analyzer import get_risk_analyzer
from phase5_pairs_analyzer import get_pairs_analyzer
```

---

## Target Architecture

### Directory Structure
```
/home/bk/source/jesse-mcp/
├── jesse_mcp/                           # Main package directory
│   ├── __init__.py                      # Package initialization
│   ├── __main__.py                      # Entry point for `python -m jesse_mcp`
│   ├── cli.py                           # CLI entry point for console script
│   ├── server.py                        # MCP server implementation
│   │
│   ├── core/                            # Core utilities
│   │   ├── __init__.py
│   │   ├── integrations.py              # From jesse_integration.py
│   │   └── mock.py                      # From mock_jesse.py
│   │
│   ├── phase3/                          # Phase 3: Optimization
│   │   ├── __init__.py
│   │   └── optimizer.py                 # From phase3_optimizer.py
│   │
│   ├── phase4/                          # Phase 4: Risk Analysis
│   │   ├── __init__.py
│   │   └── risk_analyzer.py             # From phase4_risk_analyzer.py
│   │
│   └── phase5/                          # Phase 5: Pairs Trading
│       ├── __init__.py
│       └── pairs_analyzer.py            # From phase5_pairs_analyzer.py
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_e2e.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   └── test_phase5.py
│
├── setup.py                             # Package setup configuration
├── pyproject.toml                       # Modern Python packaging (PEP 518)
├── MANIFEST.in                          # Include non-Python files
├── requirements.txt                     # Runtime dependencies
├── requirements-dev.txt                 # Development dependencies
└── [existing documentation files]
```

### New Import Pattern
```python
from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
from jesse_mcp.phase3.optimizer import get_optimizer
from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer
from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer
```

---

## Implementation Plan: 10 Phases

### Phase 1: Preparation & Planning
**Goal**: Document current dependencies and plan the refactoring

**Tasks**:
- [ ] Review all Python files to identify internal imports
- [ ] Check for circular dependencies between modules
- [ ] List all external dependencies from requirements.txt
- [ ] Document any assumptions or special configurations
- [ ] Create backup of current working version (git commit)

**Deliverables**:
- Clear map of all imports
- List of any circular dependencies to resolve
- Git commit with "pre-refactoring backup" message

---

### Phase 2: Create Package Structure
**Goal**: Create the new directory structure and __init__.py files

**Tasks**:
- [ ] Create `jesse_mcp/` directory
- [ ] Create `jesse_mcp/core/` directory
- [ ] Create `jesse_mcp/phase3/` directory
- [ ] Create `jesse_mcp/phase4/` directory
- [ ] Create `jesse_mcp/phase5/` directory
- [ ] Create `tests/` directory (move out of root)
- [ ] Create empty `__init__.py` files in each directory

**Directory Creation Order**:
```bash
mkdir -p jesse_mcp/{core,phase3,phase4,phase5}
mkdir -p tests
touch jesse_mcp/__init__.py
touch jesse_mcp/core/__init__.py
touch jesse_mcp/phase3/__init__.py
touch jesse_mcp/phase4/__init__.py
touch jesse_mcp/phase5/__init__.py
touch tests/__init__.py
```

**Deliverables**:
- Complete directory structure in place
- All __init__.py files created (content added in later phases)

---

### Phase 3: Move and Refactor Core Files
**Goal**: Move utility files to jesse_mcp/core/ and update their content

**Files to move**:
1. `jesse_integration.py` → `jesse_mcp/core/integrations.py`
2. `mock_jesse.py` → `jesse_mcp/core/mock.py`

**Tasks for each file**:
- [ ] Move file to new location
- [ ] Remove or update any local imports that may conflict
- [ ] Verify the module still exports the same public API
- [ ] Create jesse_mcp/core/__init__.py with proper exports

**jesse_mcp/core/__init__.py Template**:
```python
"""
Jesse MCP Core Utilities

Provides integration with Jesse framework and mock data generation.
"""

from jesse_mcp.core.integrations import (
    get_jesse_wrapper,
    JESSE_AVAILABLE,
)
from jesse_mcp.core.mock import (
    generate_mock_data,
    MockJesse,
    # ... any other exports from mock.py
)

__all__ = [
    "get_jesse_wrapper",
    "JESSE_AVAILABLE",
    "generate_mock_data",
    "MockJesse",
]
```

**Deliverables**:
- Core utilities moved to jesse_mcp/core/
- jesse_mcp/core/__init__.py properly configured
- All public APIs exported at package level

---

### Phase 4: Move Phase Implementation Files
**Goal**: Move phase-specific implementations to their respective directories

**Files to move**:
1. `phase3_optimizer.py` → `jesse_mcp/phase3/optimizer.py`
2. `phase4_risk_analyzer.py` → `jesse_mcp/phase4/risk_analyzer.py`
3. `phase5_pairs_analyzer.py` → `jesse_mcp/phase5/pairs_analyzer.py`

**Update all imports within each file**:
- Any import of `from core.*` should become `from jesse_mcp.core.*`
- Any import of other phase files should become `from jesse_mcp.phaseX.*`
- Any relative imports should be converted to absolute imports

**Example transformation**:
```python
# Before (in phase3_optimizer.py)
from mock_jesse import MockJesse

# After (in jesse_mcp/phase3/optimizer.py)
from jesse_mcp.core.mock import MockJesse
```

**Create __init__.py for each phase**:

Example: `jesse_mcp/phase3/__init__.py`
```python
"""
Phase 3: Advanced Optimization Tools

Tools:
- optimize(): Optuna hyperparameter optimization
- monte_carlo_trades(): Monte Carlo trade distribution analysis
- monte_carlo_candles(): Candle resampling analysis
- walk_forward_optimization(): Walk-forward analysis
"""

from jesse_mcp.phase3.optimizer import get_optimizer

__all__ = ["get_optimizer"]
```

Repeat for phase4 and phase5 with their respective functions.

**Deliverables**:
- All phase files moved to jesse_mcp/phaseX/ directories
- All imports within phase files updated to use absolute package paths
- Phase-specific __init__.py files with proper exports
- No relative imports remaining

---

### Phase 5: Refactor Server Entry Point
**Goal**: Move server.py to the package and create entry points

**Tasks**:
- [ ] Move `server.py` to `jesse_mcp/server.py`
- [ ] Create `jesse_mcp/__main__.py` (for `python -m jesse_mcp`)
- [ ] Create `jesse_mcp/cli.py` (for console script entry point)
- [ ] Update all imports in server.py to use new package paths

**Update imports in jesse_mcp/server.py**:
```python
# Before
from jesse_integration import get_jesse_wrapper, JESSE_AVAILABLE
from phase3_optimizer import get_optimizer
from phase4_risk_analyzer import get_risk_analyzer
from phase5_pairs_analyzer import get_pairs_analyzer

# After
from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
from jesse_mcp.phase3.optimizer import get_optimizer
from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer
from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer
```

**jesse_mcp/__main__.py Template**:
```python
#!/usr/bin/env python3
"""
Jesse MCP Server - Entry point for running as module

Usage:
    python -m jesse_mcp
"""

import sys
from jesse_mcp.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

**jesse_mcp/cli.py Template**:
```python
#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point

Usage:
    jesse-mcp                    # Start the server
    jesse-mcp --help             # Show help
    jesse-mcp --version          # Show version
"""

import argparse
import sys
from jesse_mcp.server import JesseMCPServer

def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Jesse MCP Server - Quantitative Trading Analysis"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="jesse-mcp 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Create and run server
    server = JesseMCPServer()
    
    # Run the async server
    import asyncio
    asyncio.run(server.run())

if __name__ == "__main__":
    sys.exit(main())
```

**jesse_mcp/__init__.py Template**:
```python
"""
Jesse MCP Server

An MCP (Model Context Protocol) server providing 17 advanced quantitative
trading analysis tools organized across 5 phases.

Phases:
- Phase 1: Backtesting Fundamentals (4 tools)
- Phase 2: Data & Analysis (5 tools)
- Phase 3: Advanced Optimization (4 tools)
- Phase 4: Risk Analysis (4 tools)
- Phase 5: Pairs Trading & Regime Analysis (4 tools)
"""

__version__ = "1.0.0"
__author__ = "Jesse Team"
__all__ = ["JesseMCPServer"]

from jesse_mcp.server import JesseMCPServer
```

**Deliverables**:
- server.py moved to jesse_mcp/server.py with updated imports
- __main__.py created for module execution
- cli.py created for console script
- jesse_mcp/__init__.py properly exports public API

---

### Phase 6: Move and Update Tests
**Goal**: Move test files to tests/ directory and update their imports

**Files to move**:
- `test_server.py` → `tests/test_server.py`
- `test_e2e.py` → `tests/test_e2e.py`
- `test_phase3.py` → `tests/test_phase3.py`
- `test_phase4.py` → `tests/test_phase4.py`
- `test_phase5.py` → `tests/test_phase5.py`

**Update all imports in test files**:

Example transformation:
```python
# Before (in test_phase3.py at root)
from phase3_optimizer import get_optimizer

# After (in tests/test_phase3.py)
from jesse_mcp.phase3.optimizer import get_optimizer
```

**Ensure tests/ is a package**:
```python
# tests/__init__.py (can be empty or include conftest utilities)
```

**Deliverables**:
- All test files moved to tests/ directory
- All imports in test files updated to use package paths
- tests/__init__.py created
- Tests remain runnable with pytest

---

### Phase 7: Create Package Metadata
**Goal**: Create setup.py, pyproject.toml, and MANIFEST.in for proper packaging

**Create setup.py**:
```python
#!/usr/bin/env python3
"""
Setup configuration for jesse-mcp package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jesse-mcp",
    version="1.0.0",
    author="Jesse Team",
    description="MCP server for quantitative trading analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "*.tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "jedi>=0.19.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "typing-extensions",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jesse-mcp=jesse_mcp.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
```

**Create pyproject.toml**:
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "jesse-mcp"
version = "1.0.0"
description = "MCP server for quantitative trading analysis"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Jesse Team"}]
keywords = ["trading", "backtesting", "optimization", "mcp"]

dependencies = [
    "mcp>=1.0.0",
    "jedi>=0.19.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
    "typing-extensions",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]

[project.scripts]
jesse-mcp = "jesse_mcp.cli:main"

[tool.setuptools]
packages = ["jesse_mcp"]

[tool.setuptools.package-data]
jesse_mcp = ["py.typed"]
```

**Create MANIFEST.in**:
```
include README.md
include LICENSE
include requirements.txt
include requirements-dev.txt
recursive-include jesse_mcp *.py
```

**Update requirements.txt** (keep only runtime deps):
```
mcp>=1.0.0
jedi>=0.19.0
numpy>=1.24.0
pandas>=2.0.0
asyncio
typing-extensions
pydantic>=2.0.0
```

**Create requirements-dev.txt** (development deps):
```
# Include runtime requirements
-r requirements.txt

# Development tools
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.990
```

**Deliverables**:
- setup.py with proper configuration and entry points
- pyproject.toml with modern packaging standards
- MANIFEST.in for file inclusion
- requirements.txt with only runtime dependencies
- requirements-dev.txt with development tools

---

### Phase 8: Create Docker Configuration for Option 2
**Goal**: Document and create Dockerfile for MetaMCP integration

**Create Dockerfile** (to be used on server2):
```dockerfile
# Dockerfile for jesse-mcp in MetaMCP
FROM metamcp:latest

# Copy the jesse-mcp source code
COPY . /app/jesse-mcp
WORKDIR /app/jesse-mcp

# Install runtime dependencies
RUN pip install -q -r requirements.txt

# Install the package in development mode (for easy updates)
RUN pip install -e .

# Verify installation
RUN jesse-mcp --version

# The entry point is configured via setup.py
# MetaMCP will call: jesse-mcp (via console_scripts entry point)
```

**Create docker-compose.override.yml** (for local testing):
```yaml
version: '3.8'
services:
  metamcp:
    environment:
      - JESSE_MCP_ENABLED=true
    volumes:
      - ./jesse_mcp:/app/jesse-mcp
```

**Create installation documentation** (DOCKER_SETUP.md):
```markdown
# Adding jesse-mcp to MetaMCP on Server2

## Step 1: Build Custom Docker Image
```bash
cd /path/to/jesse-mcp
docker build -t metamcp-jesse:latest -f Dockerfile .
```

## Step 2: Add to MetaMCP Configuration
In the MetaMCP dashboard at https://metamcp.kuri.casa:

1. Navigate to **MCP Servers**
2. Click **Add Server**
3. Fill in the configuration:
   - **Name**: jesse-mcp
   - **Type**: STDIO
   - **Command**: jesse-mcp
   - **Description**: Quantitative trading analysis tools (17 tools across 5 phases)
4. Click **Create Server**

## Step 3: Create Namespace
1. Navigate to **Namespaces**
2. Click **Create Namespace**
3. Name it something like "trading-analysis"
4. Add "jesse-mcp" server to the namespace
5. Click **Create Namespace**

## Step 4: Create Endpoint
1. Navigate to **Endpoints**
2. Click **Create Endpoint**
3. Select the "trading-analysis" namespace
4. Enable API Key Authentication
5. Click **Create Endpoint**

The jesse-mcp tools are now available through MetaMCP!
```

**Deliverables**:
- Dockerfile configured for MetaMCP
- Documentation for server2 deployment
- docker-compose.override.yml for testing
- Clear instructions for MetaMCP configuration

---

### Phase 9: Validation & Testing
**Goal**: Verify everything works correctly after refactoring

**Verification Tasks**:
- [ ] Can import the package: `python -c "import jesse_mcp; print(jesse_mcp.__version__)"`
- [ ] Can run as module: `python -m jesse_mcp --version`
- [ ] Can run console script: `jesse-mcp --version` (after `pip install -e .`)
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Can import submodules: `python -c "from jesse_mcp.phase3.optimizer import get_optimizer"`
- [ ] Package structure is correct: All files in right locations
- [ ] No flat imports remain: All imports use absolute package paths
- [ ] Documentation is updated: README reflects new structure

**Testing Script** (test_refactoring.sh):
```bash
#!/bin/bash
set -e

echo "=== Testing Package Refactoring ==="

# Test 1: Import package
echo "Test 1: Importing package..."
python -c "import jesse_mcp; print(f'✓ Package version: {jesse_mcp.__version__}')"

# Test 2: Run as module
echo "Test 2: Running as module..."
python -m jesse_mcp --version

# Test 3: Console script (requires installation)
echo "Test 3: Testing console script..."
pip install -e . > /dev/null 2>&1
jesse-mcp --version

# Test 4: Import core modules
echo "Test 4: Importing core modules..."
python -c "from jesse_mcp.core.integrations import get_jesse_wrapper; print('✓ Core integrations OK')"
python -c "from jesse_mcp.core.mock import generate_mock_data; print('✓ Core mock OK')"

# Test 5: Import phase modules
echo "Test 5: Importing phase modules..."
python -c "from jesse_mcp.phase3.optimizer import get_optimizer; print('✓ Phase 3 OK')"
python -c "from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer; print('✓ Phase 4 OK')"
python -c "from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer; print('✓ Phase 5 OK')"

# Test 6: Run pytest
echo "Test 6: Running tests..."
pytest tests/ -v --tb=short

echo ""
echo "=== All Validation Tests Passed! ==="
```

**Deliverables**:
- All import statements working correctly
- All tests passing
- Package installable with `pip install -e .`
- Console script working
- No errors in package structure

---

### Phase 10: Documentation & Cleanup
**Goal**: Update documentation and clean up old files

**Update README.md**:
- Add section explaining new package structure
- Add installation instructions
- Add usage examples
- Document the refactoring work
- Keep existing documentation

**Create REFACTORING_NOTES.md**:
- Document what was changed and why
- List any breaking changes (none expected)
- Provide migration guide if needed
- Document lessons learned

**Cleanup**:
- [ ] Remove old server.py (now jesse_mcp/server.py)
- [ ] Remove old phase*.py files (now in jesse_mcp/phaseX/)
- [ ] Remove old jesse_integration.py (now jesse_mcp/core/integrations.py)
- [ ] Remove old mock_jesse.py (now jesse_mcp/core/mock.py)
- [ ] Remove old test_*.py files (now in tests/)
- [ ] Delete root directory __pycache__ if exists

**Git Commits** (use meaningful messages):
```bash
# After each phase:
git add .
git commit -m "Refactoring Phase X: [description]"

# Final cleanup:
git add .
git commit -m "Package refactoring complete: Proper Python package structure with setuptools"
```

**Deliverables**:
- Updated README with new package structure
- REFACTORING_NOTES.md documenting the work
- Old files removed from root directory
- Git history showing refactoring progress
- Clean repository ready for Option 2 Docker deployment

---

## Import Mapping Reference

For quick reference during implementation:

### Core Module Imports
```python
# Before
from jesse_integration import get_jesse_wrapper, JESSE_AVAILABLE
from mock_jesse import generate_mock_data, MockJesse

# After
from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
from jesse_mcp.core.mock import generate_mock_data, MockJesse
```

### Phase 3 Imports
```python
# Before
from phase3_optimizer import get_optimizer

# After
from jesse_mcp.phase3.optimizer import get_optimizer
```

### Phase 4 Imports
```python
# Before
from phase4_risk_analyzer import get_risk_analyzer

# After
from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer
```

### Phase 5 Imports
```python
# Before
from phase5_pairs_analyzer import get_pairs_analyzer

# After
from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer
```

---

## Entry Points Reference

After refactoring, the package can be run in multiple ways:

```bash
# Method 1: As a module
python -m jesse_mcp

# Method 2: Via console script (after installation)
jesse-mcp

# Method 3: Programmatically
python -c "from jesse_mcp import JesseMCPServer; import asyncio; asyncio.run(JesseMCPServer().run())"

# Method 4: In MetaMCP via STDIO server
# MetaMCP will invoke: jesse-mcp
```

---

## Success Criteria

The refactoring will be considered successful when:

- ✅ All files are in correct directories
- ✅ All imports use absolute package paths
- ✅ No circular dependencies exist
- ✅ All tests pass (100%)
- ✅ Package installs cleanly: `pip install -e .`
- ✅ Console script works: `jesse-mcp --version`
- ✅ Can be imported: `import jesse_mcp`
- ✅ Entry points work: `jesse-mcp` runs the server
- ✅ Ready for Dockerfile deployment: Works in custom Docker image
- ✅ Documentation updated: README and new docs explain structure
- ✅ Git history clean: Meaningful commits throughout

---

## Notes for Implementation Agent

1. **Sequential Execution**: Follow the phases in order. Earlier phases prepare infrastructure for later phases.

2. **Testing**: After each phase, verify that imports still work. Use the validation script from Phase 9.

3. **Git Commits**: Make a git commit after each phase to track progress and allow rollback if needed.

4. **Backup**: The initial backup commit is important. If something goes wrong, you can reset to it.

5. **Import Verification**: After updating each file, verify imports work with: `python -c "import module; print('OK')"`

6. **Test-Driven**: Before moving a file, make sure you understand what it does and what depends on it.

7. **No Shortcuts**: Don't skip phases. The order matters because later phases depend on earlier ones.

8. **Documentation**: Update file docstrings as you move them to reflect the new package structure.

9. **Entry Point Testing**: Phase 5 is critical - ensure __main__.py and cli.py are correctly implemented.

10. **Final Validation**: Phase 9's validation script must pass 100%. Don't skip any verification.

---

## Timeline Estimate

- Phase 1 (Prep): 15 minutes
- Phase 2 (Structure): 10 minutes
- Phase 3 (Core Files): 20 minutes
- Phase 4 (Phase Files): 30 minutes
- Phase 5 (Entry Points): 30 minutes
- Phase 6 (Tests): 20 minutes
- Phase 7 (Metadata): 20 minutes
- Phase 8 (Docker): 20 minutes
- Phase 9 (Validation): 20 minutes
- Phase 10 (Documentation): 20 minutes

**Total: ~3-4 hours**

---

*Strategy created with sequential thinking to ensure comprehensive, systematic refactoring.*
