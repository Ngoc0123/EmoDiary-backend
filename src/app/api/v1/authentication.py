from pydantic import EmailStr
from app.schemas.user import UserBase
from fastapi import APIRouter, Depends, Response
from typing import Any

#General import
from app.utils.config import settings
from app.api import deps

#Schema import
from app.schemas.user import UserCreate, UserRead
from app.schemas.otp import OTPVerify
from app.schemas.user import UserLogin

#Service import
from app.services.authentication_service import AuthenticationService


router = APIRouter()


@router.post("/register", response_model=UserRead)
async def create_user(
    *,
    user_in: UserCreate,
    auth_service: AuthenticationService = Depends(deps.get_auth_service),
) -> UserRead:
    """
    Create new user.
    """
    return await auth_service.create_user(user_in)

@router.post("/login", response_model=Any)
async def login(
    response: Response,
    user_in: UserLogin,
    auth_service: AuthenticationService = Depends(deps.get_auth_service),
) -> Any:
    """
    Login user and set access token in httpOnly cookie.
    """
    token = await auth_service.authenticate_user(user_in.email, user_in.password)
    
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,  # TODO: Set to True in production
    )
    
    return {"message": "Login successful"}


@router.post("/verify-otp")
async def verify_otp(
    otp_in: OTPVerify,
    auth_service: AuthenticationService = Depends(deps.get_auth_service),
) -> Any:
    """
    Verify OTP for account activation.
    """
    return await auth_service.verify_otp(otp_in.email, otp_in.code)

@router.post("/resend-otp")
async def resend_otp(
    email: EmailStr,
    auth_service: AuthenticationService = Depends(deps.get_auth_service),
) -> Any:
    """
    Resend OTP for user.
    """
    return await auth_service.resend_otp(email)


@router.get("/verify-magic-link")
async def verify_magic_link(
    token: str,
    auth_service: AuthenticationService = Depends(deps.get_auth_service),
) -> Any:
    """
    Verify Magic Link for account activation.
    """
    return await auth_service.verify_magic_link(token)


@router.post("/logout")
async def logout(response: Response) -> Any:
    """
    Logout user by deleting the access token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logout successful"}

