import sys
from pathlib import Path

# Add src directory to sys.path to allow absolute imports from 'app'
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from app.api.v1 import authentication, users
from app.utils.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.middleware.cors import CORSMiddleware

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(authentication.router, prefix="/authentication", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
def main():
    return {"message": "Hello from backend!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

