# Cost Guards and Caching

This project enforces per-request cost limits and caches expensive results.

* **Cost guard** – `token_meter.cost_guard` estimates the USD cost of a call and
  raises `BudgetError` if it would exceed `COST_MAX_PER_REQUEST` or the daily
  budget. The budget is charged only after successful completion.
* **Router preflight** – `router.preflight` iterates over candidate models and
  picks the first one that fits the cost guard, enabling automatic downshifts to
  cheaper models.
* **Caches** – `core.cache.llm_cache` and `core.cache.retrieval_cache` offer
  simple in-memory TTL caches. They are enabled when the `ENABLE_CACHE` flag is
  set.

These controls keep spend predictable and latency low while remaining easy to
extend with more advanced policies.
