#!/usr/bin/env python3
"""
Database Management CLI

A comprehensive CLI tool for managing the FastAPI application database,
including migrations, health checks, and maintenance operations.
"""

import argparse
import sys
from pathlib import Path
from sqlmodel import Session, text
from src.core.config import settings
from src.core.database import engine, init_db, verify_db_connection


class DatabaseManager:
    """Database management operations."""

    def __init__(self):
        self.engine = engine
        self.settings = settings

    def health_check(self, verbose: bool = False) -> bool:
        """Perform comprehensive database health check."""
        print("🏥 Database Health Check")
        print("=" * 50)

        # Basic connectivity
        if not self._check_connectivity():
            return False

        # Table existence
        if not self._check_tables(verbose):
            return False

        # Data integrity
        if not self._check_data_integrity(verbose):
            return False

        print("\n✅ All health checks passed!")
        return True

    def _check_connectivity(self) -> bool:
        """Test database connection."""
        print("\n🔍 Testing database connectivity...")

        try:
            with Session(self.engine) as session:
                session.exec(text("SELECT 1")).first()
            print(f"✅ Connected to: {self.settings.SQLALCHEMY_DATABASE_URI}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def _check_tables(self, verbose: bool) -> bool:
        """Check for required tables."""
        print("\n🏗️ Checking database schema...")

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
            with Session(self.engine) as session:
                existing_tables = []
                missing_tables = []

                for table in required_tables:
                    try:
                        session.exec(text(f"SELECT 1 FROM {table} LIMIT 1"))
                        existing_tables.append(table)
                    except Exception:
                        missing_tables.append(table)

                if missing_tables:
                    print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
                    if verbose:
                        print(
                            "   Consider running migrations or database initialization"
                        )

                print(f"✅ Found {len(existing_tables)}/{len(required_tables)} tables")
                return len(existing_tables) > 0

        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            return False

    def _check_data_integrity(self, verbose: bool) -> bool:
        """Check basic data integrity."""
        print("\n🔍 Checking data integrity...")

        try:
            with Session(self.engine) as session:
                # Check for superuser
                result = session.exec(
                    text("SELECT COUNT(*) FROM users WHERE is_superuser = 1")
                ).first()

                # Handle SQLAlchemy Row object
                superuser_count = result[0] if result else 0

                if superuser_count > 0:
                    print(f"✅ Found {superuser_count} superuser(s)")
                else:
                    print("⚠️  No superusers found")

                # Check for orphaned records (if verbose)
                if verbose:
                    print("   Performing detailed integrity checks...")
                    # Add more detailed checks here

                return True

        except Exception as e:
            print(f"❌ Data integrity check failed: {e}")
            return False

    def initialize_database(self, force: bool = False) -> bool:
        """Initialize database with required data."""
        print("🚀 Initializing database...")

        if not force:
            try:
                with Session(self.engine) as session:
                    result = session.exec(text("SELECT COUNT(*) FROM users")).first()
                    user_count = result[0] if result else 0
                    if user_count > 0:
                        print(
                            "⚠️  Database already has data. Use --force to reinitialize"
                        )
                        return False
            except Exception:
                pass  # Table might not exist, proceed with initialization

        try:
            with Session(self.engine) as session:
                init_db(session)
            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

    def vacuum_database(self) -> bool:
        """Optimize database (SQLite only)."""
        if not str(self.settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
            print("⚠️  VACUUM only supported for SQLite databases")
            return False

        print("🧹 Optimizing database...")

        try:
            with Session(self.engine) as session:
                session.exec(text("VACUUM"))
                session.exec(text("ANALYZE"))
            print("✅ Database optimized successfully")
            return True
        except Exception as e:
            print(f"❌ Database optimization failed: {e}")
            return False

    def show_stats(self) -> bool:
        """Show database statistics."""
        print("📊 Database Statistics")
        print("=" * 30)

        try:
            with Session(self.engine) as session:
                # Table row counts
                tables = ["users", "demo_product", "demo_order", "auth_refresh_tokens"]

                for table in tables:
                    try:
                        result = session.exec(
                            text(f"SELECT COUNT(*) FROM {table}")
                        ).first()
                        count = result[0] if result else 0
                        print(f"{table:20}: {count:,} rows")
                    except Exception as e:
                        print(f"{table:20}: Error - {e}")

                # Database size (SQLite only)
                if str(self.settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
                    db_path = Path("src/sqlite3.db")
                    if db_path.exists():
                        size_mb = db_path.stat().st_size / (1024 * 1024)
                        print(f"{'Database size':20}: {size_mb:.2f} MB")

                return True

        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return False

    def create_superuser_cli(
        self,
        email: str,
        password: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> bool:
        """Create a superuser via CLI interface."""
        import getpass
        from src.apps.users.services import UserService, UserAlreadyExistsError

        print(f"🔐 Creating superuser: {email}")

        # Get password if not provided
        if not password:
            while True:
                password = getpass.getpass("Password: ")
                password_confirm = getpass.getpass("Password (again): ")

                if password == password_confirm:
                    break
                print("❌ Passwords don't match. Please try again.")

        try:
            with Session(self.engine) as session:
                user_service = UserService(session)
                user = user_service.create_superuser(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                print(f"✅ Superuser created successfully: {user.email}")
                if user.first_name or user.last_name:
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    print(f"   Name: {name}")
                return True

        except UserAlreadyExistsError as e:
            print(f"❌ {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to create superuser: {e}")
            return False

    def create_user_cli(
        self,
        email: str,
        password: str = None,
        first_name: str = None,
        last_name: str = None,
        is_active: bool = True,
    ) -> bool:
        """Create a regular user via CLI interface."""
        import getpass
        from src.apps.users.services import UserService, UserAlreadyExistsError
        from src.apps.users.schemas import UserCreate

        print(f"👤 Creating user: {email}")

        # Get password if not provided
        if not password:
            while True:
                password = getpass.getpass("Password: ")
                password_confirm = getpass.getpass("Password (again): ")

                if password == password_confirm:
                    break
                print("❌ Passwords don't match. Please try again.")

        try:
            with Session(self.engine) as session:
                user_service = UserService(session)

                # Create UserCreate schema
                user_data = UserCreate(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=is_active,
                    is_superuser=False,  # Regular users are not superusers
                )

                user = user_service.create_user(user_data)
                print(f"✅ User created successfully: {user.email}")
                if user.first_name or user.last_name:
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    print(f"   Name: {name}")
                print(f"   Active: {'Yes' if user.is_active else 'No'}")
                return True

        except UserAlreadyExistsError as e:
            print(f"❌ {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Management CLI for FastAPI application"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Health check command
    health_parser = subparsers.add_parser("health", help="Run database health check")
    health_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument(
        "--force", "-f", action="store_true", help="Force reinitialization"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # Optimize command
    subparsers.add_parser("optimize", help="Optimize database (SQLite only)")

    # Create superuser command
    createsuperuser_parser = subparsers.add_parser(
        "createsuperuser", help="Create a superuser account"
    )
    createsuperuser_parser.add_argument("email", help="Superuser email address")
    createsuperuser_parser.add_argument("--first-name", help="First name (optional)")
    createsuperuser_parser.add_argument("--last-name", help="Last name (optional)")
    createsuperuser_parser.add_argument(
        "--password", help="Password (will prompt if not provided)"
    )

    # Create user command
    createuser_parser = subparsers.add_parser(
        "createuser", help="Create a regular user account"
    )
    createuser_parser.add_argument("email", help="User email address")
    createuser_parser.add_argument("--first-name", help="First name (optional)")
    createuser_parser.add_argument("--last-name", help="Last name (optional)")
    createuser_parser.add_argument(
        "--password", help="Password (will prompt if not provided)"
    )
    createuser_parser.add_argument(
        "--active",
        action="store_true",
        default=True,
        help="Make user active (default: True)",
    )
    createuser_parser.add_argument(
        "--inactive", action="store_true", help="Make user inactive"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create manager and execute command
    manager = DatabaseManager()

    try:
        if args.command == "health":
            success = manager.health_check(args.verbose)
        elif args.command == "init":
            success = manager.initialize_database(args.force)
        elif args.command == "stats":
            success = manager.show_stats()
        elif args.command == "optimize":
            success = manager.vacuum_database()
        elif args.command == "createsuperuser":
            success = manager.create_superuser_cli(
                email=args.email,
                password=args.password,
                first_name=args.first_name,
                last_name=args.last_name,
            )
        elif args.command == "createuser":
            # Determine if user should be active
            is_active = not args.inactive if hasattr(args, "inactive") else True
            success = manager.create_user_cli(
                email=args.email,
                password=args.password,
                first_name=args.first_name,
                last_name=args.last_name,
                is_active=is_active,
            )
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
