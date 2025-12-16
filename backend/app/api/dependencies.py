"""Dependencies for API endpoints."""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db import database, crud
from app.core.security import decode_access_token
from app.db.models import User
from app.core.permissions import RoleID

ADMIN_KEY = "dev-admin-key-change-in-production"


def get_current_user(
    db: Session = Depends(database.get_db),
    authorization: Optional[str] = Header(None),
) -> User:
    """Get current authenticated user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_optional_current_user(
    db: Session = Depends(database.get_db),
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        payload = decode_access_token(token)
        if payload is None:
            return None
        email = payload.get("sub")
        if email is None:
            return None
        user = crud.get_user_by_email(db, email=email)
        return user if user and user.is_active else None
    except:
        return None


def get_admin_user(
    current_user: User = Depends(get_current_user),
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY"),
) -> User:
    """System Admin only (role_id=1)"""
    if x_admin_key == ADMIN_KEY:
        return current_user
    if current_user.is_admin or current_user.role_id == RoleID.SYSTEM_ADMIN:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System Admin access required")


def get_hr_or_admin_user(
    current_user: User = Depends(get_current_user),
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY"),
) -> User:
    """HR or System Admin access"""
    if x_admin_key == ADMIN_KEY:
        return current_user
    if current_user.is_admin or current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HR or Admin access required")


def get_manager_user(current_user: User = Depends(get_current_user)) -> User:
    """Line Manager, Delivery Manager, HR, or Admin"""
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR, RoleID.DELIVERY_MANAGER, RoleID.LINE_MANAGER]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")


def get_cp_user(current_user: User = Depends(get_current_user)) -> User:
    """Capability Partner, HR, or Admin"""
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR, RoleID.CAPABILITY_PARTNER]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capability Partner access required")


def require_roles(*allowed_roles: int):
    """Dependency factory for requiring specific roles"""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_id in allowed_roles or current_user.is_admin:
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return checker
