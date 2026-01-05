# Docker Backend Tests Skill

## Description
Backend project tests must run within a Docker container defined by a Dockerfile.backend.tests that includes all required dependencies.

## Requirements
- A `Dockerfile.backend.tests` must exist in the backend project root
- The Dockerfile must include all dependencies needed to run the backend tests
- The Docker image must build successfully

## Validation
Run the following command to validate the Dockerfile:

```bash
docker build -f Dockerfile.backend.tests -t backend-tests .
```

A successful build (exit code 0) indicates the Dockerfile is valid and complete.
