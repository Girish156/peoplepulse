"""
Role-based access control (RBAC) for PeoplePulse.

Roles
-----
- admin          : Full platform access.
- hr_partner     : Read/write access to all employees and review data.
- manager        : Access to their direct reports only.
- peer_reviewer  : Can submit peer feedback when invited.
- employee       : Access to their own data only.
- it_operations  : Read-only access to audit logs and system health.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.config import settings
from app.core.security import DEMO_USERS, verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------
ALL_ROLES: Set[str] = {
    "admin",
    "hr_partner",
    "manager",
    "peer_reviewer",
    "employee",
    "it_operations",
}

# ---------------------------------------------------------------------------
# Permission matrix (role -> set of permission strings)
# ---------------------------------------------------------------------------
_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "view_employee",
        "edit_employee",
        "create_review",
        "submit_review",
        "view_all_employees",
        "manage_cycles",
        "view_admin_reports",
        "manage_issues",
        "view_audit",
        "generate_data",
    },
    "hr_partner": {
        "view_employee",
        "edit_employee",
        "create_review",
        "submit_review",
        "view_all_employees",
        "manage_cycles",
        "view_admin_reports",
        "manage_issues",
        "view_audit",
    },
    "manager": {
        "view_employee",
        "create_review",
        "submit_review",
        "view_audit",
    },
    "peer_reviewer": {
        "submit_review",
    },
    "employee": {
        "view_employee",
        "submit_review",
    },
    "it_operations": {
        "view_audit",
        "view_admin_reports",
    },
}


def _has_permission(role: str, permission: str) -> bool:
    return permission in _ROLE_PERMISSIONS.get(role, set())


# ---------------------------------------------------------------------------
# High-level permission checks
# ---------------------------------------------------------------------------

def can_view_employee(user: Dict[str, Any], target_employee_id: Optional[str] = None) -> bool:
    """
    Admins and HR partners can view any employee.
    Managers can view their direct reports (checked separately via DB).
    Employees can view themselves.
    """
    role = user.get("role", "")
    if role in ("admin", "hr_partner"):
        return True
    if role == "manager":
        return True  # further restriction via direct-report check
    if role == "employee":
        return target_employee_id is None or target_employee_id == user.get("employee_id")
    return False


def can_edit_employee(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "edit_employee")


def can_create_review(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "create_review")


def can_submit_review(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "submit_review")


def can_view_all_employees(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "view_all_employees")


def can_manage_cycles(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "manage_cycles")


def can_view_admin_reports(user: Dict[str, Any]) -> bool:
    return _has_permission(user.get("role", ""), "view_admin_reports")


def is_direct_report(manager_employee_id: str, target_employee_id: str, db_session) -> bool:
    """
    Return True if *target_employee_id* is a direct report of *manager_employee_id*.

    This performs a DB query to check the employee.manager_id relationship.
    Accepts a SQLAlchemy session; import Employee inside to avoid circular deps.
    """
    from app.models.employee import Employee  # deferred import

    target = (
        db_session.query(Employee)
        .filter(Employee.employee_id == target_employee_id)
        .first()
    )
    if target is None:
        return False
    if target.manager is None:
        return False
    return target.manager.employee_id == manager_employee_id


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Decode the bearer token and return the current user payload dict.

    Raises HTTP 401 if the token is missing, invalid, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
    except JWTError:
        raise credentials_exception

    email: Optional[str] = payload.get("sub")
    if email is None:
        raise credentials_exception

    # In demo mode resolve user details from the in-memory store
    if settings.DEMO_MODE:
        user = DEMO_USERS.get(email.lower())
        if user is None:
            raise credentials_exception
        return {
            "email": user["email"],
            "role": user["role"],
            "name": user["name"],
            "employee_id": user["employee_id"],
        }

    # Production: resolve from DB (payload must carry role info)
    return {
        "email": email,
        "role": payload.get("role", "employee"),
        "name": payload.get("name", ""),
        "employee_id": payload.get("employee_id", ""),
    }


def require_role(roles: List[str]):
    """
    Dependency factory — raises HTTP 403 unless the current user has one of *roles*.

    Usage::

        @router.get("/admin")
        def admin_endpoint(user=Depends(require_role(["admin", "hr_partner"]))):
            ...
    """

    def _checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {roles}",
            )
        return user

    return _checker


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Shorthand dependency — requires admin role."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return user
