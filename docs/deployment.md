# Deployment Guide

This guide covers deploying your FastAPI CRUD application to various environments and platforms.

## 🎯 Deployment Overview

The application supports multiple deployment strategies:
- **Local Development**: SQLite with auto-configuration
- **Staging/Production**: PostgreSQL with environment-specific settings
- **Docker**: Containerized deployment
- **Cloud Platforms**: Azure, AWS, GCP deployment options

## 🐳 Docker Deployment

### Building the Docker Image

The project includes a `Dockerfile` for containerized deployment:

```bash
# Build the image
docker build -t fastapi-crud .

# Run with SQLite (development)
docker run -p 8001:8000 fastapi-crud

# Run with PostgreSQL (production)
docker run -p 8001:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  -e SECRET_KEY="your-secret-key" \
  fastapi-crud
```

### Docker Compose

For a complete development environment with PostgreSQL:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_db
      - SECRET_KEY=your-secret-key-here
    depends_on:
      - db
    volumes:
      - ./app:/app
    command: fastapi dev --host 0.0.0.0 --port 8000

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=fastapi_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

## ☁️ Cloud Platform Deployment

### Azure Deployment

#### Azure Container Apps

```bash
# Create resource group
az group create --name fastapi-rg --location eastus

# Create container app environment
az containerapp env create \
  --name fastapi-env \
  --resource-group fastapi-rg \
  --location eastus

# Deploy the application
az containerapp create \
  --name fastapi-crud \
  --resource-group fastapi-rg \
  --environment fastapi-env \
  --image your-registry/fastapi-crud:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    SECRET_KEY=your-secret-key \
    DATABASE_URL=your-postgres-url
```

#### Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --name fastapi-plan \
  --resource-group fastapi-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group fastapi-rg \
  --plan fastapi-plan \
  --name your-fastapi-app \
  --deployment-container-image-name your-registry/fastapi-crud:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group fastapi-rg \
  --name your-fastapi-app \
  --settings \
    SECRET_KEY=your-secret-key \
    DATABASE_URL=your-postgres-url
```

### AWS Deployment

#### AWS ECS Fargate

```bash
# Create cluster
aws ecs create-cluster --cluster-name fastapi-cluster

# Create task definition (task-definition.json)
{
  "family": "fastapi-crud",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "fastapi-crud",
      "image": "your-registry/fastapi-crud:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key"
        },
        {
          "name": "DATABASE_URL",
          "value": "your-postgres-url"
        }
      ]
    }
  ]
}

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster fastapi-cluster \
  --service-name fastapi-service \
  --task-definition fastapi-crud \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### AWS Lambda (Serverless)

Using Mangum for ASGI-to-Lambda adapter:

```python
# lambda_handler.py
from mangum import Mangum
from app.main import app

handler = Mangum(app)
```

Deploy using AWS SAM:

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  FastAPIFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.handler
      Runtime: python3.10
      Environment:
        Variables:
          SECRET_KEY: !Ref SecretKey
          DATABASE_URL: !Ref DatabaseURL
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

### Google Cloud Platform

#### Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/fastapi-crud

# Deploy to Cloud Run
gcloud run deploy fastapi-crud \
  --image gcr.io/your-project/fastapi-crud \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY=your-secret-key,DATABASE_URL=your-postgres-url
```

## 🗄️ Database Deployment

### PostgreSQL Setup

#### Managed Database Services

**Azure Database for PostgreSQL:**
```bash
az postgres server create \
  --resource-group fastapi-rg \
  --name fastapi-postgres \
  --location eastus \
  --admin-user postgres \
  --admin-password your-password \
  --sku-name GP_Gen5_2
```

**AWS RDS PostgreSQL:**
```bash
aws rds create-db-instance \
  --db-instance-identifier fastapi-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password your-password \
  --allocated-storage 20
```

**Google Cloud SQL:**
```bash
gcloud sql instances create fastapi-postgres \
  --database-version POSTGRES_14 \
  --tier db-f1-micro \
  --region us-central1
```

#### Self-Managed PostgreSQL

Using Docker for a simple PostgreSQL setup:

```bash
docker run -d \
  --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=fastapi_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
```

## 🔒 Security Considerations

### Environment Variables

**Never commit sensitive data to version control:**

```bash
# Use environment-specific .env files
cp .env.example .env.production
# Edit .env.production with production values
```

**Use secrets management:**

- **Azure**: Azure Key Vault
- **AWS**: AWS Secrets Manager
- **GCP**: Google Secret Manager

### SSL/TLS Configuration

**Enable HTTPS in production:**

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... other settings
    
    # Force HTTPS in production
    FORCE_HTTPS: bool = False
    
    @property
    def server_host(self) -> str:
        scheme = "https" if self.FORCE_HTTPS else "http"
        return f"{scheme}://{self.DOMAIN}"
```

### CORS Configuration

**Configure CORS for production:**

```python
# app/core/config.py
BACKEND_CORS_ORIGINS: list[str] = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## 📊 Monitoring and Logging

### Application Monitoring

**Using Prometheus and Grafana:**

```python
# Add to requirements.txt
prometheus-client==0.16.0

# app/monitoring.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def add_prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Structured Logging

```python
# app/core/logging.py
import structlog
import logging.config

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# Use in application
logger = structlog.get_logger()
logger.info("Application started", version="1.0.0", environment="production")
```

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run tests
        run: uv run pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker image
        run: |
          docker build -t ${{ secrets.REGISTRY_URL }}/fastapi-crud:${{ github.sha }} .
          docker push ${{ secrets.REGISTRY_URL }}/fastapi-crud:${{ github.sha }}
      - name: Deploy to production
        run: |
          # Your deployment script here
          echo "Deploying to production..."
```

### Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Test
    jobs:
      - job: RunTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'
          - script: |
              pip install uv
              uv sync
              uv run pytest
            displayName: 'Run tests'

  - stage: Deploy
    dependsOn: Test
    jobs:
      - job: DeployToProduction
        steps:
          - task: Docker@2
            inputs:
              command: 'buildAndPush'
              repository: 'fastapi-crud'
              tags: |
                $(Build.BuildId)
                latest
```

## 📈 Performance Optimization

### Database Connection Pooling

```python
# app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Caching

```python
# Add Redis caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# Use caching decorator
from fastapi_cache.decorator import cache

@app.get("/users")
@cache(expire=60)
async def get_users():
    # This will be cached for 60 seconds
    pass
```

## 🔧 Health Checks

```python
# app/api/routes/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/db")
async def database_health_check(db: Session = Depends(get_db)):
    try:
        # Simple query to check database connectivity
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

## 📋 Deployment Checklist

Before deploying to production:

- [ ] **Environment Variables**: All sensitive data in environment variables
- [ ] **Database**: Production database configured and accessible
- [ ] **SSL/TLS**: HTTPS enabled with valid certificates
- [ ] **CORS**: Proper CORS origins configured
- [ ] **Monitoring**: Logging and monitoring setup
- [ ] **Health Checks**: Health check endpoints configured
- [ ] **Security**: Security headers and authentication tested
- [ ] **Performance**: Load testing completed
- [ ] **Backup**: Database backup strategy in place
- [ ] **CI/CD**: Automated deployment pipeline configured
- [ ] **Documentation**: Deployment runbook created

## 🆘 Deployment Troubleshooting

### Common Issues

**Port binding issues:**
```bash
# Check if port is already in use
lsof -i :8000
netstat -tulpn | grep :8000
```

**Database connection issues:**
```bash
# Test database connectivity
python check_db.py
```

**Environment variable issues:**
```bash
# Print all environment variables
printenv | grep -i postgres
```

### Rollback Strategy

**Docker deployments:**
```bash
# Rollback to previous version
docker tag your-registry/fastapi-crud:previous your-registry/fastapi-crud:latest
docker push your-registry/fastapi-crud:latest
```

**Database migrations:**
```bash
# Rollback database migrations (if using Alembic)
cd src && alembic downgrade -1 && cd ..
```

This deployment guide provides comprehensive coverage for deploying your FastAPI CRUD application across different environments and platforms. Choose the deployment strategy that best fits your requirements and infrastructure.
