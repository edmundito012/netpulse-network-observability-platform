from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token

class UserService:

    @staticmethod
    def create_user(db: Session, user_data: UserCreate):

        existing_email = UserRepository.get_by_email(
            db,
            user_data.email
        )

        if existing_email:
            raise ValueError("Email already registered")

        existing_username = UserRepository.get_by_username(
            db,
            user_data.username
        )

        if existing_username:
            raise ValueError("Username already exists")

        hashed_password = hash_password(user_data.password)

        return UserRepository.create(
            db=db,
            user_data=user_data,
            hashed_password=hashed_password
        )
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):

        user = UserRepository.get_by_email(db, email)

        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Inactive user")

        token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role.value,
                "user_id": user.id
            }
        )

        return token