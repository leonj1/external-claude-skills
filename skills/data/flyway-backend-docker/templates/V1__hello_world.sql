-- Flyway Hello World Migration
-- This validates that Flyway is correctly configured

CREATE TABLE IF NOT EXISTS flyway_hello_world (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO flyway_hello_world (message) VALUES ('Hello from Flyway!');
