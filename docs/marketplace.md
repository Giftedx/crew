# Plugin Marketplace

This document outlines the marketplace layer used to distribute sandboxed
plugins across tenants.  The initial implementation ships the following
building blocks:

- **Data model** – SQLite tables (`mp_repos`, `mp_plugins`, `mp_signers`,
  `mp_releases`, `mp_advisories`, `mp_installs`, `mp_rollouts`) managed by
  :class:`MarketplaceStore`.
- **Signing helpers** – `verify_manifest` checks SHA256 signatures against
  registered signers and ensures they are valid and not revoked.
- **Trust tier policies** – helpers that clamp plugin capabilities and resource
  quotas based on declared trust tier.

## Trust Tiers

Plugins are assigned a **trust tier** when published or installed.  The tier
determines which capabilities the plugin may request and the maximum resources
(cpu and memory) it may consume.  The tiers are, from lowest to highest trust:

- `untrusted`
- `community`
- `verified`
- `partner`
- `first_party`

Lower tiers receive strict limits and may have many capabilities stripped.  The
`first_party` tier is unrestricted and intended only for internally audited
plugins.

Use the helpers in `ultimate_discord_intelligence_bot.marketplace.trust` to
apply these limits before enabling a plugin.
