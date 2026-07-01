# Contributing

Thanks for your interest in improving **django-live-operations**.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/iplweb/django-live-operations
cd django-live-operations
uv sync --extra dev --extra redis --extra celery --extra cli
```

## Running the tests

```bash
uv run pytest            # full suite
uv run ruff check .      # lint
uv run mkdocs build --strict   # docs
```

The round-trip tests spin a real Redis via
[testcontainers](https://testcontainers.com/) and therefore need a running
Docker daemon. If Docker is unavailable they skip with a clear reason.

Three test tiers:

- **Consumer** — `channels` `WebsocketCommunicator` against an in-memory layer.
- **`Progress`** — a fake channel layer captures `group_send` calls.
- **Round-trip** — worker → real Redis channel layer → consumer.

## Trying it in a browser

```bash
make demo         # docker compose: redis + ASGI + celery worker + seeded login
make demo-text    # text/tqdm mode, no infrastructure
```

## Conventions

- Code style: `ruff` (line length 88). Run `ruff format`/`ruff check`; a
  `pre-commit` config is provided (`pre-commit install`).
- Security: never build HTML by interpolating data into raw strings — render
  through Django templates (autoescaped) or `format_html`/`escape`. `html()`
  is a documented trusted-HTML escape hatch only.
- Every behavioural change ships with a test.
- Keep the package free of application-specific coupling — it must import
  only Django / channels / channels-broadcast.

## Pull requests

1. Branch from `main`.
2. Add tests; keep the suite green and `ruff` clean.
3. Update `CHANGELOG.md` (Unreleased) and the docs where relevant.
