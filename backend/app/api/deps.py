from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.schemas import UserProfile
from app.config import Settings, get_settings

DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def _get_current_user():
    from app.api.auth import get_current_user
    return get_current_user


CurrentUser = Annotated[UserProfile, Depends(_get_current_user())]
