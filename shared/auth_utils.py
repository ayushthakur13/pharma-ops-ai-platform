"""
Shared authentication utilities for all services.
Provides JWT validation and user context extraction.
"""

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from shared.config import settings
from shared.models.user import User, Role


def get_current_user(token: str, db: Session) -> tuple[User, str]:
    """
    Extract and validate user from JWT token.
    
    Returns:
        (User, role_name) tuple
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    # Get role name
    role = db.get(Role, user.role_id)
    role_name = role.name if role else "Unknown"
    
    return user, role_name


def require_role(required_roles: list[str]):
    """
    Decorator to enforce role-based access control.
    
    Args:
        required_roles: List of allowed role names (e.g., ["Pharmacist", "Manager"])
        
    Returns:
        Callable that validates user role before executing endpoint
    """
    def role_checker(user_info: tuple[User, str]) -> tuple[User, str]:
        user, role_name = user_info
        if role_name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This operation requires one of: {', '.join(required_roles)}"
            )
        return user, role_name
    return role_checker
