from django.urls import path
from django.conf import settings
from relecov_core import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "annotationDisplay=<int:annot_id>",
        views.annotation_display,
        name="annotation_display",
    ),
    path("Contact", views.contact, name="contact"),
    path("intranet/", views.intranet, name="intranet"),
    path("laboratoryContact/", views.laboratory_contact, name="laboratory_contact"),
    path("metadataForm", views.metadata_form, name="metadataForm"),
    path(
        "metadataVisualization/",
        views.metadata_visualization,
        name="metadataVisualization",
    ),
    path("sampleDisplay=<int:sample_id>", views.sample_display, name="sample_display"),
    path("schemaDisplay=<int:schema_id>", views.schema_display, name="schema_display"),
    path("schemaHandling", views.schema_handling, name="schema_handling"),
    path("searchSample", views.search_sample, name="search_sample"),
    path("virusAnnotation", views.virus_annotation, name="virus_annotation"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
