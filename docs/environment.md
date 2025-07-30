# Environment Configuration

This guide covers the comprehensive environment configuration system for the FastAPI CRUD application, including all variables, validation, and best practices.

## 🎯 Configuration Philosophy

The application uses a hierarchical configuration approach:

1. **Environment Variables** (highest priority)
2. **`.env` file** (medium priority)
3. **Default values** (lowest priority)

This allows for flexible deployment across different environments while maintaining secure defaults.

## 📋 Complete Environment Variables Reference

### Core Application Settings

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `PROJECT_NAME` | string | - | ✅ | Application name shown in API docs |
| `ENVIRONMENT` | enum | `local` | ❌ | Environment: `local`, `staging`, `production` |
| `API_V1_STR` | string | `/api/v1` | ❌ | API version prefix |
| `SECRET_KEY` | string | auto-generated | ❌ | JWT signing key (change for production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `11520` | ❌ | JWT token expiration (8 days) |

### Database Configuration

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | string | - | ❌ | Complete database URL (highest priority) |
| `POSTGRES_SERVER` | string | - | ❌ | PostgreSQL server hostname |
| `POSTGRES_PORT` | int | `5432` | ❌ | PostgreSQL server port |
| `POSTGRES_USER` | string | - | ❌ | PostgreSQL username |
| `POSTGRES_PASSWORD` | string | `""` | ❌ | PostgreSQL password |
| `POSTGRES_DB` | string | `""` | ❌ | PostgreSQL database name |

### User Management

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `FIRST_SUPERUSER` | email | - | ✅ | Initial admin user email |
| `FIRST_SUPERUSER_PASSWORD` | string | - | ✅ | Initial admin user password |
| `EMAIL_TEST_USER` | string | `test@example.com` | ❌ | Test user email |

### CORS and Frontend

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `FRONTEND_HOST` | string | `http://localhost:5173` | ❌ | Main frontend URL |
| `BACKEND_CORS_ORIGINS` | list | `[]` | ❌ | Comma-separated allowed origins |

### Email Configuration

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `SMTP_TLS` | bool | `True` | ❌ | Enable SMTP TLS |
| `SMTP_SSL` | bool | `False` | ❌ | Enable SMTP SSL |
| `SMTP_PORT` | int | `587` | ❌ | SMTP server port |
| `SMTP_HOST` | string | - | ❌ | SMTP server hostname |
| `SMTP_USER` | string | - | ❌ | SMTP username |
| `SMTP_PASSWORD` | string | - | ❌ | SMTP password |
| `EMAILS_FROM_EMAIL` | email | - | ❌ | From email address |
| `EMAILS_FROM_NAME` | string | - | ❌ | From email name |
| `EMAIL_RESET_TOKEN_EXPIRE_HOURS` | int | `48` | ❌ | Password reset token expiry |

### Monitoring and Logging

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `SENTRY_DSN` | URL | - | ❌ | Sentry error tracking DSN |

## 🔧 Environment Configuration Flow

```mermaid
graph TD
    A[Application Start] --> B[Load .env file]
    B --> C[Read Environment Variables]
    C --> D[Merge with Defaults]
    D --> E[Validate Configuration]
    
    E --> F{Validation Successful?}
    F -->|Yes| G[Create Settings Object]
    F -->|No| H[Show Validation Errors]
    
    G --> I[Apply Computed Fields]
    I --> J[Check Security Warnings]
    J --> K[Configuration Ready]
    
    H --> L[Application Exit]
    
    style B fill:#e1f5fe
    style E fill:#e8f5e8
    style K fill:#fff3e0
    style L fill:#ffebee
```

## 📁 Environment Files

### Development (.env)

```bash
# FastAPI CRUD - Development Configuration

# ============================================================================
# CORE APPLICATION SETTINGS
# ============================================================================
PROJECT_NAME="FastAPI CRUD"
ENVIRONMENT=local

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# SQLite fallback is used automatically when PostgreSQL is not configured
# Uncomment below for PostgreSQL:
# DATABASE_URL=postgresql+psycopg://postgres:changethis@localhost:5432/fastapi_crud
# POSTGRES_SERVER=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=changethis
# POSTGRES_DB=fastapi_crud

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
SECRET_KEY=changethis-development-only
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# ============================================================================
# USER MANAGEMENT
# ============================================================================
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis

# ============================================================================
# CORS AND FRONTEND
# ============================================================================
FRONTEND_HOST=http://localhost:5173
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8001,http://localhost:5173

# ============================================================================
# EMAIL CONFIGURATION (Optional for development)
# ============================================================================
SMTP_TLS=true
SMTP_SSL=false
SMTP_PORT=587
# SMTP_HOST=smtp.gmail.com
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# EMAILS_FROM_EMAIL=noreply@yourapp.com
# EMAILS_FROM_NAME="FastAPI CRUD"

# ============================================================================
# MONITORING (Optional)
# ============================================================================
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Staging (.env.staging)

```bash
# FastAPI CRUD - Staging Configuration

# ============================================================================
# CORE APPLICATION SETTINGS
# ============================================================================
PROJECT_NAME="FastAPI CRUD - Staging"
ENVIRONMENT=staging
API_V1_STR=/api/v1

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL=postgresql+psycopg://staging_user:secure_password@staging-db:5432/fastapi_staging
# Alternative individual settings:
# POSTGRES_SERVER=staging-db.example.com
# POSTGRES_PORT=5432
# POSTGRES_USER=staging_user
# POSTGRES_PASSWORD=secure_staging_password
# POSTGRES_DB=fastapi_staging

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
SECRET_KEY=your-very-secure-staging-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours for staging

# ============================================================================
# USER MANAGEMENT
# ============================================================================
FIRST_SUPERUSER=admin@staging.yourcompany.com
FIRST_SUPERUSER_PASSWORD=secure-staging-admin-password

# ============================================================================
# CORS AND FRONTEND
# ============================================================================
FRONTEND_HOST=https://staging-app.yourcompany.com
BACKEND_CORS_ORIGINS=https://staging-app.yourcompany.com,https://staging-api.yourcompany.com

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
SMTP_TLS=true
SMTP_SSL=false
SMTP_PORT=587
SMTP_HOST=smtp.mailgun.org
SMTP_USER=staging@mg.yourcompany.com
SMTP_PASSWORD=your-mailgun-password
EMAILS_FROM_EMAIL=noreply@staging.yourcompany.com
EMAILS_FROM_NAME="FastAPI CRUD Staging"

# ============================================================================
# MONITORING
# ============================================================================
SENTRY_DSN=https://your-staging-sentry-dsn@sentry.io/staging-project-id
```

### Production (.env.production)

```bash
# FastAPI CRUD - Production Configuration
# WARNING: Keep this file secure and never commit to version control!

# ============================================================================
# CORE APPLICATION SETTINGS
# ============================================================================
PROJECT_NAME="FastAPI CRUD"
ENVIRONMENT=production
API_V1_STR=/api/v1

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL=postgresql+psycopg://prod_user:very_secure_password@prod-db-cluster:5432/fastapi_production

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
SECRET_KEY=your-extremely-secure-production-secret-key-minimum-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours for production

# ============================================================================
# USER MANAGEMENT
# ============================================================================
FIRST_SUPERUSER=admin@yourcompany.com
FIRST_SUPERUSER_PASSWORD=extremely-secure-admin-password-with-special-chars

# ============================================================================
# CORS AND FRONTEND
# ============================================================================
FRONTEND_HOST=https://yourapp.com
BACKEND_CORS_ORIGINS=https://yourapp.com,https://api.yourapp.com,https://admin.yourapp.com

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
SMTP_TLS=true
SMTP_SSL=false
SMTP_PORT=587
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAILS_FROM_EMAIL=noreply@yourcompany.com
EMAILS_FROM_NAME="Your App Name"
EMAIL_RESET_TOKEN_EXPIRE_HOURS=24

# ============================================================================
# MONITORING
# ============================================================================
SENTRY_DSN=https://your-production-sentry-dsn@sentry.io/production-project-id
```

## 🔒 Configuration Validation

### Automatic Validation

The application performs automatic validation on startup:

```python
# app/core/config.py
class Settings(BaseSettings):
    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        """Validate security-critical settings"""
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        
        # Only check PostgreSQL password if PostgreSQL is being used
        if self.POSTGRES_SERVER and self.POSTGRES_USER:
            self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
            
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        return self
```

### Security Warnings

The application will show warnings for insecure default values:

```
⚠️  WARNING: The value of SECRET_KEY is "changethis", for security, 
   please change it, at least for deployments.

⚠️  WARNING: The value of FIRST_SUPERUSER_PASSWORD is "changethis", 
   for security, please change it, at least for deployments.
```

## 🛠️ Configuration Management Tools

### Check Current Configuration

```bash
# Display current configuration
python check_db.py

# Sample output:
🗄️  FastAPI Database Configuration
==================================================
Database URI: sqlite:////path/to/app/sqlite3.db
Database Type: SQLite
File Exists: ✅
File Size: 24576 bytes

🔧 Configuration Source:
Using SQLite fallback (no DATABASE_URL or PostgreSQL config found)

Project Name: FastAPI CRUD
Environment: local
First Superuser: admin@example.com
```

### Environment Variable Testing

```bash
# Test different configurations without changing files
export PROJECT_NAME="Test App"
export ENVIRONMENT="testing"
python check_db.py

# Test PostgreSQL configuration
export POSTGRES_SERVER="localhost"
export POSTGRES_USER="testuser"
export POSTGRES_PASSWORD="testpass"
export POSTGRES_DB="testdb"
python check_db.py

# Test DATABASE_URL override
export DATABASE_URL="postgresql://user:pass@host:5432/db"
python check_db.py
```

### Configuration Validation Script

```python
#!/usr/bin/env python3
# validate_config.py - Configuration validation tool

import os
import sys
from app.core.config import Settings

def validate_environment():
    """Validate current environment configuration"""
    try:
        settings = Settings()
        print("✅ Configuration validation successful!")
        
        # Check critical settings
        issues = []
        
        if settings.SECRET_KEY == "changethis":
            issues.append("🔑 SECRET_KEY is using default value")
            
        if settings.FIRST_SUPERUSER_PASSWORD == "changethis":
            issues.append("👤 FIRST_SUPERUSER_PASSWORD is using default value")
            
        if settings.ENVIRONMENT == "production":
            if not settings.SENTRY_DSN:
                issues.append("📊 SENTRY_DSN not configured for production")
                
            if not settings.SMTP_HOST:
                issues.append("📧 SMTP not configured for production")
        
        if issues:
            print("\n⚠️  Configuration Issues:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("🎉 No configuration issues found!")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
```

## 🚀 Deployment Configurations

### Docker Configuration

```dockerfile
# Dockerfile - Environment configuration
FROM python:3.11-slim

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install uv && uv sync

# The actual environment variables should be provided at runtime
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "app/main.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Load from .env file
      - PROJECT_NAME=${PROJECT_NAME}
      - ENVIRONMENT=${ENVIRONMENT}
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - FIRST_SUPERUSER=${FIRST_SUPERUSER}
      - FIRST_SUPERUSER_PASSWORD=${FIRST_SUPERUSER_PASSWORD}
    env_file:
      - .env
    depends_on:
      - db
      
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes Configuration

```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
data:
  PROJECT_NAME: "FastAPI CRUD"
  ENVIRONMENT: "production"
  API_V1_STR: "/api/v1"
  FRONTEND_HOST: "https://yourapp.com"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: fastapi-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql://user:pass@db:5432/prod"
  FIRST_SUPERUSER_PASSWORD: "secure-password"
  SMTP_PASSWORD: "smtp-password"
```

## 🔍 Environment-Specific Behaviors

### Database Selection Logic

```mermaid
graph TD
    A[Check Configuration] --> B{DATABASE_URL set?}
    B -->|Yes| C[Use DATABASE_URL]
    B -->|No| D{PostgreSQL config complete?}
    
    D -->|Yes| E[Use PostgreSQL]
    D -->|No| F[Use SQLite]
    
    C --> G[Connect to specified database]
    E --> H[Connect to PostgreSQL]
    F --> I[Create SQLite in app/]
    
    H --> J{Environment = production?}
    I --> K[Auto-create tables]
    G --> J
    
    J -->|Yes| L[Use Alembic migrations]
    J -->|No| M[Auto-create tables if SQLite]
    
    style F fill:#e1f5fe
    style I fill:#e8f5e8
    style K fill:#e8f5e8
```

### Email Behavior by Environment

| Environment | Email Enabled | SMTP Required | Behavior |
|-------------|---------------|---------------|----------|
| `local` | Optional | No | Console logging if no SMTP |
| `staging` | Recommended | Yes | Real emails to staging domains |
| `production` | Required | Yes | Real emails to production domains |

### Security Behavior by Environment

| Setting | Local | Staging | Production |
|---------|--------|---------|------------|
| Default passwords | Warning | Error | Error |
| HTTP origins | Permissive | Restricted | Strict |
| Token expiry | Long (8 days) | Medium (1 day) | Short (8 hours) |
| Error details | Full stack | Limited | Minimal |

## 🚨 Troubleshooting Configuration

### Common Issues

#### 1. Environment Variables Not Loading

```bash
# Check if .env file exists and has correct syntax
cat .env | grep -v '^#' | grep '='

# Load environment manually
export $(grep -v '^#' .env | xargs)

# Verify specific variables
echo $PROJECT_NAME
echo $DATABASE_URL
```

#### 2. Database Configuration Issues

```bash
# Test database connection
python -c "
from app.core.config import settings
print(f'Database URI: {settings.SQLALCHEMY_DATABASE_URI}')
"

# Check database file (SQLite)
ls -la app/sqlite3.db

# Test PostgreSQL connection
psql "${DATABASE_URL}" -c "SELECT version();"
```

#### 3. Permission Issues

```bash
# Check file permissions
ls -la .env
chmod 600 .env  # Secure .env file

# Check directory permissions
ls -la app/
chmod 755 app/  # Ensure app directory is accessible
```

#### 4. Validation Errors

```bash
# Run configuration validation
python validate_config.py

# Check Pydantic validation
python -c "
from app.core.config import Settings
try:
    settings = Settings()
    print('Configuration valid!')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

---

**Previous**: [Architecture Overview](./architecture.md) | **Next**: [Development Workflow](./development.md)
