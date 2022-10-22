from relecov_core.models import PublicDatabaseValues
from relecov_core.utils.plotly_graphics import bullet_graphic


def get_gisaid_accession_from_sample_lab(sample_objs):
    """Get the list of the accesion values with their sample"""
    gisaid_acc = (
        PublicDatabaseValues.objects.filter(
            sampleID__in=sample_objs,
            public_database_fieldID__property_name__exact="gisaid_accession_id",
        )
        .exclude(value="Not Provided")
        .values_list("sampleID__sequencing_sample_id", "value")
    )
    return gisaid_acc


def get_ena_accession_from_sample_lab(sample_objs):
    ena_acc = (
        PublicDatabaseValues.objects.filter(
            sampleID__in=sample_objs,
            public_database_fieldID__property_name__exact="ena_sample_accession",
        )
        .exclude(value="Not Provided")
        .values_list("sampleID__sequencing_sample_id", "value")
    )
    return ena_acc


def percentage_graphic(len_sample, len_acc, title):

    return bullet_graphic(round(len_acc / len_sample, 2) * 100, title)
