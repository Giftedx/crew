"""Cache dependency group definitions."""

# Core caching dependencies
CACHE_GROUP: set[str] = {
    "redis",
    "aioredis",
    "hiredis",
    "memcached",
    "pymemcache",
}

# Optional caching dependencies
CACHE_OPTIONAL: set[str] = {
    "diskcache",
    "cachetools",
    "beaker",
    "dogpile.cache",
}
