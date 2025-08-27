# Threat Model

This project considers threats such as unauthorized access to privileged commands,
server-side request forgery and abuse via excessive requests. Mitigations include
role-based access controls, a network guard to block private addresses, and an
in-memory token bucket rate limiter.
