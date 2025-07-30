#!/usr/bin/env python3
"""
Simple script to check database configuration and show current setup
"""
import os
from pathlib import Path

# Load environment variables
from app.core.config import settings


def main():
    print("🗄️  FastAPI Database Configuration")
    print("=" * 50)

    db_uri = settings.SQLALCHEMY_DATABASE_URI
    print(f"Database URI: {db_uri}")

    if db_uri.startswith("sqlite"):
        # Extract SQLite file path
        sqlite_path = db_uri.replace("sqlite:///", "")
        sqlite_file = Path(sqlite_path)

        print(f"Database Type: SQLite")
        print(f"Database File: {sqlite_file}")
        print(f"File Exists: {'✅' if sqlite_file.exists() else '❌'}")

        if sqlite_file.exists():
            file_size = sqlite_file.stat().st_size
            print(f"File Size: {file_size} bytes")

    elif db_uri.startswith("postgresql"):
        print(f"Database Type: PostgreSQL")
        print(f"Server: {settings.POSTGRES_SERVER}")
        print(f"Port: {settings.POSTGRES_PORT}")
        print(f"User: {settings.POSTGRES_USER}")
        print(f"Database: {settings.POSTGRES_DB}")

    print("\n🔧 Configuration Source:")
    if settings.DATABASE_URL:
        print("Using DATABASE_URL environment variable")
    elif settings.POSTGRES_SERVER:
        print("Using PostgreSQL configuration")
    else:
        print("Using SQLite fallback (no DATABASE_URL or PostgreSQL config found)")

    print(f"\nProject Name: {settings.PROJECT_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"First Superuser: {settings.FIRST_SUPERUSER}")


if __name__ == "__main__":
    main()
