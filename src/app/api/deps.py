from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.authentication_service import AuthenticationService
from app.services.user_service import UserService

from app.utils import jwt_service
from app.schemas.token import TokenPayload

from app.services.redis_service import RedisService

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_redis_service() -> RedisService:
    return RedisService()

def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)

def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    redis_service: RedisService = Depends(get_redis_service),
) -> AuthenticationService:
    return AuthenticationService(user_repository, redis_service)

async def get_token_payload(request: Request) -> TokenPayload:
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return jwt_service.verify_token(cookie_token)

