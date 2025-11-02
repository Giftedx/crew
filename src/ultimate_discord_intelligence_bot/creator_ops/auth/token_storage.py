"""
Token storage for OAuth tokens with encryption.

This module provides secure storage and retrieval of OAuth tokens
with encryption, expiration tracking, and audit logging.
"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from ultimate_discord_intelligence_bot.creator_ops.auth.vault import SecretsVault
from ultimate_discord_intelligence_bot.creator_ops.models.schema import Account, BaseModel
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


class TokenStorage:
    """Secure token storage with encryption and database persistence."""

    def __init__(self, database_url: str, encryption_key: str | None = None, vault: SecretsVault | None = None) -> None:
        """Initialize token storage.

        Args:
            database_url: Database connection URL
            encryption_key: Encryption key for tokens
            vault: Secrets vault instance
        """
        self.database_url = database_url
        self.vault = vault or SecretsVault(encryption_key)
        self.engine = create_engine(database_url, echo=False)
        BaseModel.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def store_tokens(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        user_id: str | None,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
        scope: str | None,
        handle: str | None = None,
        display_name: str | None = None,
    ) -> StepResult:
        """Store OAuth tokens securely.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            access_token: Access token
            refresh_token: Refresh token
            expires_at: Token expiration time
            scope: Granted scopes
            handle: Platform handle
            display_name: Display name

        Returns:
            StepResult indicating success or failure
        """
        session = self._get_session()
        try:
            encrypted_access_token = self.vault.encrypt_secret(access_token)
            encrypted_refresh_token = None
            if refresh_token:
                encrypted_refresh_token = self.vault.encrypt_secret(refresh_token)
            account = (
                session.query(Account)
                .filter_by(tenant=tenant, workspace=workspace, platform=platform, platform_id=user_id or "")
                .first()
            )
            if account:
                account.access_token_encrypted = encrypted_access_token
                account.refresh_token_encrypted = encrypted_refresh_token
                account.token_expires_at = expires_at
                account.oauth_scopes = scope
                if handle:
                    account.handle = handle
                if display_name:
                    account.display_name = display_name
                account.updated_at = datetime.utcnow()
            else:
                account = Account(
                    tenant=tenant,
                    workspace=workspace,
                    platform=platform,
                    handle=handle or "",
                    display_name=display_name,
                    platform_id=user_id or "",
                    oauth_scopes=scope,
                    access_token_encrypted=encrypted_access_token,
                    refresh_token_encrypted=encrypted_refresh_token,
                    token_expires_at=expires_at,
                    is_active=True,
                )
                session.add(account)
            session.commit()
            logger.info(f"Stored tokens for {platform} account {user_id} in {tenant}/{workspace}")
            return StepResult.ok(
                data={"account_id": account.id, "platform": platform, "user_id": user_id, "expires_at": expires_at}
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store tokens: {e!s}")
            return StepResult.fail(f"Token storage failed: {e!s}")
        finally:
            session.close()

    def get_tokens(self, platform: str, tenant: str, workspace: str, user_id: str | None = None) -> StepResult:
        """Get stored tokens.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID

        Returns:
            StepResult with token data
        """
        session = self._get_session()
        try:
            query = session.query(Account).filter_by(tenant=tenant, workspace=workspace, platform=platform)
            if user_id:
                query = query.filter_by(platform_id=user_id)
            account = query.first()
            if not account:
                return StepResult.fail(f"No tokens found for {platform} in {tenant}/{workspace}")
            if not account.access_token_encrypted:
                return StepResult.fail(f"No access token found for {platform} account")
            access_token = self.vault.decrypt_secret(account.access_token_encrypted)
            refresh_token = None
            if account.refresh_token_encrypted:
                refresh_token = self.vault.decrypt_secret(account.refresh_token_encrypted)
            is_expired = False
            if account.token_expires_at and account.token_expires_at <= datetime.utcnow():
                is_expired = True
            logger.info(f"Retrieved tokens for {platform} account {account.platform_id}")
            return StepResult.ok(
                data={
                    "account_id": account.id,
                    "platform": platform,
                    "user_id": account.platform_id,
                    "handle": account.handle,
                    "display_name": account.display_name,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": account.token_expires_at,
                    "is_expired": is_expired,
                    "scope": account.oauth_scopes,
                    "is_active": account.is_active,
                }
            )
        except Exception as e:
            logger.error(f"Failed to get tokens: {e!s}")
            return StepResult.fail(f"Token retrieval failed: {e!s}")
        finally:
            session.close()

    def update_tokens(
        self,
        account_id: int,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> StepResult:
        """Update stored tokens.

        Args:
            account_id: Account ID
            access_token: New access token
            refresh_token: New refresh token
            expires_at: New expiration time

        Returns:
            StepResult indicating success or failure
        """
        session = self._get_session()
        try:
            account = session.query(Account).filter_by(id=account_id).first()
            if not account:
                return StepResult.fail(f"Account {account_id} not found")
            if access_token:
                account.access_token_encrypted = self.vault.encrypt_secret(access_token)
            if refresh_token:
                account.refresh_token_encrypted = self.vault.encrypt_secret(refresh_token)
            if expires_at:
                account.token_expires_at = expires_at
            account.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated tokens for account {account_id}")
            return StepResult.ok(data={"account_id": account_id})
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update tokens: {e!s}")
            return StepResult.fail(f"Token update failed: {e!s}")
        finally:
            session.close()

    def delete_tokens(self, platform: str, tenant: str, workspace: str, user_id: str | None = None) -> StepResult:
        """Delete stored tokens.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID

        Returns:
            StepResult indicating success or failure
        """
        session = self._get_session()
        try:
            query = session.query(Account).filter_by(tenant=tenant, workspace=workspace, platform=platform)
            if user_id:
                query = query.filter_by(platform_id=user_id)
            account = query.first()
            if not account:
                return StepResult.fail(f"No tokens found for {platform} in {tenant}/{workspace}")
            account.access_token_encrypted = None
            account.refresh_token_encrypted = None
            account.token_expires_at = None
            account.is_active = False
            account.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Deleted tokens for {platform} account {account.platform_id}")
            return StepResult.ok(data={"account_id": account.id})
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete tokens: {e!s}")
            return StepResult.fail(f"Token deletion failed: {e!s}")
        finally:
            session.close()

    def list_accounts(
        self, tenant: str, workspace: str, platform: str | None = None, active_only: bool = True
    ) -> StepResult:
        """List stored accounts.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            platform: Filter by platform
            active_only: Only return active accounts

        Returns:
            StepResult with account list
        """
        session = self._get_session()
        try:
            query = session.query(Account).filter_by(tenant=tenant, workspace=workspace)
            if platform:
                query = query.filter_by(platform=platform)
            if active_only:
                query = query.filter_by(is_active=True)
            accounts = query.all()
            account_list = []
            for account in accounts:
                account_data = {
                    "id": account.id,
                    "platform": account.platform,
                    "handle": account.handle,
                    "display_name": account.display_name,
                    "platform_id": account.platform_id,
                    "has_tokens": bool(account.access_token_encrypted),
                    "expires_at": account.token_expires_at,
                    "is_expired": account.token_expires_at and account.token_expires_at <= datetime.utcnow(),
                    "is_active": account.is_active,
                    "created_at": account.created_at,
                    "updated_at": account.updated_at,
                }
                account_list.append(account_data)
            return StepResult.ok(data={"accounts": account_list})
        except Exception as e:
            logger.error(f"Failed to list accounts: {e!s}")
            return StepResult.fail(f"Account listing failed: {e!s}")
        finally:
            session.close()

    def cleanup_expired_tokens(self, tenant: str, workspace: str) -> StepResult:
        """Clean up expired tokens.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with cleanup results
        """
        session = self._get_session()
        try:
            expired_accounts = (
                session.query(Account)
                .filter_by(tenant=tenant, workspace=workspace, is_active=True)
                .filter(Account.token_expires_at <= datetime.utcnow())
                .all()
            )
            cleaned_count = 0
            for account in expired_accounts:
                account.is_active = False
                account.updated_at = datetime.utcnow()
                cleaned_count += 1
            session.commit()
            logger.info(f"Cleaned up {cleaned_count} expired tokens in {tenant}/{workspace}")
            return StepResult.ok(data={"cleaned_count": cleaned_count})
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e!s}")
            return StepResult.fail(f"Token cleanup failed: {e!s}")
        finally:
            session.close()

    def get_expiring_tokens(self, tenant: str, workspace: str, days_ahead: int = 7) -> StepResult:
        """Get tokens expiring within specified days.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            days_ahead: Days ahead to check

        Returns:
            StepResult with expiring tokens
        """
        session = self._get_session()
        try:
            cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
            expiring_accounts = (
                session.query(Account)
                .filter_by(tenant=tenant, workspace=workspace, is_active=True)
                .filter(Account.token_expires_at <= cutoff_date, Account.token_expires_at > datetime.utcnow())
                .all()
            )
            expiring_list = []
            for account in expiring_accounts:
                expiring_data = {
                    "id": account.id,
                    "platform": account.platform,
                    "handle": account.handle,
                    "display_name": account.display_name,
                    "expires_at": account.token_expires_at,
                    "has_refresh_token": bool(account.refresh_token_encrypted),
                }
                expiring_list.append(expiring_data)
            return StepResult.ok(data={"expiring_tokens": expiring_list})
        except Exception as e:
            logger.error(f"Failed to get expiring tokens: {e!s}")
            return StepResult.fail(f"Expiring tokens retrieval failed: {e!s}")
        finally:
            session.close()
