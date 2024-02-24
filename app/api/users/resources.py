from fastapi import APIRouter, Depends

from app.api.users.models import UserBase
from app.database import get_session

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/", dependencies=[Depends(get_session)])
async def get_users():
    return UserBase.get_all()