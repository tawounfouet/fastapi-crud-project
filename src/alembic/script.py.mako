"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Business Context:
- TODO: Describe the business reason for this migration
- TODO: List any data impact or requirements
- TODO: Note any rollback considerations

Technical Notes:
- TODO: Describe any complex changes or constraints
- TODO: Note any performance implications
- TODO: Document any manual steps required

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    """Apply migration changes."""
    ${upgrades if upgrades else "pass"}


def downgrade():
    """Rollback migration changes."""
    ${downgrades if downgrades else "pass"}
