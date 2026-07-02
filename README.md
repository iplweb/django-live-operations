# django-live-operations

A standalone, reusable Django package for long-running operations with a live
WebSocket + HTMX user interface — no page reloads, no polling.

The developer writes one method:

```python
from live_operations.models import LiveOperation
from live_operations.progress import Progress


class MyImport(LiveOperation):
    def run(self, p: Progress):
        for row in p.track(rows, label="Processing"):
            process(row)
            p.log(f"done: {row}")
        p.result()
```

The framework handles channels, tokens, OOB-swaps, snapshot-on-connect,
throttling, and cooperative cancellation.

## Try the demo

A self-contained demo project lives in [`example/`](example/).

```bash
# Browser demo — Daphne + Redis + Celery worker, live WebSocket progress.
# Opens http://localhost:8000 (needs Docker).
make demo

# Zero-infra text demo — runs synchronously, prints progress to stdout.
# No Docker, no Redis, no browser.
make demo-text
```

Both targets also work from inside `example/` (`cd example && make demo`);
the root `make` just delegates there. See [`example/README.md`](example/README.md)
for what you'll see and how the demo is wired.

## Documentation

Full docs are published at
**<https://iplweb.github.io/django-live-operations/>** (source in `docs/`).
