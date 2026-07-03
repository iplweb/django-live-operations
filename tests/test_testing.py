"""Tests for liveops.testing.MockProgress — the consumer test double."""

import pytest
from django.contrib.auth import get_user_model

from liveops.progress import OperationCancelled
from liveops.testing import MockProgress
from tests.models import DemoOp, StagedOp

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="mp", password="pass")


@pytest.mark.django_db
def test_records_run_calls_and_finalizes(user):
    """DemoOp.run reports status/percent/log/result — all recorded, op saved."""
    op = DemoOp.objects.create(owner=user)
    p = MockProgress(op)

    op.run(p)

    assert ("Running DemoOp", "info") in p.statuses
    assert 50 in p.percents
    assert "step 1" in p.logs
    assert p.result_context == {"message": "done"}

    # result() finalized + persisted the operation.
    op.refresh_from_db()
    assert op.finished_successfully is True
    assert op.result_context == {"message": "done"}
    assert op.finished_on is not None


@pytest.mark.django_db
def test_track_yields_items_and_records_percent(user):
    op = DemoOp.objects.create(owner=user)
    p = MockProgress(op)

    got = list(p.track([10, 20, 30]))

    assert got == [10, 20, 30]
    # int(n * 100 / total) for total=3 → 33, 66, 100 (no throttling).
    assert p.percents == [33, 66, 100]


@pytest.mark.django_db
def test_cancel_after_raises_in_track(user):
    op = DemoOp.objects.create(owner=user)
    p = MockProgress(op, cancel_after=2)

    consumed = []
    with pytest.raises(OperationCancelled):
        for item in p.track([1, 2, 3, 4]):
            consumed.append(item)

    # track() checks cancellation before each yield; the 3rd check raises.
    assert consumed == [1, 2]


@pytest.mark.django_db
def test_error_records_and_finalizes(user):
    op = DemoOp.objects.create(owner=user)
    p = MockProgress(op)

    p.error("boom")

    assert p.error_message == "boom"
    op.refresh_from_db()
    assert op.finished_successfully is False
    assert op.traceback == "boom"


@pytest.mark.django_db
def test_records_stage_names(user):
    op = StagedOp.objects.create(owner=user)
    p = MockProgress(op)

    op.run(p)

    assert p.stages_entered == ["Alpha", "Beta", "Gamma"]
    assert p.result_context == {"stage_result": "complete"}


@pytest.mark.django_db
def test_pkless_operation_is_not_saved(user):
    """An unsaved (in-memory) operation gets attrs set but no DB write."""
    op = DemoOp(owner=user)  # not .create()d → _state.adding is True
    p = MockProgress(op)

    p.result({"x": 1})

    assert op.finished_successfully is True
    assert op.result_context == {"x": 1}
    # Nothing was persisted.
    assert not DemoOp.objects.filter(pk=op.pk).exists()
