from fastapi import FastAPI

app = FastAPI(title="Skripts API")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
