# Turn logs (`turns.jsonl`)

Local-only JSONL of AI page turns for offline cross-check.

- **Path:** `data/turn_logs/turns.jsonl` (gitignored)
- **Schema:** `finfit_youth.turn_log` — `schema: 1`
- **Disable:** set env `FINFIT_TURN_LOG=0`
- **Does not store:** API keys, full secrets, full tool dumps (args are digests)

## One-line inspect (PowerShell)

```powershell
Get-Content data\turn_logs\turns.jsonl -Tail 3
```

## Python

```python
import json
from pathlib import Path
for line in Path("data/turn_logs/turns.jsonl").read_text(encoding="utf-8").splitlines()[-5:]:
    print(json.loads(line)["query"], json.loads(line)["plan"])
```
