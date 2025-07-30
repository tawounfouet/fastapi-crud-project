# Troubleshooting Guide

This guide helps you diagnose and resolve common issues you might encounter while developing or deploying the FastAPI CRUD application.

## 🚨 Common Issues and Solutions

### 1. Application Startup Issues

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Symptoms:**
```bash
ModuleNotFoundError: No module named 'app'
```

**Solutions:**

**Option A: Use the development script**
```bash
./run_dev.sh
```

**Option B: Set PYTHONPATH manually**
```bash
export PYTHONPATH=/path/to/your/project:$PYTHONPATH
.venv/bin/fastapi dev app/main.py --port 8001
```

**Option C: Run from project root**
```bash
cd /path/to/fastapi-crud
.venv/bin/python -m app.main
```

#### Issue: `fastapi: command not found`

**Symptoms:**
```bash
bash: fastapi: command not found
```

**Solutions:**

**Install FastAPI CLI:**
```bash
uv add "fastapi[all]"
# or
pip install "fastapi[all]"
```

**Use the virtual environment path:**
```bash
.venv/bin/fastapi dev app/main.py --port 8001
```

#### Issue: `ValidationError` on startup

**Symptoms:**
```bash
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
POSTGRES_PASSWORD
  Field required [type=missing, input={...}]
```

**Solutions:**

**Check environment file:**
```bash
# Ensure .env file exists and is properly formatted
cat .env

# Example .env content:
PROJECT_NAME="FastAPI CRUD"
SECRET_KEY="your-secret-key-here"
# POSTGRES_SERVER=localhost
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=password
# POSTGRES_DB=app
```

**Verify environment loading:**
```bash
python check_db.py
```

### 2. Database Issues

#### Issue: SQLite database not created

**Symptoms:**
- Application starts but no database operations work
- `sqlite3.OperationalError: no such table`

**Solutions:**

**Check database file creation:**
```bash
ls -la app/sqlite3.db
```

**Manually create tables:**
```python
# Run in Python shell
from app.core.db import engine
from app.models import *
from sqlmodel import SQLModel

SQLModel.metadata.create_all(engine)
```

**Use the check script:**
```bash
python check_db.py
```

#### Issue: PostgreSQL connection failed

**Symptoms:**
```bash
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solutions:**

**Check PostgreSQL service:**
```bash
# macOS with Homebrew
brew services list | grep postgresql
brew services start postgresql

# Linux systemd
systemctl status postgresql
sudo systemctl start postgresql

# Docker
docker ps | grep postgres
docker start postgres-container-name
```

**Test connection manually:**
```bash
psql -h localhost -U postgres -d app
```

**Verify connection string:**
```python
# check_db.py output should show your connection details
python check_db.py
```

**Switch to SQLite fallback:**
```bash
# Comment out PostgreSQL settings in .env
sed -i 's/^POSTGRES_/#POSTGRES_/' .env
```

#### Issue: Database migration errors

**Symptoms:**
```bash
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "user" already exists
```

**Solutions:**

**For SQLite (automatic table creation):**
```bash
# Remove SQLite file and restart
rm app/sqlite3.db
./run_dev.sh
```

**For PostgreSQL (manual migration):**
```bash
# If using Alembic migrations
alembic upgrade head

# Or recreate database
dropdb app && createdb app
```

### 3. Authentication and User Issues

#### Issue: Cannot create superuser

**Symptoms:**
- First superuser creation fails
- `User already exists` error

**Solutions:**

**Check existing users:**
```python
# In Python shell
from app.core.db import SessionLocal
from app.models import User

with SessionLocal() as db:
    users = db.query(User).all()
    for user in users:
        print(f"Email: {user.email}, Is Superuser: {user.is_superuser}")
```

**Reset superuser:**
```python
# In Python shell
from app.core.db import SessionLocal
from app.models import User
from app.core.security import get_password_hash

with SessionLocal() as db:
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if user:
        user.is_superuser = True
        user.hashed_password = get_password_hash("changethis")
        db.commit()
        print("Superuser updated")
```

#### Issue: JWT Token errors

**Symptoms:**
```bash
JWTError: Invalid token
```

**Solutions:**

**Check SECRET_KEY:**
```bash
# Ensure SECRET_KEY is set and consistent
echo $SECRET_KEY
```

**Generate new SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Clear browser tokens:**
- Clear browser localStorage/sessionStorage
- Use incognito/private mode for testing

### 4. Development Environment Issues

#### Issue: Port already in use

**Symptoms:**
```bash
OSError: [Errno 48] Address already in use
```

**Solutions:**

**Find process using port:**
```bash
lsof -i :8001
netstat -tulpn | grep :8001
```

**Kill process:**
```bash
# Find PID from lsof output
kill -9 <PID>

# Or kill all Python processes (careful!)
pkill -f python
```

**Use different port:**
```bash
.venv/bin/fastapi dev app/main.py --port 8002
```

#### Issue: Changes not reflected (hot reload not working)

**Symptoms:**
- Code changes don't appear in the running application
- Need to manually restart server

**Solutions:**

**Check development mode:**
```bash
# Ensure using 'dev' command for hot reload
.venv/bin/fastapi dev app/main.py --port 8001
```

**Check file permissions:**
```bash
ls -la app/
# Ensure files are writable
```

**Clear Python cache:**
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

#### Issue: Import errors after adding new dependencies

**Symptoms:**
```bash
ImportError: No module named 'new_package'
```

**Solutions:**

**Sync dependencies:**
```bash
uv sync
```

**Check virtual environment:**
```bash
which python
# Should point to .venv/bin/python
```

**Reinstall dependencies:**
```bash
rm -rf .venv
uv sync
```

### 5. API Issues

#### Issue: CORS errors in browser

**Symptoms:**
```javascript
Access to XMLHttpRequest at 'http://localhost:8001' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Solutions:**

**Check CORS settings:**
```python
# app/core/config.py
BACKEND_CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8001",
]
```

**Update .env file:**
```bash
# Add your frontend URL to CORS origins
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

#### Issue: 422 Validation Error

**Symptoms:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "field_name"],
      "msg": "Field required"
    }
  ]
}
```

**Solutions:**

**Check request body:**
```bash
# Use curl to test API
curl -X POST "http://localhost:8001/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

**Verify model schema:**
```python
# Check the Pydantic model
from app.schemas import UserCreate
print(UserCreate.schema())
```

#### Issue: 401 Unauthorized

**Symptoms:**
```json
{"detail": "Not authenticated"}
```

**Solutions:**

**Get access token:**
```bash
# Login and get token
curl -X POST "http://localhost:8001/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"
```

**Use token in requests:**
```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Authorization: Bearer <your-token-here>"
```

### 6. Performance Issues

#### Issue: Slow database queries

**Symptoms:**
- Long response times
- High CPU usage

**Solutions:**

**Enable query logging:**
```python
# app/core/db.py
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=True  # Enable SQL query logging
)
```

**Add database indexes:**
```python
# In your models
from sqlmodel import Field, Index

class User(SQLModel, table=True):
    email: str = Field(index=True)  # Add index
    # ...
```

**Use connection pooling:**
```python
# app/core/db.py
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_size=20,
    max_overflow=30
)
```

#### Issue: High memory usage

**Symptoms:**
- Application consuming too much RAM
- Out of memory errors

**Solutions:**

**Limit query results:**
```python
# Use pagination
def get_users(skip: int = 0, limit: int = 100):
    return session.query(User).offset(skip).limit(limit).all()
```

**Use streaming for large datasets:**
```python
def stream_users():
    for user in session.query(User).yield_per(100):
        yield user
```

### 7. Testing Issues

#### Issue: Tests failing with database errors

**Symptoms:**
```bash
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked
```

**Solutions:**

**Use separate test database:**
```python
# tests/conftest.py
@pytest.fixture
def db():
    engine = create_engine("sqlite:///./test.db")
    SQLModel.metadata.create_all(engine)
    # ... rest of fixture
```

**Clean up after tests:**
```python
@pytest.fixture
def db():
    # Setup
    yield session
    # Cleanup
    session.close()
    os.remove("test.db")
```

#### Issue: Tests running slowly

**Solutions:**

**Use in-memory SQLite:**
```python
engine = create_engine("sqlite:///:memory:")
```

**Parallelize tests:**
```bash
pytest -n auto  # Requires pytest-xdist
```

## 🔧 Debugging Tools

### 1. Database Debugging

**Check database configuration:**
```bash
python check_db.py
```

**Inspect database schema:**
```python
# For SQLite
sqlite3 app/sqlite3.db ".schema"

# For PostgreSQL
psql -h localhost -U postgres -d app -c "\dt"
```

**Query database directly:**
```python
from app.core.db import SessionLocal
from app.models import User

with SessionLocal() as db:
    users = db.query(User).all()
    print(f"Found {len(users)} users")
```

### 2. API Debugging

**Test endpoints with curl:**
```bash
# Health check
curl http://localhost:8001/api/v1/utils/health-check/

# Get API documentation
curl http://localhost:8001/openapi.json
```

**Use interactive documentation:**
- Open http://localhost:8001/docs
- Test endpoints directly in browser

### 3. Log Analysis

**Enable detailed logging:**
```python
# app/core/config.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

**View application logs:**
```bash
# If running in background
tail -f app.log

# If using Docker
docker logs container-name -f
```

### 4. Performance Profiling

**Profile database queries:**
```python
import time
from functools import wraps

def profile_db_query(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Query {func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper
```

**Memory profiling:**
```bash
# Install memory profiler
pip install memory-profiler

# Profile a function
@profile
def my_function():
    # Your code here
    pass
```

## 📞 Getting Help

### Check Logs First

1. **Application logs**: Check console output or log files
2. **Database logs**: Check database server logs
3. **System logs**: Check system/container logs

### Useful Commands

```bash
# Check system resources
top
htop
free -h

# Check disk space
df -h

# Check network connectivity
ping google.com
telnet localhost 5432  # Test PostgreSQL connection
```

### Community Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLModel Documentation**: https://sqlmodel.tiangolo.com/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Stack Overflow**: Tag questions with `fastapi`, `sqlmodel`, `python`
- **GitHub Issues**: Check the FastAPI repository for known issues

### Creating a Bug Report

When reporting issues, include:

1. **Environment information:**
   ```bash
   python --version
   uv --version
   cat .env (remove sensitive data)
   ```

2. **Error messages:** Full stack traces
3. **Steps to reproduce:** Minimal example
4. **Expected vs actual behavior**
5. **Configuration:** Database type, OS, deployment method

### Quick Diagnostic Script

Create this script to gather diagnostic information:

```python
# diagnostic.py
import sys
import os
from pathlib import Path

def diagnose():
    print("=== FastAPI CRUD Diagnostic Information ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {sys.path}")
    
    # Check virtual environment
    venv_path = Path(".venv")
    print(f"Virtual environment exists: {venv_path.exists()}")
    
    # Check key files
    key_files = ["app/main.py", ".env", "pyproject.toml"]
    for file in key_files:
        print(f"{file} exists: {Path(file).exists()}")
    
    # Check environment variables
    env_vars = ["DATABASE_URL", "SECRET_KEY", "PROJECT_NAME"]
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if var == "SECRET_KEY" and value != "Not set":
            value = f"{value[:4]}***{value[-4:]}"  # Mask secret
        print(f"{var}: {value}")
    
    # Test imports
    try:
        from app.main import app
        print("✅ Main app import successful")
    except ImportError as e:
        print(f"❌ Main app import failed: {e}")
    
    try:
        from app.core.db import engine
        print("✅ Database engine import successful")
    except ImportError as e:
        print(f"❌ Database engine import failed: {e}")

if __name__ == "__main__":
    diagnose()
```

Run with:
```bash
python diagnostic.py
```

This troubleshooting guide should help you resolve most common issues. Remember to check the logs first, and don't hesitate to ask for help in the community forums!
