# Generic imports
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Local imports
import core.views

urlpatterns = [
    path("", core.views.index, name="index"),
    path(
        "annotationDisplay=<int:annot_id>",
        core.views.annotation_display,
        name="annotation_display",
    ),
    path(
        "assignSamplesToUser",
        core.views.assign_samples_to_user,
        name="assign_samples_to_user",
    ),
    path("Contact", core.views.contact, name="contact"),
    path("cookie-consent/", core.views.cookie_consent, name="cookie_consent"),
    path("cookie-policy/", core.views.cookie_policy, name="cookie_policy"),
    path("intranet/", core.views.intranet, name="intranet"),
    path(
        "laboratoryContact/",
        core.views.laboratory_contact,
        name="laboratory_contact",
    ),
    path("metadataForm", core.views.metadata_form, name="metadataForm"),
    path(
        "metadataVisualization/",
        core.views.metadata_visualization,
        name="metadataVisualization",
    ),
    path(
        "organismAnnotation",
        core.views.organism_annotation,
        name="organism_annotation",
    ),
    path(
        "sampleDisplay=<int:sample_id>",
        core.views.sample_display,
        name="sample_display",
    ),
    path("receivedSamples", core.views.received_samples, name="received_samples"),
    path(
        "schemaDisplay=<int:schema_id>",
        core.views.schema_display,
        name="schema_display",
    ),
    path("schemaHandling", core.views.schema_handling, name="schema_handling"),
    path("searchSample", core.views.search_sample, name="search_sample"),
    path(
        "searchSample/data",
        core.views.search_sample_data,
        name="search_sample_data",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
