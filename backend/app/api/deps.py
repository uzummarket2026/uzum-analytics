from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """JWT'dan user.id ni o'qib, foydalanuvchini qaytaradi.

    Eski (email'li) tokenlar ham orqaga moslik uchun qabul qilinadi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = None
    # Yangi format: sub = user.id (string)
    try:
        uid = int(sub)
        user = db.query(User).filter(User.id == uid).first()
    except (TypeError, ValueError):
        pass

    # Orqaga moslik: eski tokenlar email saqlagan
    if user is None and isinstance(sub, str) and "@" in sub:
        user = db.query(User).filter(User.email == sub).first()

    if user is None or not user.is_active:
        raise credentials_exception
    return user
