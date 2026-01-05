# Docker Frontend Tests Skill

## Description
Frontend project tests must run within a Docker container defined by a Dockerfile.frontend.tests that includes all required dependencies.

## Requirements
- A `Dockerfile.frontend.tests` must exist in the frontend project root
- The Dockerfile must include all dependencies needed to run the frontend tests
- The Docker image must build successfully

## Validation
Run the following command to validate the Dockerfile:

```bash
docker build -f Dockerfile.frontend.tests -t frontend-tests .
```

A successful build (exit code 0) indicates the Dockerfile is valid and complete.
