from fastapi import FastAPI
from fpts.config.settings import Settings

settings = Settings()

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.environment,
        "log_level": settings.log_level,
    }
