from fastapi import FastAPI

from app.api.users.resources import router as user_router
from app.api.ingest.resources import router as arcsight_router
app = FastAPI()

app.include_router(user_router)
app.include_router(arcsight_router)

