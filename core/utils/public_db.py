# Local imports
import core.models
import core.utils.plotly_graphics
import dashboard.utils.generic_graphic_data
from django.db.models import Q


def get_public_accession_from_sample_lab(p_field, sample_objs=None):
    """Get the list of the accesion values with their sample.
    If not samples are given it gets the information for all samples
    """
    if sample_objs is None:
        return (
            core.models.PublicDatabaseValues.objects.filter(
                public_database_fieldID__property_name__iexact=p_field,
            )
            .exclude(Q(value__icontains="Not Provided") | Q(value__isnull=True))
            .values_list(
                "sampleID__submitting_institution",
                "sampleID__sequencing_sample_id",
                "value",
            )
        )
    else:
        return (
            core.models.PublicDatabaseValues.objects.filter(
                sampleID__in=sample_objs,
                public_database_fieldID__property_name__exact=p_field,
            )
            .exclude(Q(value__icontains="Not Provided") | Q(value__isnull=True))
            .values_list("sampleID__sequencing_sample_id", "value")
        )


def percentage_graphic(len_sample, len_acc, title):
    """Display Pie graphic with upload samples as len_acc and not upload as the
    difference from total sample minus the ones that are uploaded
    """
    data = [len_acc, len_sample - len_acc]
    names = ["Upload", "Pending"]
    return core.utils.plotly_graphics.pie_graphic(data, names, title)


def get_public_information_from_sample(p_type, sample_id):
    """Return all values that are stored for the sample and for the public type"""
    if core.models.PublicDatabaseValues.objects.filter(
        sampleID__pk=sample_id,
        public_database_fieldID__database_type__public_type_name__iexact=p_type,
    ).exists():
        return core.models.PublicDatabaseValues.objects.filter(
            sampleID__pk=sample_id,
            public_database_fieldID__database_type__public_type_name__iexact=p_type,
        ).values_list("public_database_fieldID__label_name", "value")
    return []


def get_preprocessed_gisaid_data():
    """Load preprocessed gisaid data in graphic_json table"""
    gisaid_data = (
        dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "intranet_gisaid_data"
        )
    )
    if gisaid_data is None:
        # Execute the pre-processed task to get the data
        result = (
            dashboard.utils.generic_process_data.pre_proc_intranet_gisaid_data()
        )
        if "ERROR" in result:
            return result
        gisaid_data = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "intranet_gisaid_data"
            )
        )
    return gisaid_data


def get_preprocessed_ena_data():
    """Load preprocessed ena data in graphic_json table"""
    ena_data = (
        dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "intranet_ena_data"
        )
    )
    if ena_data is None:
        # Execute the pre-processed task to get the data
        result = (
            dashboard.utils.generic_process_data.pre_proc_intranet_ena_data()
        )
        if "ERROR" in result:
            return result
        ena_data = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "intranet_ena_data"
            )
        )
    return ena_data
