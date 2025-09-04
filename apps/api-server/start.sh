#!/bin/bash
set -e

echo "Starting application with database migration check..."

# Wait for database to be ready (optional, but recommended)
echo "Waiting for database to be ready..."
python -c "
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print('Warning: DATABASE_URL not set, skipping database checks')
    exit(0)

# Add SSL configuration for production databases (like Render PostgreSQL)
engine_kwargs = {}
if 'render.com' in database_url or 'dpg-' in database_url:
    # Different SSL configuration for internal vs external Render connections
    if '.singapore-postgres.render.com' in database_url:
        # External connection - requires SSL
        ssl_mode = 'require'
    else:
        # Internal connection (dpg-xxx format) - SSL may not be required/available
        ssl_mode = 'disable'
    
    engine_kwargs['connect_args'] = {
        'sslmode': ssl_mode,
        'connect_timeout': 30,
        'application_name': 'coaching-assistant-startup',
    }
    engine_kwargs['pool_pre_ping'] = True
    engine_kwargs['pool_recycle'] = 3600
    engine_kwargs['pool_timeout'] = 20

engine = create_engine(database_url, **engine_kwargs)
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready!')
        break
    except OperationalError as e:
        attempt += 1
        print(f'Database not ready yet (attempt {attempt}/{max_attempts}): {e}')
        time.sleep(2)
else:
    print('Failed to connect to database after maximum attempts')
    exit(1)
"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Migrations completed successfully!"

# Start the application
echo "Starting FastAPI application..."
cd /app
exec python main.py