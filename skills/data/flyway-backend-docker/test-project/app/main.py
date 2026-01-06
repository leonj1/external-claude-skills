from fastapi import FastAPI

app = FastAPI(title="Flyway Test App")


@app.get("/")
def root():
    return {"status": "healthy", "message": "Flyway test app running"}


@app.get("/health")
def health():
    return {"status": "ok"}
