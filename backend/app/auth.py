from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, Tenant

import bcrypt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password[:72].encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(password[:72].encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise exc
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_tenant_from_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    db: Session = Depends(get_db)
) -> Tenant:
    """Resolve an active Tenant from the X-Api-Key header (used by embedded widgets)."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-Api-Key header is required")
    tenant = db.query(Tenant).filter(Tenant.api_key == x_api_key, Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return tenant

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized for this action."
            )
        return current_user

# ── Pre-built role guards ──────────────────────────────────────────────────────
require_super_admin   = RoleChecker(["super_admin"])
require_store_admin   = RoleChecker(["super_admin", "store_admin"])
require_agent_or_admin = RoleChecker(["super_admin", "store_admin", "agent"])
# Legacy alias — keep existing endpoints working
require_admin = RoleChecker(["super_admin", "store_admin"])
