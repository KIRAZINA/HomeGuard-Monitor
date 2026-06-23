"""Authentication dependencies for FastAPI endpoints."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.models.device import Device
from app.models.user import User
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Authenticated User

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user.

    Args:
        current_user: Authenticated user from get_current_user

    Returns:
        Active User

    Raises:
        HTTPException 400: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


agent_api_key_header = APIKeyHeader(name="X-Agent-API-Key", auto_error=False)


async def verify_agent_api_key(
    api_key: str | None = Security(agent_api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """Verify agent API key and return the associated device.

    Args:
        api_key: API key from X-Agent-API-Key header
        db: Database session

    Returns:
        Device associated with the API key

    Raises:
        AuthenticationError: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Agent API Key",
            headers={"WWW-Authenticate": "X-Agent-API-Key"},
        )

    result = await db.execute(select(Device).where(Device.api_key == api_key))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Agent API Key",
            headers={"WWW-Authenticate": "X-Agent-API-Key"},
        )

    return device


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """Validate a JWT token and return the associated user."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token")
        token_data = TokenData(email=email)
    except JWTError:
        raise AuthenticationError("Invalid token") from None

    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User not found")

    return user
