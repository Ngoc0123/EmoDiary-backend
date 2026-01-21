from fastapi import APIRouter, Depends
from app.api import deps
from app.schemas.token import TokenPayload
from app.services.authentication_service import AuthenticationService
from app.services.user_service import UserService

router = APIRouter()

from app.schemas.user import UserRead

@router.get("/me", response_model=UserRead)
async def read_user_me(
    payload: TokenPayload = Depends(deps.get_token_payload),
    user_service: UserService = Depends(deps.get_user_service),
) -> UserRead:
    """
    Get current user info from token.
    """
    return await user_service.get_user_by_id(payload.sub)