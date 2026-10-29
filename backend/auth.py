import os
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from backend.database import db

users_collection = db["users"]

Password_hash = PasswordHash.recommended()
barer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def hash_password(password: str)->str:
    """Hash a password before storing it."""
    return Password_hash.hash(password)
def verify_password(password:str,hashed_password:str)->bool:
    """verify a password against its scored hash."""
    return Password_hash.verify(password, hashed_password)

def create_access_token(user_id: str)-> str:
    """Create a signed JWT for a authenticated user."""
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KET is not configured.")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM,)

async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(barer_scheme),) ->dict[str, Any]:
    """Validate the JWT and return its corresponding MongoDB user."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token.",
        headers= {"WWW-authenticate": "Bearer"},
    )

    if credentials is None or not JWT_SECRET_KEY:
        raise unauthorized

    try:
        payload =jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]}
        )
        user_id = payload.get("sub")

        if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
            raise unauthorized
        
    except jwt.InvalidTokenError:
        raise unauthorized
    user = await users_collection.find_one(
        {"_id": ObjectId(user_id)}
    )

    if user is None:
        raise unauthorized
    return user