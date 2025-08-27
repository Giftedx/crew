# Security Operations

This repository includes basic role-based access control and rate limiting helpers.

## RBAC

Use the :class:`security.rbac.RBAC` class to verify permissions. Decorate callables with
``@rbac.require('perm')`` and call them with a ``roles`` keyword argument.

## Rate limiting

The :class:`security.rate_limit.TokenBucket` class offers a simple in-memory token bucket
that can be used to throttle abusive callers.

## Network guard

Use :func:`security.net_guard.is_safe_url` before making outbound requests to
ensure URLs use public hosts and approved schemes.

## Secrets

Load credentials from environment variables using
``security.secrets.get_secret``. Use ``rotate_secret`` after rotating the
underlying value to refresh the in-memory cache.

## Moderation

The :class:`security.moderation.Moderation` helper scans text for banned
terms defined in ``config/security.yaml``. Depending on the configured action it
will redact or block offending content.
