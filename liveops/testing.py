"""
Test helpers for liveops consumers.

``MockProgress`` is a ``Progress`` double for unit-testing a
``LiveOperation.run(self, p)`` method without a channel layer, Redis, or a
worker. It:

- **records** every call — ``statuses``, ``logs``, ``percents``,
  ``stages_entered``, ``result_context``, ``error_message``, ``swaps``,
  ``htmls``, ``chained`` — so tests can assert on what ``run()`` reported;
- **finalizes** the operation on ``result()`` / ``error()`` (like
  ``TextProgress``): sets ``finished_on`` / ``finished_successfully`` /
  ``result_context`` (or ``traceback``) and saves them when the operation has
  a pk — so an end-to-end ``op.run(MockProgress(op))`` behaves naturally;
- does **no** transport (no WebSocket, no stdout), applies **no** throttling
  (every ``percent`` value is recorded), and does **no** DB read for
  cancellation.

Cancellation can be simulated with ``cancel_after=N``: the ``N+1``-th
``check_cancelled()`` (which ``track()`` calls once per item) raises
``OperationCancelled``.

Example::

    from liveops.testing import MockProgress

    def test_my_import_run():
        op = MyImport.objects.create(owner=user, ...)
        p = MockProgress(op)
        op.run(p)
        assert p.logs == ["row 1 ok", "row 2 ok"]
        assert p.result_context == {"total": 2}
        assert op.finished_successfully is True
"""

from __future__ import annotations

from typing import Any, Optional

from liveops.progress import OperationCancelled, Progress


class MockProgress(Progress):
    """Recording, transport-free ``Progress`` for unit tests. See module docs."""

    def __init__(self, operation: Any, *, cancel_after: Optional[int] = None) -> None:
        super().__init__(operation)
        self.statuses: list[tuple[str, str]] = []
        self.logs: list[str] = []
        self.percents: list[int] = []
        self.stages_entered: list[str] = []
        self.swaps: list[tuple[str, Optional[str], dict]] = []
        self.htmls: list[tuple[str, str, str]] = []
        self.chained: list[Any] = []
        self.result_context: Optional[dict] = None
        self.error_message: Optional[str] = None
        self._cancel_after = cancel_after
        self._cancel_checks = 0

    # ------------------------------------------------------------------ #
    # Core API — record instead of transmit                               #
    # ------------------------------------------------------------------ #

    def status(self, text: str, level: str = "info") -> None:
        self.statuses.append((text, level))

    def percent(self, value: int) -> None:
        # No throttling: record every value so assertions are deterministic.
        self.percents.append(int(value))

    def log(self, line: str) -> None:
        self.logs.append(line)

    def check_cancelled(self) -> None:
        self._cancel_checks += 1
        if self._cancel_after is not None and self._cancel_checks > self._cancel_after:
            raise OperationCancelled(
                f"MockProgress: cancelled after {self._cancel_after} check(s)"
            )

    def result(self, context: Optional[dict] = None, **extra: Any) -> None:
        ctx: dict = {} if context is None else dict(context)
        ctx.update(extra)
        self.result_context = ctx
        self._finalized = True
        self._apply_terminal(finished_successfully=True, result_context=ctx)

    def error(self, message: str) -> None:
        self.error_message = message
        self._finalized = True
        self._apply_terminal(finished_successfully=False, traceback=message)

    def chain_to(self, next_op: Any) -> None:
        # Record the chain target; do not run it (unit-test isolation).
        self.chained.append(next_op)
        self._finalized = True

    # ------------------------------------------------------------------ #
    # Stage hooks — record entered stage names                            #
    # ------------------------------------------------------------------ #

    def _on_stage_start(self, name: str, idx: int) -> None:
        self.stages_entered.append(name)

    # ------------------------------------------------------------------ #
    # Web-only helpers — record (base class raises NotImplementedError)   #
    # ------------------------------------------------------------------ #

    def swap(self, selector: str, name: Optional[str] = None, **ctx: Any) -> None:
        self.swaps.append((selector, name, ctx))

    def html(self, selector: str, raw: str, mode: str = "innerHTML") -> None:
        self.htmls.append((selector, raw, mode))

    # ------------------------------------------------------------------ #
    # Terminal state on the operation (mirrors TextProgress)              #
    # ------------------------------------------------------------------ #

    def _apply_terminal(self, **fields: Any) -> None:
        from django.utils import timezone

        op = self._operation
        op.finished_on = timezone.now()
        for key, value in fields.items():
            setattr(op, key, value)
        # Persist only for a real DB row. UUID pk defaults are assigned at
        # __init__, so ``pk is not None`` can't tell a saved row from a fresh
        # one — use ``_state.adding`` (False once saved/loaded). Pure in-memory
        # instances just get their attributes set, no save.
        if not op._state.adding:
            op.save(update_fields=["finished_on", *fields.keys()])
