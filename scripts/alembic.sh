#!/bin/bash
# Alembic helper script to run migrations from project root
# Usage: ./scripts/alembic.sh [alembic commands]
# Examples:
#   ./scripts/alembic.sh current
#   ./scripts/alembic.sh upgrade head
#   ./scripts/alembic.sh revision -m "description"

cd "$(dirname "$0")/.." || exit 1
cd src || exit 1
alembic "$@"
