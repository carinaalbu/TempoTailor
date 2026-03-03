from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.curation import router as curation_router
from app.api.drafts import router as drafts_router
from app.core.config import settings
from app.db.session import init_db
from app.models import Draft, DraftTrack, OAuthState  # noqa: F401 - register models for create_all
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="TempoTailor API", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(curation_router)
app.include_router(drafts_router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")
