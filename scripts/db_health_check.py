#!/usr/bin/env python3
"""
Database Health Check and Diagnostics

This script provides comprehensive database health checks and diagnostics
for the FastAPI application database setup.
"""

import sys

from sqlmodel import Session, text

from src.core.config import settings
from src.core.database import engine


def check_database_connection():
    """Test basic database connectivity."""
    print("🔍 Testing database connection...")

    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1")).first()
            print("✅ Database connection successful")
            print(f"   Database URI: {settings.SQLALCHEMY_DATABASE_URI}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_table_creation():
    """Verify that required tables exist."""
    print("\n🏗️ Checking table existence...")

    required_tables = [
        "users",
        "user_sessions",
        "user_profiles",
        "auth_refresh_tokens",
        "auth_password_reset_tokens",
        "auth_login_attempts",
        "demo_product",
        "demo_order",
        "demo_order_item",
    ]

    try:
        with Session(engine) as session:
            existing_tables = []

            for table in required_tables:
                try:
                    session.exec(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    existing_tables.append(table)
                except Exception:
                    print(f"⚠️  Table '{table}' not found")

            print(
                f"✅ Found {len(existing_tables)}/{len(required_tables)} required tables"
            )

            if existing_tables:
                print("   Existing tables:")
                for table in existing_tables:
                    print(f"   - {table}")

            return len(existing_tables) > 0

    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


def check_superuser():
    """Verify superuser exists and is accessible."""
    print("\n👤 Checking superuser configuration...")

    try:
        with Session(engine) as session:
            user = session.exec(
                text(
                    "SELECT email, is_superuser, is_active FROM users WHERE email = :email"
                ),
                {"email": settings.FIRST_SUPERUSER},
            ).first()

            if user:
                print(f"✅ Superuser found: {user[0]}")
                print(f"   Is superuser: {user[1]}")
                print(f"   Is active: {user[2]}")
                return True
            else:
                print(f"⚠️  Superuser not found: {settings.FIRST_SUPERUSER}")
                return False

    except Exception as e:
        print(f"❌ Superuser check failed: {e}")
        return False


def check_database_indexes():
    """Check for important database indexes."""
    print("\n📊 Checking database indexes...")

    if str(settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
        print("ℹ️  Index checking not implemented for SQLite")
        return True

    try:
        with Session(engine) as session:
            # Check for critical indexes
            critical_indexes = [
                ("users", "email"),
                ("users", "created_at"),
                ("auth_refresh_tokens", "user_id"),
                ("auth_refresh_tokens", "token_hash"),
            ]

            for table, column in critical_indexes:
                result = session.exec(
                    text(
                        "SELECT indexname FROM pg_indexes WHERE tablename = :table AND indexdef LIKE :column"
                    ),
                    {"table": table, "column": f"%{column}%"},
                ).fetchall()

                if result:
                    print(f"✅ Index found for {table}.{column}")
                else:
                    print(f"⚠️  Missing index for {table}.{column}")

            return True

    except Exception as e:
        print(f"ℹ️  Index check skipped: {e}")
        return True


def main():
    """Run all database health checks."""
    print("🏥 Database Health Check")
    print("=" * 50)

    checks = [
        check_database_connection,
        check_table_creation,
        check_superuser,
        check_database_indexes,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)

    print("\n📋 Summary")
    print("-" * 20)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        sys.exit(1)


if __name__ == "__main__":
    main()
