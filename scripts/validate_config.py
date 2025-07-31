#!/usr/bin/env python3
"""
Configuration validation tool for FastAPI CRUD application.
This script validates the current environment configuration and provides helpful feedback.
"""
import os
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.core.config import settings
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def validate_environment():
    """Validate current environment configuration"""
    print("🔍 FastAPI CRUD - Configuration Validation")
    print("=" * 50)

    try:
        # Basic configuration info
        print(f"✅ Configuration loaded successfully!")
        print(f"   Project Name: {settings.PROJECT_NAME}")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   API Version: {settings.API_V1_STR}")
        print()

        # Check critical settings
        issues = []
        warnings = []

        # Security checks
        if settings.SECRET_KEY == "changethis":
            issues.append("🔑 SECRET_KEY is using default value 'changethis'")

        if settings.FIRST_SUPERUSER_PASSWORD == "changethis":
            issues.append(
                "👤 FIRST_SUPERUSER_PASSWORD is using default value 'changethis'"
            )

        # Database configuration
        db_uri = settings.SQLALCHEMY_DATABASE_URI
        if "sqlite" in db_uri.lower():
            db_type = "SQLite"
            db_file = db_uri.split("///")[-1] if "///" in db_uri else "unknown"
            if os.path.exists(db_file):
                db_size = os.path.getsize(db_file)
                print(f"📁 Database: {db_type}")
                print(f"   File: {db_file}")
                print(f"   Size: {db_size:,} bytes")
                print(f"   Status: ✅ File exists")
            else:
                print(f"📁 Database: {db_type}")
                print(f"   File: {db_file}")
                print(
                    f"   Status: ⚠️  File does not exist (will be created on first run)"
                )
        else:
            db_type = "PostgreSQL" if "postgresql" in db_uri.lower() else "Other"
            print(f"📁 Database: {db_type}")
            print(
                f"   URI: {db_uri.split('@')[0]}@[hidden]"
                if "@" in db_uri
                else "URI format invalid"
            )

        print()

        # Environment-specific checks
        if settings.ENVIRONMENT == "production":
            if not settings.SENTRY_DSN:
                warnings.append("📊 SENTRY_DSN not configured for production")

            if not settings.SMTP_HOST:
                warnings.append("📧 SMTP not configured for production")

            if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 8 * 60:  # More than 8 hours
                warnings.append(
                    "⏰ ACCESS_TOKEN_EXPIRE_MINUTES is quite long for production"
                )

        # Email configuration
        if settings.emails_enabled:
            print("📧 Email Configuration:")
            print(f"   SMTP Host: {settings.SMTP_HOST}")
            print(f"   SMTP Port: {settings.SMTP_PORT}")
            print(f"   From Email: {settings.EMAILS_FROM_EMAIL}")
            print(f"   Status: ✅ Email is enabled")
        else:
            print("📧 Email Configuration:")
            print("   Status: ⚠️  Email is disabled (no SMTP_HOST or EMAILS_FROM_EMAIL)")

        print()

        # CORS configuration
        print("🌐 CORS Configuration:")
        print(f"   Frontend Host: {settings.FRONTEND_HOST}")
        if settings.BACKEND_CORS_ORIGINS:
            print("   Allowed Origins:")
            for origin in settings.all_cors_origins:
                print(f"     - {origin}")
        else:
            print("   ⚠️  No CORS origins configured")

        print()

        # Password hashing
        print("🔐 Password Hashing:")
        print(f"   Algorithm: {settings.PASSWORD_HASH_ALGORITHM}")
        if settings.PASSWORD_HASH_ALGORITHM == "bcrypt":
            print(f"   Bcrypt Rounds: {settings.BCRYPT_ROUNDS}")
        elif settings.PASSWORD_HASH_ALGORITHM == "argon2":
            print(f"   Argon2 Time Cost: {settings.ARGON2_TIME_COST}")
            print(f"   Argon2 Memory Cost: {settings.ARGON2_MEMORY_COST} KiB")
            print(f"   Argon2 Parallelism: {settings.ARGON2_PARALLELISM}")

        print()

        # Report issues
        if issues:
            print("❌ Configuration Issues:")
            for issue in issues:
                print(f"   {issue}")
            print()

        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   {warning}")
            print()

        if not issues and not warnings:
            print("🎉 No configuration issues found!")

        # Environment file info
        env_file = Path(".env")
        if env_file.exists():
            print(
                f"📄 Environment file: .env (exists, {env_file.stat().st_size} bytes)"
            )
        else:
            print("📄 Environment file: .env (not found)")

        return len(issues) == 0

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    try:
        success = validate_environment()

        print()
        print("💡 Tips:")
        print("   - Use 'make check-env' for quick environment validation")
        print("   - Use 'make db-health' for database-specific checks")
        print("   - Copy .env.example to .env for new setups")
        print("   - See docs/environment.md for detailed configuration guide")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
