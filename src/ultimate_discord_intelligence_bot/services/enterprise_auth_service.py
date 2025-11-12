"""Enterprise authentication service with SSO, RBAC, and API key management."""

from __future__ import annotations

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum

import bcrypt
import jwt

from app.config.settings import ENABLE_ENTERPRISE_TENANT_MANAGEMENT
from ultimate_discord_intelligence_bot.step_result import StepResult


log = logging.getLogger(__name__)


class AuthProvider(Enum):
    """Supported authentication providers."""

    LOCAL = "local"
    OAUTH2 = "oauth2"
    SAML = "saml"
    OIDC = "oidc"
    LDAP = "ldap"


class UserRole(Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"


class Permission(Enum):
    """System permissions."""

    CREATE_TENANT = "create_tenant"
    MANAGE_TENANT = "manage_tenant"
    DELETE_TENANT = "delete_tenant"
    CREATE_USER = "create_user"
    MANAGE_USER = "manage_user"
    DELETE_USER = "delete_user"
    MANAGE_RESOURCES = "manage_resources"
    VIEW_RESOURCES = "view_resources"
    CREATE_AGENT = "create_agent"
    MANAGE_AGENT = "manage_agent"
    DELETE_AGENT = "delete_agent"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_ALERTS = "manage_alerts"
    API_READ = "api_read"
    API_WRITE = "api_write"
    API_ADMIN = "api_admin"


@dataclass
class User:
    """User entity."""

    user_id: str
    email: str
    username: str
    full_name: str
    tenant_id: str
    roles: set[UserRole] = field(default_factory=set)
    permissions: set[Permission] = field(default_factory=set)
    auth_provider: AuthProvider = AuthProvider.LOCAL
    external_id: str | None = None
    is_active: bool = True
    is_verified: bool = False
    created_at: float = field(default_factory=time.time)
    last_login: float | None = None
    password_hash: str | None = None
    mfa_enabled: bool = False
    mfa_secret: str | None = None


@dataclass
class APIKey:
    """API key entity."""

    key_id: str
    key_hash: str
    user_id: str
    tenant_id: str
    name: str
    description: str
    permissions: set[Permission] = field(default_factory=set)
    expires_at: float | None = None
    last_used: float | None = None
    usage_count: int = 0
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    created_by: str = ""


@dataclass
class Session:
    """User session."""

    session_id: str
    user_id: str
    tenant_id: str
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400)
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True


class EnterpriseAuthService:
    """Enterprise authentication service with SSO and RBAC support."""

    def __init__(self, jwt_secret: str = "default_secret_change_in_production"):
        """Initialize enterprise auth service."""
        self.enabled = ENABLE_ENTERPRISE_TENANT_MANAGEMENT
        self.jwt_secret = jwt_secret
        self.users: dict[str, User] = {}
        self.api_keys: dict[str, APIKey] = {}
        self.sessions: dict[str, Session] = {}
        self.role_permissions: dict[UserRole, set[Permission]] = {}
        if self.enabled:
            log.info("Enterprise Auth Service initialized")
            self._initialize_default_permissions()
        else:
            log.info("Enterprise Auth Service disabled via feature flag")

    def _initialize_default_permissions(self) -> StepResult:
        """Initialize default role-permission mappings."""
        self.role_permissions = {
            UserRole.SUPER_ADMIN: {
                Permission.CREATE_TENANT,
                Permission.MANAGE_TENANT,
                Permission.DELETE_TENANT,
                Permission.CREATE_USER,
                Permission.MANAGE_USER,
                Permission.DELETE_USER,
                Permission.MANAGE_RESOURCES,
                Permission.VIEW_RESOURCES,
                Permission.CREATE_AGENT,
                Permission.MANAGE_AGENT,
                Permission.DELETE_AGENT,
                Permission.VIEW_ANALYTICS,
                Permission.MANAGE_ALERTS,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.API_ADMIN,
            },
            UserRole.TENANT_ADMIN: {
                Permission.MANAGE_TENANT,
                Permission.CREATE_USER,
                Permission.MANAGE_USER,
                Permission.MANAGE_RESOURCES,
                Permission.VIEW_RESOURCES,
                Permission.CREATE_AGENT,
                Permission.MANAGE_AGENT,
                Permission.DELETE_AGENT,
                Permission.VIEW_ANALYTICS,
                Permission.MANAGE_ALERTS,
                Permission.API_READ,
                Permission.API_WRITE,
            },
            UserRole.USER: {
                Permission.VIEW_RESOURCES,
                Permission.MANAGE_AGENT,
                Permission.VIEW_ANALYTICS,
                Permission.API_READ,
            },
            UserRole.VIEWER: {Permission.VIEW_RESOURCES, Permission.VIEW_ANALYTICS, Permission.API_READ},
            UserRole.API_USER: {Permission.API_READ, Permission.API_WRITE},
        }

    def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        tenant_id: str,
        password: str | None = None,
        roles: set[UserRole] | None = None,
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        external_id: str | None = None,
    ) -> StepResult:
        """Create a new user."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        try:
            user_id = f"user_{int(time.time() * 1000)}_{secrets.token_hex(4)}"
            if not email or not username or (not tenant_id):
                return StepResult.fail("Email, username, and tenant_id are required")
            if any(user.email == email or user.username == username for user in self.users.values()):
                return StepResult.fail("User with this email or username already exists")
            if roles is None:
                roles = {UserRole.USER}
            password_hash = None
            if password and auth_provider == AuthProvider.LOCAL:
                password_hash = self._hash_password(password)
            user = User(
                user_id=user_id,
                email=email,
                username=username,
                full_name=full_name,
                tenant_id=tenant_id,
                roles=roles,
                auth_provider=auth_provider,
                external_id=external_id,
                password_hash=password_hash,
            )
            user.permissions = self._get_permissions_for_roles(roles)
            self.users[user_id] = user
            log.info(f"Created user {user_id} ({email}) for tenant {tenant_id}")
            return StepResult.ok(
                data={
                    "user_id": user_id,
                    "email": email,
                    "username": username,
                    "tenant_id": tenant_id,
                    "roles": [role.value for role in roles],
                    "permissions": [perm.value for perm in user.permissions],
                }
            )
        except Exception as e:
            log.error(f"Failed to create user: {e}")
            return StepResult.fail(f"Failed to create user: {e}")

    def _hash_password(self, password: str) -> StepResult:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> StepResult:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def _get_permissions_for_roles(self, roles: set[UserRole]) -> StepResult:
        """Get all permissions for given roles."""
        permissions = set()
        for role in roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        return permissions

    def authenticate_user(self, email: str, password: str, tenant_id: str) -> StepResult:
        """Authenticate user with email and password."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        try:
            user = None
            for u in self.users.values():
                if u.email == email and u.tenant_id == tenant_id and (u.auth_provider == AuthProvider.LOCAL):
                    user = u
                    break
            if not user:
                return StepResult.fail("Invalid credentials")
            if not user.is_active:
                return StepResult.fail("User account is inactive")
            if not user.password_hash:
                return StepResult.fail("No password set for user")
            if not self._verify_password(password, user.password_hash):
                return StepResult.fail("Invalid credentials")
            user.last_login = time.time()
            session = self._create_session(user)
            token = self._generate_jwt_token(user, session)
            log.info(f"User {user.user_id} authenticated successfully")
            return StepResult.ok(
                data={
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "tenant_id": tenant_id,
                    "session_id": session.session_id,
                    "token": token,
                    "expires_at": session.expires_at,
                    "roles": [role.value for role in user.roles],
                    "permissions": [perm.value for perm in user.permissions],
                }
            )
        except Exception as e:
            log.error(f"Authentication failed: {e}")
            return StepResult.fail(f"Authentication failed: {e}")

    def _create_session(self, user: User) -> StepResult:
        """Create a new session for user."""
        session_id = f"session_{int(time.time() * 1000)}_{secrets.token_hex(8)}"
        session = Session(session_id=session_id, user_id=user.user_id, tenant_id=user.tenant_id)
        self.sessions[session_id] = session
        return session

    def _generate_jwt_token(self, user: User, session: Session) -> StepResult:
        """Generate JWT token for user session."""
        payload = {
            "user_id": user.user_id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "session_id": session.session_id,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "iat": int(time.time()),
            "exp": int(session.expires_at),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_token(self, token: str) -> StepResult:
        """Verify JWT token and return user information."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            if not user_id or not session_id:
                return StepResult.fail("Invalid token")
            user = self.users.get(user_id)
            if not user or not user.is_active:
                return StepResult.fail("User not found or inactive")
            session = self.sessions.get(session_id)
            if not session or not session.is_active or session.expires_at < time.time():
                return StepResult.fail("Session expired or invalid")
            return StepResult.ok(
                data={
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "tenant_id": user.tenant_id,
                    "session_id": session_id,
                    "roles": [role.value for role in user.roles],
                    "permissions": [perm.value for perm in user.permissions],
                }
            )
        except jwt.ExpiredSignatureError:
            return StepResult.fail("Token expired")
        except jwt.InvalidTokenError:
            return StepResult.fail("Invalid token")
        except Exception as e:
            log.error(f"Token verification failed: {e}")
            return StepResult.fail(f"Token verification failed: {e}")

    def create_api_key(
        self,
        user_id: str,
        name: str,
        description: str,
        permissions: set[Permission] | None = None,
        expires_at: float | None = None,
    ) -> StepResult:
        """Create a new API key for a user."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        try:
            user = self.users.get(user_id)
            if not user:
                return StepResult.fail("User not found")
            if not user.is_active:
                return StepResult.fail("User is inactive")
            key_value = f"ak_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(key_value.encode()).hexdigest()
            if permissions is None:
                permissions = user.permissions.copy()
            api_key = APIKey(
                key_id=f"key_{int(time.time() * 1000)}_{secrets.token_hex(4)}",
                key_hash=key_hash,
                user_id=user_id,
                tenant_id=user.tenant_id,
                name=name,
                description=description,
                permissions=permissions,
                expires_at=expires_at,
                created_by=user_id,
            )
            self.api_keys[api_key.key_id] = api_key
            log.info(f"Created API key {api_key.key_id} for user {user_id}")
            return StepResult.ok(
                data={
                    "key_id": api_key.key_id,
                    "key_value": key_value,
                    "name": name,
                    "description": description,
                    "permissions": [perm.value for perm in permissions],
                    "expires_at": expires_at,
                }
            )
        except Exception as e:
            log.error(f"Failed to create API key: {e}")
            return StepResult.fail(f"Failed to create API key: {e}")

    def verify_api_key(self, api_key: str) -> StepResult:
        """Verify API key and return user information."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            api_key_record = None
            for key in self.api_keys.values():
                if key.key_hash == key_hash and key.is_active:
                    api_key_record = key
                    break
            if not api_key_record:
                return StepResult.fail("Invalid API key")
            if api_key_record.expires_at and api_key_record.expires_at < time.time():
                return StepResult.fail("API key expired")
            user = self.users.get(api_key_record.user_id)
            if not user or not user.is_active:
                return StepResult.fail("User not found or inactive")
            api_key_record.last_used = time.time()
            api_key_record.usage_count += 1
            return StepResult.ok(
                data={
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "tenant_id": user.tenant_id,
                    "key_id": api_key_record.key_id,
                    "permissions": [perm.value for perm in api_key_record.permissions],
                    "usage_count": api_key_record.usage_count,
                }
            )
        except Exception as e:
            log.error(f"API key verification failed: {e}")
            return StepResult.fail(f"API key verification failed: {e}")

    def check_permission(self, user_id: str, permission: Permission) -> StepResult:
        """Check if user has a specific permission."""
        if not self.enabled:
            return StepResult.ok(data={"has_permission": True})
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return StepResult.fail("User not found or inactive")
        has_permission = permission in user.permissions
        return StepResult.ok(
            data={
                "has_permission": has_permission,
                "user_id": user_id,
                "permission": permission.value,
                "user_roles": [role.value for role in user.roles],
            }
        )

    def update_user_roles(self, user_id: str, roles: set[UserRole]) -> StepResult:
        """Update user roles and permissions."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        user = self.users.get(user_id)
        if not user:
            return StepResult.fail("User not found")
        try:
            old_roles = user.roles.copy()
            user.roles = roles
            user.permissions = self._get_permissions_for_roles(roles)
            log.info(f"Updated roles for user {user_id}: {[r.value for r in old_roles]} -> {[r.value for r in roles]}")
            return StepResult.ok(
                data={
                    "user_id": user_id,
                    "old_roles": [role.value for role in old_roles],
                    "new_roles": [role.value for role in roles],
                    "new_permissions": [perm.value for perm in user.permissions],
                }
            )
        except Exception as e:
            log.error(f"Failed to update user roles: {e}")
            return StepResult.fail(f"Failed to update user roles: {e}")

    def get_user_by_id(self, user_id: str) -> StepResult:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_users_by_tenant(self, tenant_id: str) -> StepResult:
        """Get all users for a tenant."""
        return [user for user in self.users.values() if user.tenant_id == tenant_id and user.is_active]

    def deactivate_api_key(self, key_id: str) -> StepResult:
        """Deactivate an API key."""
        if not self.enabled:
            return StepResult.fail("Enterprise auth service disabled")
        api_key = self.api_keys.get(key_id)
        if not api_key:
            return StepResult.fail("API key not found")
        api_key.is_active = False
        log.info(f"Deactivated API key {key_id}")
        return StepResult.ok(data={"key_id": key_id, "status": "deactivated"})

    def logout_user(self, session_id: str) -> StepResult:
        """Logout user by invalidating session."""
        if not self.enabled:
            return StepResult.ok(data={"logged_out": True})
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            log.info(f"User logged out, session {session_id} invalidated")
        return StepResult.ok(data={"session_id": session_id, "logged_out": True})

    def get_auth_stats(self) -> StepResult:
        """Get authentication service statistics."""
        if not self.enabled:
            return {"enabled": False}
        active_users = len([u for u in self.users.values() if u.is_active])
        active_sessions = len([s for s in self.sessions.values() if s.is_active])
        active_api_keys = len([k for k in self.api_keys.values() if k.is_active])
        return {
            "enabled": True,
            "total_users": len(self.users),
            "active_users": active_users,
            "active_sessions": active_sessions,
            "total_api_keys": len(self.api_keys),
            "active_api_keys": active_api_keys,
        }


_auth_service: EnterpriseAuthService | None = None


def get_auth_service() -> StepResult:
    """Get the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = EnterpriseAuthService()
    return _auth_service


def authenticate_user(email: str, password: str, tenant_id: str) -> StepResult:
    """Authenticate user."""
    service = get_auth_service()
    return service.authenticate_user(email, password, tenant_id)


def verify_token(token: str) -> StepResult:
    """Verify JWT token."""
    service = get_auth_service()
    return service.verify_token(token)


def verify_api_key(api_key: str) -> StepResult:
    """Verify API key."""
    service = get_auth_service()
    return service.verify_api_key(api_key)


def check_permission(user_id: str, permission: Permission) -> StepResult:
    """Check user permission."""
    service = get_auth_service()
    return service.check_permission(user_id, permission)
