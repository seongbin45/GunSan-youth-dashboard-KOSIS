# Agent state store

`FinFitAgent` persists per-`user_id` JSON here:

```text
data/agent_state/agent_state_{user_id}.json
```

- **Do not commit** these files (see root `.gitignore`).
- Legacy files used to live in the project root as `agent_state_*.json`.
  On first load the agent **copies** a matching root file into this folder if the
  canonical path is missing (it does not auto-delete the root copy).
- Safe to delete individual files to reset a user; the app recreates them on save.
