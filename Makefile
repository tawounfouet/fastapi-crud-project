# FastAPI CRUD - Project Makefile
# ============================================================================
# This Makefile provides convenient commands for development, testing, and deployment
# ============================================================================

.PHONY: help install dev test format lint clean migrate shell db-init db-reset db-health run docs check-env security pre-commit docker build deploy

# Variables
PYTHON := uv run python
UV := uv
PROJECT_NAME := fastapi-crud
SRC_DIR := src
TEST_DIR := src/tests
SCRIPTS_DIR := scripts

# Default target
help: ## Show this help message
	@echo "FastAPI CRUD - Available Commands"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Environment files:"
	@echo "  .env           - Development (active)"
	@echo "  .env.staging   - Staging template"
	@echo "  .env.production - Production template"

# ============================================================================
# SETUP AND INSTALLATION
# ============================================================================

install: ## Install dependencies using uv
	$(UV) sync
	@echo "✅ Dependencies installed successfully"

install-dev: ## Install with development dependencies
	$(UV) sync --dev
	@echo "✅ Development dependencies installed successfully"

env-setup: ## Copy .env.example to .env if .env doesn't exist
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please update the values in .env for your environment"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev: env-setup ## Start development server with auto-reload
	$(UV) run fastapi dev $(SRC_DIR)/main.py --host 0.0.0.0 --port 8000

run: ## Start production server
	$(UV) run fastapi run $(SRC_DIR)/main.py --host 0.0.0.0 --port 8000

shell: ## Start interactive Python shell with app context
	$(PYTHON) -i -c "from $(SRC_DIR).core.config import settings; from $(SRC_DIR).core.database import engine; print('🐍 FastAPI Shell - settings and engine available')"

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

db-init: ## Initialize database with initial data
	$(PYTHON) scripts/backend_pre_start.py
	cd $(SRC_DIR) && $(UV) run alembic upgrade head && cd ..
	$(PYTHON) $(SRC_DIR)/initial_data.py
	@echo "✅ Database initialized successfully"

db-reset: ## Reset database (⚠️  DESTRUCTIVE - removes all data)
	@echo "⚠️  This will DELETE ALL DATA in your database!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	$(PYTHON) scripts/debug_reset.py
	@echo "✅ Database reset completed"

db-health: ## Check database health and configuration
	$(PYTHON) scripts/check_db.py

migrate: ## Create and apply database migration
	@read -p "Migration name: " name; \
	cd $(SRC_DIR) && $(UV) run alembic revision --autogenerate -m "$$name" && cd ..
	cd $(SRC_DIR) && $(UV) run alembic upgrade head && cd ..
	@echo "✅ Migration created and applied"

migrate-create: ## Create new migration (without applying)
	@read -p "Migration name: " name; \
	cd $(SRC_DIR) && $(UV) run alembic revision --autogenerate -m "$$name" && cd ..
	@echo "✅ Migration created (not applied yet)"

migrate-apply: ## Apply pending migrations
	cd $(SRC_DIR) && $(UV) run alembic upgrade head && cd ..
	@echo "✅ Migrations applied"

migrate-history: ## Show migration history
	cd $(SRC_DIR) && $(UV) run alembic history --verbose && cd ..

migrate-current: ## Show current migration
	cd $(SRC_DIR) && $(UV) run alembic current --verbose && cd ..

# ============================================================================
# TESTING
# ============================================================================

test: ## Run all tests with coverage
	$(UV) run coverage run --source=$(SRC_DIR) -m pytest
	$(UV) run coverage report --show-missing
	@echo "✅ Tests completed"

test-html: ## Run tests and generate HTML coverage report
	$(UV) run coverage run --source=$(SRC_DIR) -m pytest
	$(UV) run coverage html --title "FastAPI CRUD Coverage"
	@echo "✅ Coverage report generated in htmlcov/"

test-unit: ## Run unit tests only
	$(UV) run pytest $(TEST_DIR) -v -m "not integration"

test-integration: ## Run integration tests only
	$(UV) run pytest $(TEST_DIR) -v -m integration

test-watch: ## Run tests in watch mode
	$(UV) run pytest-watch -- $(TEST_DIR) -v

test-debug: ## Run tests with debug output
	$(UV) run pytest $(TEST_DIR) -v -s --tb=long

# ============================================================================
# CODE QUALITY
# ============================================================================

format: ## Format code with ruff
	$(UV) run ruff check $(SRC_DIR) $(SCRIPTS_DIR) --fix
	$(UV) run ruff format $(SRC_DIR) $(SCRIPTS_DIR)
	@echo "✅ Code formatted"

lint: ## Lint code with ruff and mypy
	$(UV) run ruff check $(SRC_DIR) $(SCRIPTS_DIR)
	$(UV) run mypy $(SRC_DIR)
	@echo "✅ Code linted"

lint-fix: ## Lint and auto-fix issues
	$(UV) run ruff check $(SRC_DIR) $(SCRIPTS_DIR) --fix
	@echo "✅ Linting issues fixed"

type-check: ## Run type checking with mypy
	$(UV) run mypy $(SRC_DIR)
	@echo "✅ Type checking completed"

# ============================================================================
# SECURITY AND VALIDATION
# ============================================================================

security: ## Run security checks
	@echo "🔒 Running security checks..."
	$(UV) run python -c "from $(SRC_DIR).core.config import settings; print('✅ Configuration validation passed')"
	@echo "ℹ️  TODO: Add bandit or other security scanning tools"

check-env: ## Validate environment configuration
	@echo "🔍 Checking environment configuration..."
	$(PYTHON) -c "from $(SRC_DIR).core.config import settings; print(f'✅ Environment: {settings.ENVIRONMENT}'); print(f'✅ Project: {settings.PROJECT_NAME}'); print(f'✅ Database: {settings.SQLALCHEMY_DATABASE_URI.split(\"://\")[0]}://')"

validate-config: ## Run comprehensive configuration validation
	$(PYTHON) scripts/validate_config.py

# ============================================================================
# PRE-COMMIT AND GIT
# ============================================================================

pre-commit: format lint test ## Run all pre-commit checks
	@echo "✅ Pre-commit checks completed"

pre-commit-install: ## Install pre-commit hooks
	$(UV) run pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run: ## Run pre-commit on all files
	$(UV) run pre-commit run --all-files

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs: ## Start documentation server (if available)
	@echo "📚 API documentation available at:"
	@echo "   http://localhost:8000/docs (Swagger UI)"
	@echo "   http://localhost:8000/redoc (ReDoc)"
	@echo ""
	@echo "Start the development server with: make dev"

docs-build: ## Build documentation (placeholder for future docs)
	@echo "📚 Documentation build (TODO: implement with mkdocs or similar)"

# ============================================================================
# DOCKER
# ============================================================================

docker-build: ## Build Docker image
	docker build -t $(PROJECT_NAME):latest .
	@echo "✅ Docker image built: $(PROJECT_NAME):latest"

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env $(PROJECT_NAME):latest

docker-dev: ## Run Docker container in development mode
	docker run -p 8000:8000 -v $(PWD):/app --env-file .env $(PROJECT_NAME):latest

# ============================================================================
# DEPLOYMENT AND PRODUCTION
# ============================================================================

deploy-staging: ## Deploy to staging (customize as needed)
	@echo "🚀 Deploying to staging..."
	@echo "ℹ️  TODO: Implement staging deployment pipeline"

deploy-prod: ## Deploy to production (customize as needed)
	@echo "🚀 Deploying to production..."
	@echo "⚠️  TODO: Implement production deployment pipeline"

build: ## Build project for deployment
	$(UV) build
	@echo "✅ Project built for deployment"

# ============================================================================
# CLEANUP
# ============================================================================

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf .mypy_cache/ 2>/dev/null || true
	rm -rf .ruff_cache/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

clean-db: ## Remove SQLite database file (⚠️  DESTRUCTIVE)
	@echo "⚠️  This will DELETE the SQLite database file!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	rm -f $(SRC_DIR)/sqlite3.db
	@echo "✅ SQLite database file removed"

# ============================================================================
# UTILITIES
# ============================================================================

logs: ## Show recent application logs (if using docker/systemd)
	@echo "📋 Application logs (customize based on deployment):"
	@echo "ℹ️  For local development, check console output"

status: ## Show project status
	@echo "📊 FastAPI CRUD Project Status"
	@echo "=============================="
	@echo "Python version: $$(python --version)"
	@echo "UV version: $$($(UV) --version)"
	@echo "Project root: $$(pwd)"
	@echo "Environment file: $$([ -f .env ] && echo '✅ .env exists' || echo '❌ .env missing')"
	@echo "Dependencies: $$([ -f uv.lock ] && echo '✅ uv.lock exists' || echo '❌ uv.lock missing')"
	@$(PYTHON) -c "from $(SRC_DIR).core.config import settings; print(f'Current environment: {settings.ENVIRONMENT}')" 2>/dev/null || echo "❌ Cannot load settings"

# ============================================================================
# ADVANCED COMMANDS
# ============================================================================

user-create: ## Create a new user (interactive)
	@echo "👤 Creating new user..."
	@read -p "Email: " email; \
	read -p "First name: " first_name; \
	read -p "Last name: " last_name; \
	read -s -p "Password: " password; echo; \
	read -p "Is superuser? (y/N): " is_superuser; \
	$(PYTHON) -c "from $(SRC_DIR).apps.users.services import UserService; from $(SRC_DIR).apps.users.schemas import UserCreate; from $(SRC_DIR).api.deps import get_db; session = next(get_db()); service = UserService(session); user_data = UserCreate(email='$$email', password='$$password', first_name='$$first_name', last_name='$$last_name', is_superuser='$$is_superuser'.lower() == 'y'); user = service.create_user(user_data); print(f'✅ User created: {user.email} (ID: {user.id})')"

user-list: ## List all users
	$(PYTHON) -c "from $(SRC_DIR).apps.users.services import UserService; from $(SRC_DIR).api.deps import get_db; session = next(get_db()); service = UserService(session); users = service.get_users(); print('👥 Users:'); [print(f'  {u.email} - {u.first_name} {u.last_name} ({\"Admin\" if u.is_superuser else \"User\"})') for u in users]"

backup-db: ## Backup SQLite database
	@if [ -f $(SRC_DIR)/sqlite3.db ]; then \
		mkdir -p backups; \
		backup_name="backups/backup_$$(date +%Y%m%d_%H%M%S).db"; \
		cp $(SRC_DIR)/sqlite3.db "$$backup_name"; \
		echo "✅ Database backed up to: $$backup_name"; \
	else \
		echo "❌ No SQLite database found"; \
	fi

# Show status on make without arguments
.DEFAULT_GOAL := help

test-email: ## Test email functionality and configuration
	$(PYTHON) scripts/test_email_functionality.py

test-live-email: ## Send actual test emails (⚠️ sends real emails!)
	$(PYTHON) scripts/test_live_email.py

test-email-integration: ## Test email via FastAPI endpoints (requires running server)
	$(PYTHON) scripts/test_email_integration.py

demo-blog: ## Run blog app demonstration (requires running server)
	$(PYTHON) scripts/demo_blog_app.py
