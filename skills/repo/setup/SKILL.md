# Project Makefile Setup Skill

## Description
Creates a Makefile for managing project lifecycle events using Docker containers. The Makefile supports backend and frontend projects with configurable listening ports.

## Requirements
- A `Makefile` must exist in the project root
- The Makefile must include the following targets: `build`, `stop`, `start`, `restart`, `test`
- Port configuration must be overridable via environment variables

## Makefile Structure

```makefile
# Default ports (can be overridden)
BACKEND_PORT ?= 8080
FRONTEND_PORT ?= 3000

.PHONY: build stop start restart test

build:
	docker build -t $(PROJECT_NAME) .

stop:
	docker stop $(PROJECT_NAME) || true

start:
	docker run -d --name $(PROJECT_NAME) -p $(BACKEND_PORT):$(BACKEND_PORT) $(PROJECT_NAME)
	# For frontend: -p $(FRONTEND_PORT):$(FRONTEND_PORT)

restart: stop start

test:
	docker build -f Dockerfile.backend.tests -t $(PROJECT_NAME)-tests .
	docker run --rm $(PROJECT_NAME)-tests
	# For frontend: use Dockerfile.frontend.tests
```

## Port Override Examples

```bash
# Override backend port
BACKEND_PORT=9000 make start

# Override frontend port
FRONTEND_PORT=4000 make start
```

## Validation
Run the following command to validate the Makefile:

```bash
make build
```

A successful build (exit code 0) indicates the Makefile is valid and functional.
