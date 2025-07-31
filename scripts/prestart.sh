#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python scripts/backend_pre_start.py

# Run migrations
cd src && alembic upgrade head && cd ..

# Create initial data in DB
python src/initial_data.py
