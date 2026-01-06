FROM python:3.13-slim

# Install tini, flyway dependencies, and netcat for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    wget \
    curl \
    netcat-openbsd \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Flyway with retry logic
ENV FLYWAY_VERSION=10.22.0
RUN mkdir -p /tmp/flyway && \
    curl -fSL --retry 3 --retry-delay 5 \
        "https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/${FLYWAY_VERSION}/flyway-commandline-${FLYWAY_VERSION}-linux-x64.tar.gz" \
        -o /tmp/flyway/flyway.tar.gz && \
    tar -xzf /tmp/flyway/flyway.tar.gz -C /opt && \
    ln -s /opt/flyway-${FLYWAY_VERSION}/flyway /usr/local/bin/flyway && \
    rm -rf /tmp/flyway

WORKDIR /app

# Copy SQL migrations
COPY sql/ /app/sql/

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy application code
COPY . .

EXPOSE 8000

# Use tini as init, entrypoint runs flyway then app
ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
