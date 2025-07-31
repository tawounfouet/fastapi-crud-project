"""remove_old_tables_cleanup

Revision ID: 9e0d977dd763
Revises: 425b97d9ed0c
Create Date: 2025-07-31 00:25:03.843841

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "9e0d977dd763"
down_revision = "425b97d9ed0c"
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove old tables that are no longer needed after DDD refactoring:
    - Old 'user' table (replaced by 'users')
    - Old 'item' table (no longer used)
    - Old DDD tables with prefixes (replaced by clean versions)
    """
    # Remove old tables
    op.drop_table("item")
    op.drop_table("user")
    op.drop_table("ddd_user_profiles")
    op.drop_table("ddd_user_sessions")
    op.drop_table("ddd_users")


def downgrade():
    """
    Recreate the old tables (basic structure only for rollback purposes)
    Note: This won't restore data, just table structure
    """
    # Recreate old user table
    op.create_table(
        "user",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("is_active", sa.BOOLEAN, nullable=False),
        sa.Column("is_superuser", sa.BOOLEAN, nullable=False),
        sa.Column("full_name", sa.VARCHAR(255), nullable=True),
        sa.Column("hashed_password", sa.VARCHAR, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Recreate old item table
    op.create_table(
        "item",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("title", sa.VARCHAR(255), nullable=False),
        sa.Column("description", sa.VARCHAR(255), nullable=True),
        sa.Column("owner_id", sa.CHAR(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
    )

    # Note: Not recreating ddd_ tables as they were intermediate versions
