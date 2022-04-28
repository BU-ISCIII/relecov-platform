from django.urls import path
from django.conf import settings
from relecov_core import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("variants", views.variants, name="variants"),
    path("documentation", views.documentation, name="documentation"),
    path("relecovForm", views.relecov_form, name="relecovForm"),
    path("intranet/", views.intranet, name="intranet"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
