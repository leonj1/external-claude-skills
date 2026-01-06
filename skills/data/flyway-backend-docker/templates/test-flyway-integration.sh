#!/bin/bash
set -e

echo "=== Flyway Integration Test ==="

# Cleanup any existing containers
docker compose down -v 2>/dev/null || true

# Start MySQL
echo "Starting MySQL container..."
docker compose up -d db

# Wait for MySQL to be healthy
echo "Waiting for MySQL to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker compose exec -T db mysqladmin ping -h localhost -u root -proot 2>/dev/null; then
        echo "MySQL is ready!"
        break
    fi
    echo "Waiting... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "ERROR: MySQL failed to start within timeout"
    docker compose logs db
    docker compose down -v
    exit 1
fi

# Build and start app (which runs Flyway migrations)
echo "Building and starting app container..."
docker compose up -d --build app

# Wait for app to start
echo "Waiting for app to start..."
sleep 10

# Check if app is running
if ! docker compose ps app | grep -q "Up"; then
    echo "ERROR: App container failed to start"
    docker compose logs app
    docker compose down -v
    exit 1
fi

# Verify Flyway migration was applied
echo "Verifying Flyway migration..."
RESULT=$(docker compose exec -T db mysql -u root -proot -D app -e "SELECT message FROM flyway_hello_world LIMIT 1;" 2>/dev/null)

if echo "$RESULT" | grep -q "Hello from Flyway!"; then
    echo "SUCCESS: Flyway migration applied correctly!"
    echo "Found message: Hello from Flyway!"
else
    echo "ERROR: Flyway migration verification failed"
    echo "Query result: $RESULT"
    docker compose logs app
    docker compose down -v
    exit 1
fi

# Verify flyway_schema_history table exists
echo "Verifying Flyway schema history..."
HISTORY=$(docker compose exec -T db mysql -u root -proot -D app -e "SELECT version, description FROM flyway_schema_history;" 2>/dev/null)

if echo "$HISTORY" | grep -q "hello_world"; then
    echo "SUCCESS: Flyway schema history recorded correctly!"
else
    echo "WARNING: Could not verify schema history"
fi

# Cleanup
echo "Cleaning up..."
docker compose down -v

echo "=== Integration Test PASSED ==="
