.PHONY: test docs demo demo-text

test:
	uv run pytest

docs:
	uv run mkdocs build

# Demo targets delegate to example/Makefile (single source of truth); the demo
# is a self-contained project under example/.
demo:
	$(MAKE) -C example demo

demo-text:
	$(MAKE) -C example demo-text
