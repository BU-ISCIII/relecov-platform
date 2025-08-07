from django.db.models import Q
from django.contrib.auth.models import Group

import core.models
import core.serializers
import core.config
import core.utils.labs
import core.utils.generic_functions


def get_search_data(user_obj):
    """Structure data to render form in search sample view."""
    if core.models.Sample.objects.count() == 0:
        return {"ERROR": core.config.ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED}

    states_qs = core.models.SampleState.objects.all()
    serialized_states = core.serializers.SampleStateSerializer(
        states_qs, many=True
    ).data

    group = Group.objects.get(name="RelecovManager")
    if group in user_obj.groups.all():
        labs = core.utils.labs.get_all_defined_labs()
        if isinstance(labs, dict) and "ERROR" in labs:
            labs = ["", ""]
    else:
        labs = [core.utils.labs.get_lab_name_from_user(user_obj)]

    return {"labs": labs, "states": serialized_states}


def validate_search_params(sample_name, lab_name, sample_state, s_date):
    """Validates search parameters and returns warnings if applicable."""
    if not any([sample_name, lab_name, sample_state, s_date]):
        return {"warning": "You must fill in at least one field to search."}
    if s_date and not core.utils.generic_functions.check_valid_date_format(s_date):
        return {"warning": core.config.ERROR_INVALID_DEFINED_SAMPLE_FORMAT}
    return {}


def display_samples(sample_name, lab_name, sample_state, s_date, user):
    """Search for samples and return serialized results."""
    result = {"data": {}, "success": False, "errors": []}

    samples_qs = core.models.Sample.objects.all()

    if lab_name:
        samples_qs = samples_qs.filter(collecting_institution__iexact=lab_name)

    if sample_name:
        exact_qs = samples_qs.filter(
            Q(sequencing_sample_id__iexact=sample_name)
            | Q(collecting_lab_sample_id__iexact=sample_name)
        )
        if exact_qs.exists():
            samples_qs = exact_qs
        else:
            partial_qs = samples_qs.filter(
                Q(sequencing_sample_id__icontains=sample_name)
                | Q(collecting_lab_sample_id__icontains=sample_name)
            )
            if partial_qs.exists():
                samples_qs = partial_qs
            else:
                result["data"] = {
                    "samples": [],
                    "heading": core.config.HEADING_FOR_SAMPLE_LIST,
                    "redirect": None,
                }
                result["errors"].append(core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH)
                return result

    if sample_state:
        sample_ids = core.models.SampleStateHistory.objects.filter(
            state_id__pk=sample_state
        ).values_list("sample__pk", flat=True)
        samples_qs = samples_qs.filter(pk__in=sample_ids)

    if s_date:
        samples_qs = samples_qs.filter(created_at__exact=s_date)

    if not samples_qs.exists():
        result["data"] = {
            "samples": [],
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
            "redirect": None,
        }
        result["errors"].append(core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH)
        return result

    if samples_qs.count() == 1:
        result["data"] = {
            "samples": [],
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
            "redirect": samples_qs.first().pk,
        }
        result["success"] = True
        return result

    serialized = core.serializers.SampleSearchResultSerializer(samples_qs, many=True).data

    result["data"] = {
        "samples": serialized,
        "heading": core.config.HEADING_FOR_SAMPLE_LIST,
        "redirect": None,
    }
    result["success"] = True
    return result
