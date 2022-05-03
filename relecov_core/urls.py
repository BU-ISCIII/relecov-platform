from django.urls import path
from django.conf import settings
from relecov_core import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("documentation", views.documentation, name="documentation"),
    path("intranet/", views.intranet, name="intranet"),
    path("relecovForm", views.relecov_form, name="relecovForm"),
    path("variants", views.variants, name="variants"),
    path("schemaHandling", views.schema_handling, name="schema_handling"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
