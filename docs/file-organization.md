# File Organization & Project Structure

This document explains the project's file organization, especially the DDD (Domain-Driven Development) structure and configuration file placement.

## 📁 Project Structure Overview

```
fastapi-crud/
├── src/                          # All source code and configurations
│   ├── alembic.ini              # Database migration configuration
│   ├── main.py                  # FastAPI application entry point
│   ├── alembic/                 # Database migration files
│   ├── apps/                    # DDD application modules
│   ├── api/                     # API routing and endpoints
│   ├── core/                    # Core functionality (DB, auth, config)
│   └── tests/                   # Test files
├── scripts/                     # Utility scripts
│   ├── alembic.sh              # Alembic wrapper script
│   └── *.sh                    # Other automation scripts
├── docs/                        # Documentation
├── .env                        # Environment configuration
└── pyproject.toml              # Project configuration
```

## 🎯 Design Principles

### Source Code Centralization

All source code and related configuration files are located in the `src/` directory:

**Benefits:**
- **Clear separation** between source code and project metadata
- **Easier deployment** - just package the `src/` directory
- **Better IDE support** - most IDEs recognize `src/` as the source root
- **Cleaner project root** - reduces clutter in the main directory

### Configuration File Placement

#### alembic.ini Location

**Current Location:** `src/alembic.ini`
**Previous Location:** `./alembic.ini` (project root)

**Why moved to src/?**
1. **Logical grouping**: Configuration belongs with the code it configures
2. **Deployment simplicity**: All source-related files in one place
3. **Better organization**: Reduces project root clutter
4. **Industry standard**: Many Python projects follow this pattern

#### Usage Patterns

**From src/ directory (direct):**
```bash
cd src
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**From project root (via script):**
```bash
./scripts/alembic.sh upgrade head
./scripts/alembic.sh revision --autogenerate -m "description"
```

**In deployment scripts:**
```bash
# scripts/prestart.sh
cd src && alembic upgrade head && cd ..
```

## 📱 DDD App Structure

### Apps Directory Organization

```
src/apps/
├── shared.py                    # Shared utilities across apps
├── users/                       # User management domain
│   ├── __init__.py
│   ├── models.py               # Database models
│   ├── schemas.py              # API schemas (Pydantic)
│   ├── services.py             # Business logic
│   ├── views.py                # API endpoints
│   ├── urls.py                 # URL routing
│   └── tests/                  # App-specific tests
└── demo/                       # Demo/example domain
    ├── models.py
    ├── schemas.py
    ├── services.py
    ├── views.py
    ├── urls.py
    └── tests/
```

### DDD Component Responsibilities

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| **models.py** | Database entities, relationships | SQLModel, core DB |
| **schemas.py** | API input/output validation | Pydantic |
| **services.py** | Business logic, CRUD operations | Models, core services |
| **views.py** | HTTP endpoints, request handling | FastAPI, services |
| **urls.py** | Route configuration | FastAPI, views |
| **tests/** | Unit and integration tests | Pytest, app components |

### App Integration Pattern

```python
# src/apps/users/urls.py
from fastapi import APIRouter
from .views import router as views_router

# Create app router
router = APIRouter(prefix="/users", tags=["users"])
router.include_router(views_router)

# src/api/router.py
from fastapi import APIRouter
from apps.users.urls import router as users_router
from apps.demo.urls import router as demo_router

# Main API router
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(users_router)
api_router.include_router(demo_router)
```

## 🔧 Configuration Management

### Environment Files

```
├── .env                        # Local development (gitignored)
├── .env.example               # Template for .env
└── src/core/config.py         # Configuration parser
```

**Configuration hierarchy:**
1. Environment variables (highest priority)
2. `.env` file values
3. Default values in `config.py` (lowest priority)

### Database Configuration

**SQLite (default for development):**
```python
# Automatic fallback when no PostgreSQL config
SQLALCHEMY_DATABASE_URI = "sqlite:///src/sqlite3.db"
```

**PostgreSQL (production):**
```bash
# .env
DATABASE_URL=postgresql+psycopg://user:pass@host:port/db
```

## 📜 Scripts and Automation

### Script Organization

```
scripts/
├── alembic.sh                  # Database migration wrapper
├── format.sh                  # Code formatting
├── lint.sh                    # Linting and type checking
├── test.sh                    # Test execution
└── prestart.sh                # Deployment preparation
```

### Script Design Patterns

**Wrapper Scripts Benefits:**
- **Consistent interface** across different environments
- **Path management** - handles directory changes automatically
- **Environment setup** - loads necessary environment variables
- **Error handling** - provides better error messages

**Example wrapper pattern:**
```bash
#!/bin/bash
# scripts/alembic.sh
cd "$(dirname "$0")/.." || exit 1  # Go to project root
cd src || exit 1                   # Enter source directory
alembic "$@"                       # Forward all arguments
```

## 🚀 Development Workflow

### File Organization Benefits

1. **Clean imports**: All source code in one place
2. **Easy testing**: Clear test structure
3. **Simple deployment**: Package `src/` directory
4. **Better IDE support**: Source root recognition
5. **Logical grouping**: Related files together

### Common Operations

**Starting development:**
```bash
# Setup
uv sync
cp .env.example .env

# Development
./run_dev.sh                    # Start server
./scripts/test.sh              # Run tests
./scripts/alembic.sh current   # Check migrations
```

**Database operations:**
```bash
# Create migration
./scripts/alembic.sh revision --autogenerate -m "description"

# Apply migrations
./scripts/alembic.sh upgrade head

# Check status
./scripts/alembic.sh current
```

**Code quality:**
```bash
./scripts/format.sh            # Format code
./scripts/lint.sh              # Check code quality
./scripts/test.sh              # Run tests
```

## 🏗️ Migration from Old Structure

### Changes Made

**File movements:**
- `alembic.ini` → `src/alembic.ini`
- `src/api/main.py` → `src/api/router.py`

**Script updates:**
- Updated `scripts/prestart.sh` to use `cd src && alembic ...`
- Created `scripts/alembic.sh` wrapper
- Updated documentation references

**Import updates:**
- Fixed all import paths for new structure
- Updated API router imports
- Cleaned up circular dependencies

### Compatibility

**Backward compatibility maintained:**
- All existing functionality works
- No breaking API changes
- Migration history preserved
- Environment configuration unchanged

**New preferred methods:**
- Use `./scripts/alembic.sh` from project root
- Use `cd src && alembic ...` in scripts
- Import from `src.apps.*` structure

## 📚 Best Practices

### File Organization Rules

1. **Source code belongs in src/**: All Python code, configs, migrations
2. **Scripts are utilities**: Automation, helpers, deployment tools
3. **Docs are separate**: Documentation, guides, examples
4. **Root is metadata**: Project config, dependencies, git files

### DDD App Guidelines

1. **One domain per app**: Users, orders, products, etc.
2. **Clear boundaries**: Minimal coupling between apps
3. **Consistent structure**: All apps follow same pattern
4. **Shared utilities**: Common code in `apps/shared.py`

### Configuration Management

1. **Environment-based**: Different configs per environment
2. **Secure defaults**: Safe fallbacks for development
3. **Documentation**: All config options documented
4. **Validation**: Config validation at startup

---

**Related Documentation:**
- [Development Guide](./development.md)
- [Database Configuration](./database-configuration.md)
- [DDD Guide](./ddd-guide/README.md)
