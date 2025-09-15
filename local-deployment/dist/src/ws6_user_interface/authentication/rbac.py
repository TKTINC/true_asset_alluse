"""
Role-Based Access Control (RBAC)

This module implements the role-based access control system for the
True-Asset-ALLUSE platform, defining user roles and their permissions.
"""

from enum import Enum

class Role(Enum):
    """User roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    TRADER = "trader"
    VIEWER = "viewer"


class RBAC:
    """
    Role-Based Access Control system.
    """
    
    def __init__(self):
        self.permissions = {
            Role.ADMIN: {
                "users:create",
                "users:read",
                "users:update",
                "users:delete",
                "trading:execute",
                "reporting:generate"
            },
            Role.MANAGER: {
                "users:read",
                "trading:execute",
                "reporting:generate"
            },
            Role.TRADER: {
                "trading:execute"
            },
            Role.VIEWER: {
                "reporting:generate"
            }
        }
    
    def has_permission(self, role: Role, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return permission in self.permissions.get(role, set())


rbac = RBAC()


