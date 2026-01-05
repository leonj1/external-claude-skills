# Docker Frontend Skill

## Description
Frontend projects must run within a Docker container defined by a Dockerfile that includes all required dependencies.

## Requirements
- A `Dockerfile` must exist in the frontend project root
- The Dockerfile must include all dependencies needed to run the frontend
- The Docker image must build successfully

## Validation
Run the following command to validate the Dockerfile:

```bash
docker build -t frontend-test .
```

A successful build (exit code 0) indicates the Dockerfile is valid and complete.
