from uuid import UUID
from fastapi import HTTPException
from app.models.user import User
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
