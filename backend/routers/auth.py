from fastapi import APIRouter, Depends, Header, HTTPException

from backend.config import HARDCODED_USERS
from backend.models.schemas import UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(x_user_id: str = Header(default="user-john")) -> UserInfo:
    user = next((u for u in HARDCODED_USERS if u["id"] == x_user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")
    return UserInfo(**user)


@router.get("/users", response_model=list[UserInfo])
async def list_users():
    return [UserInfo(**u) for u in HARDCODED_USERS]


@router.get("/me", response_model=UserInfo)
async def get_me(user: UserInfo = Depends(get_current_user)):
    """Returns the current user based on X-User-Id header."""
    return user
