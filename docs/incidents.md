# Incidents

The incident helper provides a tiny in-memory tracker used by ops commands and
tests.  Incidents can be opened, acknowledged, and resolved:

```python
from obs import incident
inc_id = incident.manager.open("database down", severity="high")
incident.manager.ack(inc_id, "alice")
incident.manager.resolve(inc_id)
```

Discord operations expose wrappers such as `ops_incident_open` for automation.
