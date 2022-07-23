from django.urls import path
from django.conf import settings
from relecov_documentation import views
from django.conf.urls.static import static

from django.urls import include

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "createUserAccount/",
        views.create_user_account,
        name="create_user_account",
    ),
    path(
        "initialConfiguration",
        views.initial_configuration,
        name="initial_configuration",
    ),
    path("Intranet/", views.intranet, name="intranet"),
    path("Dashboard/", views.dashboard, name="dashboard"),
    path("markdownx/", include("markdownx.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
