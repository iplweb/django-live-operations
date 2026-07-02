.PHONY: demo demo-text

# Browser demo: Daphne (ASGI) + Redis channel layer + Celery worker.
# Opens http://localhost:8000 — see README.md.
demo:
	docker compose up --build

# Zero-infra text demo: run DemoImport synchronously in TextProgress mode.
# No Docker, no Redis, no browser needed.
demo-text:
	RUNNER=eager uv run python manage.py migrate --run-syncdb --noinput
	RUNNER=eager uv run python manage.py seed_demo
	RUNNER=eager uv run python manage.py run_liveop demo.DemoImport
