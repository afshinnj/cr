"""FastAPI dependencies: settings, clock, database session, local auth."""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, get_clock
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.database.session import get_db_session


async def db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]
SessionDep = Annotated[AsyncSession, Depends(db_session)]


async def require_local_token(
    settings: SettingsDep,
    x_local_token: Annotated[str | None, Header(alias="X-Local-Token")] = None,
) -> None:
    """Guard the loopback API against other local processes.

    Disabled when no token is configured (development convenience); the
    settings validator makes the token mandatory in production.
    """
    expected = settings.local_api_token.get_secret_value()
    if not expected:
        return
    if not x_local_token or not secrets.compare_digest(x_local_token, expected):
        raise UnauthorizedError("A valid X-Local-Token header is required")


LocalAuth = Depends(require_local_token)
