"""
OAuth scope validation and management.

This module provides scope validation, audit trails, and compliance checking
for OAuth scopes across all supported platforms.
"""

from __future__ import annotations

import logging
from platform.core.step_result import StepResult
from typing import Any


logger = logging.getLogger(__name__)


class ScopeValidator:
    """OAuth scope validation and audit."""

    def __init__(self) -> None:
        """Initialize scope validator."""
        self.required_scopes = {
            "youtube": {
                "readonly": ["https://www.googleapis.com/auth/youtube.readonly"],
                "full": [
                    "https://www.googleapis.com/auth/youtube",
                    "https://www.googleapis.com/auth/youtube.force-ssl",
                ],
            },
            "twitch": {
                "basic": ["user:read:email"],
                "streamer": ["user:read:email", "channel:read:stream_key"],
                "moderator": ["user:read:email", "moderator:read:chatters"],
                "full": [
                    "user:read:email",
                    "channel:read:stream_key",
                    "moderator:read:chatters",
                    "channel:manage:broadcast",
                ],
            },
            "tiktok": {
                "basic": ["user.info.basic"],
                "content": ["user.info.basic", "video.list"],
                "publish": ["user.info.basic", "video.publish"],
            },
            "instagram": {
                "basic": ["instagram_basic"],
                "insights": ["instagram_basic", "instagram_manage_insights"],
                "content": ["instagram_basic", "instagram_manage_insights", "instagram_manage_comments"],
            },
            "x": {
                "read": ["tweet.read", "users.read"],
                "write": ["tweet.read", "users.read", "tweet.write", "users.write"],
                "full": ["tweet.read", "users.read", "tweet.write", "users.write", "offline.access"],
            },
        }
        self.scope_descriptions = {
            "https://www.googleapis.com/auth/youtube.readonly": "Read YouTube channel and video data",
            "https://www.googleapis.com/auth/youtube": "Full access to YouTube channel",
            "https://www.googleapis.com/auth/youtube.force-ssl": "Force HTTPS for YouTube API calls",
            "user:read:email": "Read user email address",
            "channel:read:stream_key": "Read channel stream key",
            "moderator:read:chatters": "Read chat messages",
            "channel:manage:broadcast": "Manage channel broadcasts",
            "user.info.basic": "Read basic user information",
            "video.list": "List user videos",
            "video.publish": "Publish videos",
            "instagram_basic": "Read Instagram profile and media",
            "instagram_manage_insights": "Read Instagram insights and analytics",
            "instagram_manage_comments": "Manage Instagram comments",
            "tweet.read": "Read tweets and timelines",
            "users.read": "Read user profiles",
            "tweet.write": "Post and delete tweets",
            "users.write": "Update user profile",
            "offline.access": "Access account when user is offline",
        }
        self.sensitive_scopes = {
            "youtube": ["https://www.googleapis.com/auth/youtube"],
            "twitch": ["channel:manage:broadcast"],
            "tiktok": ["video.publish"],
            "instagram": ["instagram_manage_comments"],
            "x": ["tweet.write", "users.write"],
        }

    def validate_scopes(self, platform: str, requested_scopes: list[str], purpose: str) -> StepResult:
        """Validate requested scopes for a platform.

        Args:
            platform: Platform name
            requested_scopes: List of requested scopes
            purpose: Purpose of the scope request (readonly, content_management, etc.)

        Returns:
            StepResult with validation results
        """
        try:
            if platform not in self.required_scopes:
                return StepResult.fail(f"Unknown platform: {platform}")
            if purpose not in self.required_scopes[platform]:
                return StepResult.fail(f"Unknown purpose '{purpose}' for platform {platform}")
            required_scopes = set(self.required_scopes[platform][purpose])
            requested_scopes_set = set(requested_scopes)
            missing_scopes = required_scopes - requested_scopes_set
            if missing_scopes:
                return StepResult.fail(f"Missing required scopes for {purpose}: {', '.join(missing_scopes)}")
            all_valid_scopes = set()
            for purpose_scopes in self.required_scopes[platform].values():
                all_valid_scopes.update(purpose_scopes)
            unknown_scopes = requested_scopes_set - all_valid_scopes
            if unknown_scopes:
                logger.warning(f"Unknown scopes requested for {platform}: {', '.join(unknown_scopes)}")
            sensitive_requested = requested_scopes_set.intersection(set(self.sensitive_scopes.get(platform, [])))
            return StepResult.ok(
                data={
                    "valid": True,
                    "platform": platform,
                    "purpose": purpose,
                    "requested_scopes": requested_scopes,
                    "missing_scopes": list(missing_scopes),
                    "unknown_scopes": list(unknown_scopes),
                    "sensitive_scopes": list(sensitive_requested),
                    "requires_special_approval": len(sensitive_requested) > 0,
                }
            )
        except Exception as e:
            logger.error(f"Scope validation failed: {e!s}")
            return StepResult.fail(f"Scope validation error: {e!s}")

    def get_scope_descriptions(self, scopes: list[str]) -> dict[str, str]:
        """Get descriptions for scopes.

        Args:
            scopes: List of scope strings

        Returns:
            Dictionary mapping scopes to descriptions
        """
        descriptions = {}
        for scope in scopes:
            descriptions[scope] = self.scope_descriptions.get(scope, "Unknown scope")
        return descriptions

    def audit_scope_request(
        self,
        platform: str,
        requested_scopes: list[str],
        purpose: str,
        tenant: str,
        workspace: str,
        user_id: str | None = None,
    ) -> StepResult:
        """Audit a scope request for compliance.

        Args:
            platform: Platform name
            requested_scopes: List of requested scopes
            purpose: Purpose of the scope request
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID

        Returns:
            StepResult with audit results
        """
        try:
            validation_result = self.validate_scopes(platform, requested_scopes, purpose)
            if not validation_result.success:
                return validation_result
            validation_data = validation_result.data
            audit_record = {
                "timestamp": str(
                    logger.handlers[0].formatter.formatTime(logger.makeRecord("", 0, "", 0, "", (), None))
                ),
                "platform": platform,
                "tenant": tenant,
                "workspace": workspace,
                "user_id": user_id,
                "purpose": purpose,
                "requested_scopes": requested_scopes,
                "scope_descriptions": self.get_scope_descriptions(requested_scopes),
                "validation_result": validation_data,
                "compliance_status": "compliant" if validation_data["valid"] else "non_compliant",
                "requires_approval": validation_data.get("requires_special_approval", False),
            }
            logger.info(f"OAuth scope audit: {audit_record}")
            compliance_issues = []
            if validation_data.get("missing_scopes"):
                compliance_issues.append("Missing required scopes")
            if validation_data.get("unknown_scopes"):
                compliance_issues.append("Unknown scopes requested")
            if validation_data.get("requires_special_approval"):
                compliance_issues.append("Sensitive scopes require special approval")
            return StepResult.ok(
                data={
                    "audit_record": audit_record,
                    "compliance_issues": compliance_issues,
                    "requires_manual_review": len(compliance_issues) > 0,
                }
            )
        except Exception as e:
            logger.error(f"Scope audit failed: {e!s}")
            return StepResult.fail(f"Scope audit error: {e!s}")

    def get_minimal_scopes(self, platform: str, purpose: str) -> list[str]:
        """Get minimal required scopes for a purpose.

        Args:
            platform: Platform name
            purpose: Purpose (readonly, basic, etc.)

        Returns:
            List of minimal required scopes
        """
        if platform not in self.required_scopes:
            return []
        if purpose not in self.required_scopes[platform]:
            return []
        return self.required_scopes[platform][purpose].copy()

    def is_scope_sensitive(self, platform: str, scope: str) -> bool:
        """Check if a scope is sensitive.

        Args:
            platform: Platform name
            scope: Scope string

        Returns:
            True if scope is sensitive
        """
        return scope in self.sensitive_scopes.get(platform, [])

    def get_platform_compliance_summary(self, platform: str) -> dict[str, Any]:
        """Get compliance summary for a platform.

        Args:
            platform: Platform name

        Returns:
            Compliance summary dictionary
        """
        if platform not in self.required_scopes:
            return {"error": f"Unknown platform: {platform}"}
        purposes = list(self.required_scopes[platform].keys())
        sensitive_scopes = self.sensitive_scopes.get(platform, [])
        return {
            "platform": platform,
            "available_purposes": purposes,
            "sensitive_scopes": sensitive_scopes,
            "total_scopes": len(set().union(*self.required_scopes[platform].values())),
            "compliance_requirements": {
                "minimal_scopes": {purpose: self.get_minimal_scopes(platform, purpose) for purpose in purposes},
                "sensitive_scope_approval_required": len(sensitive_scopes) > 0,
            },
        }

    def validate_scope_consistency(
        self, platform: str, stored_scopes: list[str], requested_scopes: list[str]
    ) -> StepResult:
        """Validate consistency between stored and requested scopes.

        Args:
            platform: Platform name
            stored_scopes: Previously granted scopes
            requested_scopes: Newly requested scopes

        Returns:
            StepResult with consistency validation
        """
        try:
            stored_set = set(stored_scopes)
            requested_set = set(requested_scopes)
            new_scopes = requested_set - stored_set
            removed_scopes = stored_set - requested_set
            sensitive_new = new_scopes.intersection(set(self.sensitive_scopes.get(platform, [])))
            return StepResult.ok(
                data={
                    "consistent": True,
                    "new_scopes": list(new_scopes),
                    "removed_scopes": list(removed_scopes),
                    "sensitive_new_scopes": list(sensitive_new),
                    "requires_approval": len(sensitive_new) > 0,
                    "scope_expansion": len(new_scopes) > 0,
                    "scope_reduction": len(removed_scopes) > 0,
                }
            )
        except Exception as e:
            logger.error(f"Scope consistency validation failed: {e!s}")
            return StepResult.fail(f"Scope consistency validation error: {e!s}")
