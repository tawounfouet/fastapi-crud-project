"""add_auth_models

Revision ID: 23202aace4b1
Revises: 9e0d977dd763
Create Date: 2025-07-31 00:52:03.677336

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "23202aace4b1"
down_revision = "9e0d977dd763"
branch_labels = None
depends_on = None


def upgrade():
    """Create auth tables for authentication functionality."""

    # Create auth_refresh_tokens table
    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("token_hash", sa.VARCHAR(255), nullable=False),
        sa.Column("user_id", sa.CHAR(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.BOOLEAN, nullable=False, default=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_id", sa.VARCHAR(255), nullable=True),
        sa.Column("user_agent", sa.VARCHAR(500), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(45), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("token_hash"),
    )

    # Create indexes for auth_refresh_tokens
    op.create_index(
        "ix_auth_refresh_tokens_created_at", "auth_refresh_tokens", ["created_at"]
    )
    op.create_index(
        "ix_auth_refresh_tokens_token_hash", "auth_refresh_tokens", ["token_hash"]
    )
    op.create_index(
        "ix_auth_refresh_tokens_user_id", "auth_refresh_tokens", ["user_id"]
    )

    # Create auth_password_reset_tokens table
    op.create_table(
        "auth_password_reset_tokens",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("token_hash", sa.VARCHAR(255), nullable=False),
        sa.Column("user_id", sa.CHAR(32), nullable=False),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.BOOLEAN, nullable=False, default=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(45), nullable=True),
        sa.Column("user_agent", sa.VARCHAR(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("token_hash"),
    )

    # Create indexes for auth_password_reset_tokens
    op.create_index(
        "ix_auth_password_reset_tokens_created_at",
        "auth_password_reset_tokens",
        ["created_at"],
    )
    op.create_index(
        "ix_auth_password_reset_tokens_token_hash",
        "auth_password_reset_tokens",
        ["token_hash"],
    )
    op.create_index(
        "ix_auth_password_reset_tokens_user_id",
        "auth_password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_auth_password_reset_tokens_email", "auth_password_reset_tokens", ["email"]
    )

    # Create auth_login_attempts table
    op.create_table(
        "auth_login_attempts",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("successful", sa.BOOLEAN, nullable=False, default=False),
        sa.Column("failure_reason", sa.VARCHAR(255), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(45), nullable=True),
        sa.Column("user_agent", sa.VARCHAR(500), nullable=True),
        sa.Column("user_id", sa.CHAR(32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Create indexes for auth_login_attempts
    op.create_index(
        "ix_auth_login_attempts_created_at", "auth_login_attempts", ["created_at"]
    )
    op.create_index("ix_auth_login_attempts_email", "auth_login_attempts", ["email"])


def downgrade():
    """Drop auth tables."""

    # Drop indexes first
    op.drop_index("ix_auth_login_attempts_email", "auth_login_attempts")
    op.drop_index("ix_auth_login_attempts_created_at", "auth_login_attempts")
    op.drop_index("ix_auth_password_reset_tokens_email", "auth_password_reset_tokens")
    op.drop_index("ix_auth_password_reset_tokens_user_id", "auth_password_reset_tokens")
    op.drop_index(
        "ix_auth_password_reset_tokens_token_hash", "auth_password_reset_tokens"
    )
    op.drop_index(
        "ix_auth_password_reset_tokens_created_at", "auth_password_reset_tokens"
    )
    op.drop_index("ix_auth_refresh_tokens_user_id", "auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_token_hash", "auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_created_at", "auth_refresh_tokens")

    # Drop tables
    op.drop_table("auth_login_attempts")
    op.drop_table("auth_password_reset_tokens")
    op.drop_table("auth_refresh_tokens")
