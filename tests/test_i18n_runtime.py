"""
Regression tests: live fragments must render in the operation's language.

The worker / WS consumer that renders live progress has no request locale, so
without re-activating the operation's captured language the progress UI falls
back to English mid-run (stage stepper, status, log). runner.task_run must
re-activate ``operation.language`` around ``run()``.
"""

import io

import pytest
from django.contrib.auth import get_user_model
from django.utils import translation

from live_operations import runner
from live_operations.progress import TextProgress
from tests.models import DemoOp

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="lang-user", password="x")


def test_task_run_activates_operation_language(user):
    """Even when the ambient language is English, task_run runs the operation
    under the language captured at enqueue."""
    op = DemoOp.objects.create(owner=user, language="pl")

    captured = {}

    def probe(p):
        captured["lang"] = translation.get_language()

    op.run = probe  # instance-level override

    with translation.override("en"):  # simulate a worker defaulting to English
        runner.task_run(op, TextProgress(op, io.StringIO()))

    assert captured["lang"] == "pl"


def test_task_run_without_language_leaves_ambient(user):
    """No captured language → don't override the ambient language."""
    op = DemoOp.objects.create(owner=user, language="")

    captured = {}

    def probe(p):
        captured["lang"] = translation.get_language()

    op.run = probe

    with translation.override("de"):
        runner.task_run(op, TextProgress(op, io.StringIO()))

    assert captured["lang"] == "de"


def test_enqueue_captures_active_language(user, settings):
    """enqueue() (called in a request) records the active language so the
    worker can re-activate it."""
    settings.LIVE_OPERATIONS = {"RUNNER": "eager"}
    op = DemoOp.objects.create(owner=user)

    with translation.override("uk"):
        op.enqueue()

    op.refresh_from_db()
    assert op.language == "uk"
