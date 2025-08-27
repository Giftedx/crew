# Plugin Capability Testing

Plugins must prove their behaviour through a small suite of capability
scenarios described in the `tests` block of `manifest.json`.  Each
scenario specifies minimal inputs and simple predicates that the plugin
must satisfy when executed in a sandbox with stubbed service adapters.

The test runner can be invoked with:

```bash
python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin <module>
```

It imports the plugin, runs its self‑test entrypoint and then iterates
through the declared scenarios.  Any failures are reported with a non‑zero
exit code so they can be hooked into CI or marketplace publish checks.
