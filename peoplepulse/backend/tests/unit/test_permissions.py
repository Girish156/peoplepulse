"""
Unit tests for security, roles, and permissions.
"""

from app.core.security import create_access_token, verify_token, DEMO_USERS
from app.core.permissions import can_view_all_employees, can_manage_cycles

def test_token_creation_and_verification():
    data = {"sub": "admin@peoplepulse.demo", "role": "admin", "employee_id": "EMP-000001"}
    token = create_access_token(data)
    decoded = verify_token(token)
    assert decoded["sub"] == "admin@peoplepulse.demo"
    assert decoded["role"] == "admin"
    assert decoded["employee_id"] == "EMP-000001"

def test_demo_users_roles():
    assert DEMO_USERS["admin@peoplepulse.demo"]["role"] == "admin"
    assert DEMO_USERS["hr@peoplepulse.demo"]["role"] == "hr_partner"
    assert DEMO_USERS["manager@peoplepulse.demo"]["role"] == "manager"
    assert DEMO_USERS["employee@peoplepulse.demo"]["role"] == "employee"

def test_permission_helpers():
    admin = {"role": "admin"}
    hr = {"role": "hr_partner"}
    emp = {"role": "employee"}

    assert can_view_all_employees(admin) is True
    assert can_view_all_employees(hr) is True
    assert can_view_all_employees(emp) is False

    assert can_manage_cycles(admin) is True
    assert can_manage_cycles(hr) is True
    assert can_manage_cycles(emp) is False

