FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pyyaml

COPY lib/ ./lib/
COPY manifest.yaml ./manifest.yaml

ENV PYTHONPATH=/app

EXPOSE 8000

ENV MANIFEST_PATH=/app/manifest.yaml

CMD ["uvicorn", "lib.skill_router.api.handlers:create_app_from_env", "--host", "0.0.0.0", "--port", "8000", "--factory"]
