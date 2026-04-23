# Issue #13: Setup Project Configuration - pyproject.toml and Dependencies

## Description

Create the `pyproject.toml` file that defines all project metadata, dependencies, build configuration, and tool settings. This file is the single source of truth for the Python project configuration.

### Requirements

#### Project Metadata

```toml
[project]
name = "socialseed-tasker"
version = "0.1.0"
description = "A graph-based task management framework for AI agents"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
authors = [
    {name = "SocialSeed"}
]
keywords = ["task-management", "neo4j", "graph-database", "ai-agents", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
```

#### Core Dependencies

```toml
dependencies = [
    # CLI
    "typer>=0.9.0",
    "rich>=13.0.0",
    
    # API
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    
    # Validation
    "pydantic>=2.5.0",
    
    # Database
    "neo4j>=5.15.0",
    
    # Utilities
    "python-dotenv>=1.0.0",
]
```

#### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "testcontainers[neo4j]>=3.7.0",
    
    # Linting
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    
    # Type stubs
    "types-setuptools",
    
    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.5.0",
]
```

#### Build System

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Entry Points

```toml
[project.scripts]
tasker = "socialseed_tasker.entrypoints.terminal_cli.app:main"
```

#### Tool Configuration

**Ruff (linting + formatting):**
```toml
[tool.ruff]
target-version = "py310"
line-length = 120
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.ruff.isort]
known-first-party = ["socialseed_tasker"]
```

**MyPy (type checking):**
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = ["neo4j.*"]
ignore_missing_imports = true
```

**Pytest (testing):**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "--cov=socialseed_tasker --cov-report=term-missing"
```

### Requirements
- Use `pyproject.toml` exclusively (no setup.py, no requirements.txt)
- Pin minimum versions, not exact versions (allow compatible updates)
- Include all necessary type stubs
- Configure all tools in pyproject.toml (no separate config files where possible)
- Apache 2.0 license with patent protection clauses

### Business Value

A well-configured pyproject.toml ensures consistent development experience across all contributors, enforces code quality through linting and type checking configuration, and enables proper package distribution. Using modern Python packaging standards (PEP 621) ensures compatibility with all major tools (pip, uv, poetry, hatch).

## Status: COMPLETED
