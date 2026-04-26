import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from database import fetch_one


SECRET_KEY = os.getenv("WS_SECRET_KEY", "worksphere-dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("WS_TOKEN_EXPIRE_MINUTES", "480"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> dict | None:
    query = """
        SELECT user_id, user_name, username, email, password_hash, role, is_active
        FROM users
        WHERE username = %s
        LIMIT 1
    """
    user = fetch_one(query, (username,))
    if not user or not user["is_active"]:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = fetch_one(
        """
        SELECT user_id, user_name, username, email, role, is_active
        FROM users
        WHERE user_id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    if not user or not user["is_active"]:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    def role_checker(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


CurrentUser = Annotated[dict, Depends(get_current_user)]
