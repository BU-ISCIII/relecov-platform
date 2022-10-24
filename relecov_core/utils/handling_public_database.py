from relecov_core.models import PublicDatabaseValues
from relecov_core.utils.plotly_graphics import pie_graphic


def get_public_accession_from_sample_lab(p_field, sample_objs):
    """Get the list of the accesion values with their sample"""
    return (
        PublicDatabaseValues.objects.filter(
            sampleID__in=sample_objs,
            public_database_fieldID__property_name__exact=p_field,
        )
        .exclude(value="Not Provided")
        .values_list("sampleID__sequencing_sample_id", "value")
    )


def percentage_graphic(len_sample, len_acc, title):
    """Display Pie graphic with upload samples as len_acc and not upload as the
    difference from total sample minus the ones that are uploaded
    """
    data = [len_acc, len_sample - len_acc]
    names = ["Upload", "Pending"]
    return pie_graphic(data, names, title)


def get_public_information_from_sample(p_type, sample_id):
    """Return all values that are stored for the sample and for the public type"""
    if PublicDatabaseValues.objects.filter(
        sampleID__pk=sample_id,
        public_database_fieldID__database_type__public_type_name__iexact=p_type,
    ).exists():
        return PublicDatabaseValues.objects.filter(
            sampleID__pk=sample_id,
            public_database_fieldID__database_type__public_type_name__iexact=p_type,
        ).values_list("public_database_fieldID__label_name", "value")
    return []


def get_samples_upload_public_database(field_db, s_names=False):
    """Fetch the samples that are upload to public database, (ENA/GISAID). If
    s_names is set to True, function returns name of samples and if False
    returns just the numbers
    """
    if (
        PublicDatabaseValues.objects.filter(
            public_database_fieldID__property_name__iexact=field_db
        )
        .exclude(value__iexact="Not Provided")
        .exists()
    ):
        if s_names:
            return PublicDatabaseValues.objects.filter(
                public_database_fieldID__property_name__iexact=field_db
            ).exclude(value__iexact="Not Provided")
        else:
            return (
                PublicDatabaseValues.objects.filter(
                    public_database_fieldID__property_name__iexact=field_db
                )
                .exclude(value__iexact="Not Provided")
                .count()
            )
    if s_names:
        return []
    else:
        return 0
