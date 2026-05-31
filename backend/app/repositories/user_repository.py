from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(User).order_by(User.id.asc()).all()

    @staticmethod
    def get_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def create(db: Session, user_data: UserCreate, hashed_password: str):
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def update(
        db: Session,
        user: User,
        user_data: UserUpdate,
        hashed_password: str | None = None,
    ):
        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data.pop("password")

        for field, value in update_data.items():
            setattr(user, field, value)

        if hashed_password is not None:
            user.hashed_password = hashed_password

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete(db: Session, user: User):
        db.delete(user)
        db.commit()