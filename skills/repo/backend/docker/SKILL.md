# Docker Backend Skill

## Description
Backend projects must run within a Docker container defined by a Dockerfile that includes all required dependencies.

## Requirements
- A `Dockerfile` must exist in the backend project root
- The Dockerfile must include all dependencies needed to run the backend
- The Docker image must build successfully

## Validation
Run the following command to validate the Dockerfile:

```bash
docker build -t backend-test .
```

A successful build (exit code 0) indicates the Dockerfile is valid and complete.
