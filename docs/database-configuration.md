# Database Configuration

This FastAPI application features a flexible database configuration system with automatic SQLite fallback, similar to Django's approach.

## 🎯 Configuration Philosophy

The database configuration follows a priority-based approach:

1. **DATABASE_URL** (highest priority) - Direct database URL
2. **PostgreSQL Configuration** - Individual PostgreSQL settings
3. **SQLite Fallback** (lowest priority) - Automatic fallback for development

## 🏗️ Configuration Flow

```mermaid
graph TD
    A[Application Start] --> B{DATABASE_URL exists?}
    B -->|Yes| C[Parse DATABASE_URL]
    B -->|No| D{PostgreSQL Config Complete?}
    
    D -->|Yes| E[Build PostgreSQL URL]
    D -->|No| F[Use SQLite Fallback]
    
    C --> G[Connect to Database]
    E --> G
    F --> H[Create SQLite File in app/]
    
    H --> I[Auto-create Tables]
    I --> G
    
    G --> J{Connection Successful?}
    J -->|Yes| K[Initialize Superuser]
    J -->|No| L[Show Error]
    
    K --> M[Application Ready]
    
    style F fill:#e1f5fe
    style H fill:#e8f5e8
    style I fill:#e8f5e8
    style M fill:#fff3e0
```

## 📝 Configuration Options

### Option 1: DATABASE_URL (Recommended for Production)

Set a complete database URL in your environment:

```bash
# PostgreSQL
DATABASE_URL=postgresql+psycopg://username:password@host:port/database

# SQLite (explicit)
DATABASE_URL=sqlite:///path/to/database.db

# MySQL (if supported)
DATABASE_URL=mysql+pymysql://username:password@host:port/database
```

### Option 2: PostgreSQL Individual Settings

Configure PostgreSQL using individual environment variables:

```bash
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
```

### Option 3: SQLite Fallback (Automatic)

When neither `DATABASE_URL` nor complete PostgreSQL configuration is provided:

- Automatically creates `app/sqlite3.db`
- Tables are auto-created on startup
- Perfect for development and testing

## 🛠️ Implementation Details

### Configuration Class (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # Database Configuration with SQLite fallback
    DATABASE_URL: str | None = None
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Priority 1: Direct DATABASE_URL
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Priority 2: PostgreSQL configuration
        if self.POSTGRES_SERVER and self.POSTGRES_USER:
            return str(MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            ))
        
        # Priority 3: SQLite fallback
        app_folder = Path(__file__).parent.parent
        sqlite_path = app_folder / "sqlite3.db"
        return f"sqlite:///{sqlite_path}"
```

### Database Engine Creation (`app/core/db.py`)

```python
from sqlmodel import Session, SQLModel, create_engine

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Auto-create tables for SQLite
if str(settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
    SQLModel.metadata.create_all(engine)
```

## 🔄 Database Scenarios

### Scenario 1: Development with SQLite

**Environment Variables**: None required for database

**Result**:
```
Database URI: sqlite:////path/to/app/sqlite3.db
Database Type: SQLite
File Location: app/sqlite3.db
Auto-created: ✅
Tables: Auto-created on startup
```

**Advantages**:
- No setup required
- Portable database file
- Perfect for development
- No external dependencies

### Scenario 2: Production with PostgreSQL (DATABASE_URL)

**Environment Variables**:
```bash
DATABASE_URL=postgresql+psycopg://user:pass@db.example.com:5432/proddb
```

**Result**:
```
Database URI: postgresql+psycopg://user:pass@db.example.com:5432/proddb
Database Type: PostgreSQL
Server: db.example.com
Tables: Created via Alembic migrations
```

**Advantages**:
- Production-ready
- Supports migrations
- Better performance
- Multi-user support

### Scenario 3: Local PostgreSQL Development

**Environment Variables**:
```bash
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=dev_pass
POSTGRES_DB=dev_db
```

**Result**:
```
Database URI: postgresql+psycopg://dev_user:dev_pass@localhost:5432/dev_db
Database Type: PostgreSQL
Local Development: ✅
Tables: Via Alembic or auto-creation
```

## 🗂️ File Structure and Storage

### SQLite Storage

```
app/
├── sqlite3.db          # SQLite database file
├── core/
│   ├── config.py       # Configuration logic
│   └── db.py           # Database engine
└── models.py           # SQLModel definitions
```

### Migration Files (PostgreSQL)

```
app/
├── alembic/
│   ├── versions/       # Migration files
│   │   ├── 001_initial.py
│   │   └── 002_add_users.py
│   └── env.py          # Alembic config
└── alembic.ini         # Alembic settings
```

## 🎛️ Environment File Examples

### Development (.env)

```bash
# Basic development setup
PROJECT_NAME="FastAPI CRUD"
ENVIRONMENT=local
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis
SECRET_KEY=your-secret-key

# Database: SQLite (automatic fallback)
# No database config needed!

# CORS for local development
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8001
```

### Production (.env)

```bash
# Production configuration
PROJECT_NAME="FastAPI CRUD Production"
ENVIRONMENT=production
FIRST_SUPERUSER=admin@yourcompany.com
FIRST_SUPERUSER_PASSWORD=secure-password-here
SECRET_KEY=very-secure-secret-key

# Database: PostgreSQL
DATABASE_URL=postgresql+psycopg://user:password@db-server:5432/prod_db

# CORS for production domains
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Email configuration
SMTP_HOST=smtp.yourprovider.com
SMTP_USER=noreply@yourcompany.com
SMTP_PASSWORD=email-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

## 🧪 Testing Database Configuration

### Check Current Configuration

```bash
# Run the database checker
python check_db.py
```

### Test Different Configurations

```bash
# Test SQLite fallback
unset DATABASE_URL POSTGRES_SERVER
python check_db.py

# Test PostgreSQL
export POSTGRES_SERVER=localhost
export POSTGRES_USER=testuser
python check_db.py

# Test DATABASE_URL
export DATABASE_URL="sqlite:///test.db"
python check_db.py
```

## 🔧 Migration Management

### SQLite (Development)

- **Auto-migration**: Tables created automatically
- **No migration files**: Changes applied directly
- **Data persistence**: Database file retained between runs

### PostgreSQL (Production)

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current

# Rollback migration
alembic downgrade -1
```

## 🚨 Troubleshooting

### SQLite Issues

**File Permission Errors**:
```bash
# Ensure app directory is writable
chmod 755 app/
```

**Database Locked**:
```bash
# Check for other processes using the database
lsof app/sqlite3.db
```

### PostgreSQL Issues

**Connection Refused**:
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection manually
psql -h localhost -U username -d database
```

**Authentication Failed**:
```bash
# Verify credentials
echo $POSTGRES_PASSWORD
echo $POSTGRES_USER
```

### Configuration Issues

**Environment Variables Not Loading**:
```bash
# Check .env file syntax
cat .env | grep -v '^#'

# Load manually
export $(grep -v '^#' .env | xargs)
```

## 📊 Performance Considerations

### SQLite

- ✅ **Fast for development**: Single-file database
- ✅ **No setup overhead**: Zero configuration
- ❌ **Limited concurrency**: Single writer
- ❌ **Not for production**: File-based limitations

### PostgreSQL

- ✅ **Production ready**: Multi-user support
- ✅ **ACID compliance**: Data integrity
- ✅ **Scalability**: Handles large datasets
- ❌ **Setup complexity**: Requires server installation

## 🔄 Switching Between Databases

### From SQLite to PostgreSQL

1. **Set up PostgreSQL server**
2. **Configure environment variables**:
   ```bash
   DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/mydb
   ```
3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```
4. **Restart application**

### From PostgreSQL to SQLite

1. **Remove PostgreSQL configuration**:
   ```bash
   unset DATABASE_URL POSTGRES_SERVER POSTGRES_USER
   ```
2. **Restart application** (SQLite auto-created)

---

**Previous**: [Getting Started](./getting-started.md) | **Next**: [Architecture Overview](./architecture.md)
