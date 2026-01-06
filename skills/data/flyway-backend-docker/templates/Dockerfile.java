FROM eclipse-temurin:21-jre-alpine

# Install tini and netcat
RUN apk add --no-cache tini wget curl bash netcat-openbsd

# Install Flyway with retry logic
ENV FLYWAY_VERSION=10.22.0
RUN mkdir -p /tmp/flyway && \
    curl -fSL --retry 3 --retry-delay 5 \
        "https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/${FLYWAY_VERSION}/flyway-commandline-${FLYWAY_VERSION}-linux-alpine-x64.tar.gz" \
        -o /tmp/flyway/flyway.tar.gz && \
    tar -xzf /tmp/flyway/flyway.tar.gz -C /opt && \
    ln -s /opt/flyway-${FLYWAY_VERSION}/flyway /usr/local/bin/flyway && \
    rm -rf /tmp/flyway

WORKDIR /app

# Copy SQL migrations
COPY sql/ /app/sql/

# Copy JAR file
COPY target/*.jar app.jar

# Copy entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

# Use tini as init, entrypoint runs flyway then app
ENTRYPOINT ["/sbin/tini", "--", "/docker-entrypoint.sh"]
CMD ["java", "-jar", "app.jar"]
