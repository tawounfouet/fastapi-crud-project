# FastAPI CRUD Project - Domain Driven Development (DDD) 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLModel](https://img.shields.io/badge/SQLModel-crimson?style=for-the-badge)](https://sqlmodel.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://pydantic.dev)
[![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge)](https://docs.astral.sh/uv/)

A production-ready FastAPI CRUD application following Domain-Driven Design (DDD) principles with comprehensive email system, authentication, testing infrastructure, and modern development practices.

## ✨ Features

### 🏗️ **Architecture & Design**
- **Domain-Driven Design (DDD)** - Clean, maintainable architecture with clear separation of concerns
- **Modular Structure** - Apps-based organization (`auth`, `users`, `demo`) for scalability
- **Modern Python** - Python 3.11+ with type hints, async/await, and latest best practices
- **SQLModel Integration** - Type-safe database operations with Pydantic validation

### 🔐 **Authentication & Security**
- **JWT-based Authentication** - Secure token-based auth with refresh tokens
- **Password Security** - Modern Argon2 hashing with secure password policies
- **Role-based Access Control** - Admin/user permissions with proper authorization
- **Security Headers** - CORS, rate limiting, and security best practices

### 📧 **Email System**
- **SMTP Integration** - Production-ready Gmail/SMTP email delivery
- **Beautiful Templates** - Responsive HTML email templates with Jinja2
- **Email Types** - Welcome emails, password reset, test emails, and more
- **Template System** - MJML-based templates for cross-client compatibility
- **JWT Password Reset** - Secure token-based password recovery

### 🧪 **Testing & Quality**
- **Comprehensive Test Suite** - Unit, integration, and API endpoint testing
- **Email Testing** - Dedicated email functionality and live delivery tests
- **Test Coverage** - HTML coverage reports with detailed analysis
- **Jupyter Notebooks** - Interactive testing and demonstration notebooks
- **Make Commands** - Easy testing with `make test-email`, `make test-live-email`

### 🛠️ **Development Experience**
- **Hot Reload** - Fast development with automatic code reloading
- **Docker Support** - Complete containerization with Docker Compose
- **VS Code Integration** - Debugger configuration and Python test runner
- **Database Management** - Alembic migrations with automatic schema management
- **Code Quality** - Linting, formatting, and pre-commit hooks

## 📋 Requirements

### System Requirements
- **Python 3.11+**
- **Docker** & **Docker Compose**
- **uv** for Python package management

### Installation

```bash
# Install uv (Python package manager)
curl -sSfL https://astral.sh/uv/install.sh | sh
# or using brew
brew install uv

# Verify installation
uv --version
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fast-api-crud
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
# Configure database, email settings, JWT secrets, etc.
```

### 3. Development Setup

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run development server
make dev
# or
fastapi dev src/main.py
```

### 4. Docker Setup (Recommended)

```bash
# Start all services
docker compose up -d

# Watch for changes (development)
docker compose watch

# View logs
docker compose logs -f
```

## 🏃‍♂️ Running the Application

### Development Server

```bash
# Local development
make dev

# With hot reload
fastapi dev src/main.py --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# Start with hot reload
docker compose watch

# Or standard up
docker compose up -d

# Execute commands in container
docker compose exec backend bash
```

### API Documentation

Once running, access:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📁 Project Structure

```
├── src/                        # Main application code
│   ├── apps/                   # Domain applications
│   │   ├── auth/              # Authentication & authorization
│   │   ├── users/             # User management
│   │   └── demo/              # Demo/example endpoints
│   ├── core/                  # Core configuration & dependencies
│   ├── utils/                 # Utilities (email, auth helpers)
│   ├── emails/                # Email templates
│   └── tests/                 # Test suite
├── scripts/                   # Utility scripts
│   ├── test_email_*.py       # Email testing scripts
│   ├── db_manage.py          # Database management
│   └── validate_config.py    # Configuration validation
├── notebooks/                 # Jupyter notebooks for testing/demos
├── docs/                      # Documentation
├── htmlcov/                   # Test coverage reports
└── Makefile                   # Development commands
```

## 🧪 Testing

### Run All Tests

```bash
# Run complete test suite
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest src/tests/test_auth.py -v
```

### Email System Testing

```bash
# Test email functionality
make test-email

# Test live email delivery (requires SMTP config)
make test-live-email

# Test email API endpoints
make test-email-integration
```

### Interactive Testing

```bash
# Open Jupyter notebooks for interactive testing
jupyter lab notebooks/

# Specific email functionality demo
jupyter lab notebooks/email_functionality_demo.ipynb
```

## 📧 Email System

### Configuration

Set up email in your `.env` file:

```env
# Email Configuration
SMTP_TLS=True
SMTP_SSL=False
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=Your App Name
```

### Usage

```python
from src.utils.email import send_email, generate_test_email

# Send test email
email_data = generate_test_email(email_to="user@example.com")
await send_email(email_data)

# Send password reset email
from src.utils.auth import generate_password_reset_token
token = generate_password_reset_token("user@example.com")
# Use token in password reset email
```

### Email Templates

Templates are stored in `src/emails/` with MJML source files:

```
src/emails/
├── build/          # Compiled HTML templates
│   ├── test_email.html
│   ├── reset_password.html
│   └── new_account.html
└── src/            # MJML source files
    ├── test_email.mjml
    ├── reset_password.mjml
    └── new_account.mjml
```

## 🛢️ Database

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Management

```bash
# Check database health
python scripts/db_health_check.py

# Database utilities
python scripts/db_manage.py --help
```

## 🔧 Development Commands

The project includes a comprehensive Makefile with common development tasks:

```bash
# Development
make dev                    # Start development server
make dev-build             # Build and start with Docker
make dev-logs              # View development logs

# Testing
make test                  # Run all tests
make test-cov             # Run tests with coverage
make test-email           # Test email functionality
make test-live-email      # Test live email delivery
make test-email-integration # Test email API endpoints

# Database
make migration            # Create new migration
make migrate             # Apply migrations
make db-reset            # Reset database

# Code Quality
make lint                # Run linting
make format              # Format code
make check               # Check code quality

# Utilities
make clean               # Clean cache files
make help                # Show all commands
```

## 🏗️ Architecture

### Domain-Driven Design (DDD)

The application follows DDD principles:

- **Apps**: Domain-specific modules (`auth`, `users`, `demo`)
- **Models**: SQLModel for database entities with Pydantic validation
- **Services**: Business logic separation
- **Dependencies**: Clean dependency injection
- **APIs**: RESTful endpoints with proper HTTP semantics

### Key Components

1. **Authentication App** (`src/apps/auth/`)
   - JWT token management
   - Login/logout endpoints
   - Password reset functionality

2. **Users App** (`src/apps/users/`)
   - User CRUD operations
   - Profile management
   - Admin user management

3. **Demo App** (`src/apps/demo/`)
   - Example implementations
   - Testing endpoints
   - Development utilities

4. **Core Module** (`src/core/`)
   - Configuration management
   - Database setup
   - Global dependencies

5. **Utils Module** (`src/utils/`)
   - Email utilities
   - Authentication helpers
   - Common functions

## 🚢 Deployment

### Environment Variables

Key environment variables for production:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# App
ENVIRONMENT=production
DOMAIN=yourdomain.com
```

### Docker Production

```bash
# Build production image
docker build -t fastapi-crud .

# Run production container
docker run -d \
  --name fastapi-crud \
  -p 8000:8000 \
  --env-file .env \
  fastapi-crud
```

## 🤝 Contributing

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Set up development environment**
   ```bash
   uv sync
   source .venv/bin/activate
   ```

4. **Make your changes**
5. **Run tests**
   ```bash
   make test
   make test-email
   ```

6. **Submit a pull request**

### Development Guidelines

- **Follow DDD principles** - Keep domain logic in appropriate apps
- **Write tests** - Maintain test coverage above 80%
- **Update documentation** - Keep README and docs current
- **Use type hints** - Leverage Python's type system
- **Follow PEP 8** - Use `make format` and `make lint`

### Code Style

```bash
# Format code
make format

# Check linting
make lint

# Run all quality checks
make check
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Getting Started](docs/getting-started.md)** - Quick start guide
- **[Architecture](docs/architecture.md)** - System design and patterns
- **[API Documentation](docs/api.md)** - API endpoints and usage
- **[Database](docs/database-configuration.md)** - Database setup and migrations
- **[Email Integration](docs/email-integration-completion-summary.md)** - Email system guide
- **[DDD Guide](docs/ddd-guide/)** - Domain-driven design implementation
- **[Deployment](docs/deployment.md)** - Production deployment guide

## 🔍 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/password-recovery` - Password reset request

### Users
- `GET /api/v1/users/` - List users (admin)
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update current user

### Utils
- `POST /api/v1/utils/test-email/` - Send test email
- `GET /api/v1/health` - Health check

## ❓ Troubleshooting

### Common Issues

1. **Email not sending**
   ```bash
   # Test email configuration
   python scripts/test_email_functionality.py
   ```

2. **Database connection issues**
   ```bash
   # Check database health
   python scripts/db_health_check.py
   ```

3. **Import errors**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate
   ```

### Getting Help

- Check the [troubleshooting guide](docs/troubleshooting.md)
- Review [issue tracker](https://github.com/your-repo/issues)
- Run `make help` for available commands

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLModel** - SQL databases in Python with type safety
- **Pydantic** - Data validation and settings management
- **uv** - Fast Python package installer and resolver

---

**Made with ❤️ and FastAPI**

For more information, visit our [documentation](docs/) or check out the [live demo](https://your-demo-url.com).
