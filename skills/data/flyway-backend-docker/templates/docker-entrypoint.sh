#!/bin/sh
set -e

echo "=== Running Flyway migrations ==="

# Wait for database to be ready
until nc -z -v -w30 ${DB_HOST:-db} ${DB_PORT:-3306}
do
  echo "Waiting for database connection at ${DB_HOST:-db}:${DB_PORT:-3306}..."
  sleep 2
done

echo "Database is up - running migrations"

# Run Flyway migrations
flyway -url="jdbc:mysql://${DB_HOST:-db}:${DB_PORT:-3306}/${DB_NAME:-app}?allowPublicKeyRetrieval=true&useSSL=false" \
       -user=${DB_USER:-root} \
       -password=${DB_PASSWORD:-root} \
       -locations=filesystem:/app/sql \
       -connectRetries=5 \
       migrate

echo "=== Flyway migrations complete ==="
echo "=== Starting application ==="

# Execute the main command (passed as arguments)
exec "$@"
