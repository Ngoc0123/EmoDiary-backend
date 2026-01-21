import random
import string
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException
from app.utils import jwt_service
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.redis_service import RedisService
from app.schemas.token import Token, TokenPayload
from typing import Any
from app.utils.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
otp_prefix = "otp"
otp_attemps_prefix = "otp_attemps"
otp_resend_cooldown_prefix = "otp_resend_cooldown"

class AuthenticationService:
    def __init__(self, user_repository: UserRepository, redis_service: RedisService):
        self.user_repository = user_repository
        self.redis_service = redis_service

    async def create_user(self, user_in: UserCreate) -> User:
        user = await self.user_repository.get_by_email(user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        
        user = User(
            email=user_in.email,
            hashed_password=self.get_password_hash(user_in.password),
            is_active=True,
            is_verified=False
        )
        user = await self.user_repository.save(user)

        #################### Activate Account ####################
        # Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        
        # Store in Redis
        otp_key = f"{otp_prefix}:{user.id}"
        await self.redis_service.set_value(otp_key, otp_code, expire_seconds=settings.OTP_EXPIRE_SECONDS)

        # Rate limit protection
        otp_attemps_key = f"{otp_attemps_prefix}:{user.id}"
        await self.redis_service.set_value(otp_attemps_key, 0, expire_seconds=settings.OTP_ATTEMPS_EXPIRE_SECONDS)
        # Generate Magic Link
        magic_link_token = jwt_service.create_magic_link_token(user.id)
        # Assuming frontend URL or API URL. For now using API URL.
        magic_link_url = f"{settings.DOMAIN}/api/v1/login/verify-magic-link?token={magic_link_token}"

        # Mock Email Dispatch
        print(f"==================================================")
        print(f"Sending Email to {user.email}")
        print(f"Subject: Activate your account")
        print(f"OTP Code: {otp_code}")
        print(f"Magic Link: {magic_link_url}")
        print(f"==================================================")

        return user

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.user_repository.get_by_email(email)
        if not user or not  self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        elif not user.is_verified:
            raise HTTPException(status_code=400, detail="User is not verified")
        elif not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=jwt_service.create_access_token(
                user.id, 
                expires_delta=access_token_expires,
                extra_claims={"is_verified": user.is_verified, "is_active": user.is_active}
            ),
            token_type="bearer",
        )

    async def verify_otp(self, email: str, code: str) -> Any:
        user = await self.user_repository.get_by_email(email)
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
        
        otp_key = f"{otp_prefix}:{user.id}"
        stored_otp = await self.redis_service.get_value(otp_key)
        
        if not stored_otp or stored_otp != code:
             raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        await self.redis_service.delete_value(otp_key)
        
        user.is_verified = True
        await self.user_repository.save(user)
        
        return {"message": "Account verified successfully"}

    async def resend_otp(self, email: str) -> Any:
        #Check if user email exist
        user = await self.user_repository.get_by_email(email)
        if not user:
             raise HTTPException(status_code=404, detail="User not found")

        #Check if user is verified
        if user.is_verified:
             raise HTTPException(status_code=400, detail="User is already verified")
        
        # Check for resend cooldown
        otp_resend_cooldown_key = f"{otp_resend_cooldown_prefix}:{user.id}"
        if await self.redis_service.get_value(otp_resend_cooldown_key):
             raise HTTPException(status_code=400, detail=f"Please wait {settings.OTP_RESEND_COOLDOWN_SECONDS} seconds before resending OTP")

        # Check for resend attemps
        otp_attemps_key = f"{otp_attemps_prefix}:{user.id}"
        attemps = await self.redis_service.get_value(otp_attemps_key)
        
        current_attemps = int(attemps) if attemps else 0
        if current_attemps >= 5:
             raise HTTPException(status_code=400, detail="Too many resend attemps")
        
        # Set cooldown
        await self.redis_service.set_value(otp_resend_cooldown_key, 1, expire_seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
        
        #Generate new OTP
        await self.redis_service.set_value(otp_attemps_key, current_attemps + 1, expire_seconds=settings.OTP_ATTEMPS_EXPIRE_SECONDS)
        otp_key = f"{otp_prefix}:{user.id}"
        await self.redis_service.delete_value(otp_key)
        
        otp_code = "".join(random.choices(string.digits, k=6))
        await self.redis_service.set_value(otp_key, otp_code, expire_seconds=settings.OTP_EXPIRE_SECONDS)
        
        print(f"==================================================")
        print(f"Sending Email to {user.email}")
        print(f"Subject: Activate your account")
        print(f"OTP Code: {otp_code}")
        print(f"==================================================")
        
        return {"message": "OTP resent successfully"}


    async def verify_magic_link(self, token: str) -> Any:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            if payload.get("scope") != "activation":
                 raise HTTPException(status_code=403, detail="Invalid token scope")
        except (jwt.JWTError, ValidationError):
             raise HTTPException(status_code=403, detail="Invalid token")

        user = await self.user_repository.get_by_id(token_data.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_verified = True
        await self.user_repository.save(user)
        
        return {"message": "Account verified successfully"}



    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

