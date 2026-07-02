from demo.views import autologin_view, healthz_view
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language view
    path("accounts/", include("django.contrib.auth.urls")),
    # Docker healthcheck endpoint (no side effects — see healthz_view).
    path("healthz/", healthz_view, name="healthz"),
    # demo.urls declares app_name="live_operations" — all liveop URL reversals work.
    path("", include("demo.urls")),
    path("__login__/", autologin_view, name="autologin"),
]
