from django.contrib.auth import get_user_model, login
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect

from demo.forms import DemoImportForm
from demo.models import DemoImport
from live_operations.views import (
    CancelView,
    CreateLiveOperationView,
    LiveOperationListView,
    LiveOperationView,
    RestartView,
)


class CreateDemoImportView(CreateLiveOperationView):
    model = DemoImport
    form_class = DemoImportForm
    template_name = "demo/demo_import_create.html"


class LiveDemoImportView(LiveOperationView):
    model = DemoImport


class ListDemoImportView(LiveOperationListView):
    model = DemoImport


class CancelDemoImportView(CancelView):
    model = DemoImport


class RestartDemoImportView(RestartView):
    model = DemoImport


def healthz_view(request):
    """Liveness probe for the Docker healthcheck.

    Deliberately does no DB writes, no template render, and no login — unlike
    /__login__/, which would create a new session row on every poll. Plain 200.
    """
    return HttpResponse("ok", content_type="text/plain")


def autologin_view(request):
    """Dev-only: log in as the first superuser without a password prompt."""
    if not __debug__:
        return HttpResponseForbidden("Not available in production.")

    from django.conf import settings

    if not settings.DEBUG:
        return HttpResponseForbidden("Not available when DEBUG=False.")

    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if user is None:
        return HttpResponseForbidden("No superuser found. Run: manage.py seed_demo")

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect(request.GET.get("next", "/"))
