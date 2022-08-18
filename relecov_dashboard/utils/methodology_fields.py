import pandas as pd
from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)
from relecov_core.utils.handling_samples import get_samples_count_per_schema


def schema_fields_utilization():
    """ """
    schema_fields = get_bioinfo_analyis_fields_utilization()
    for schema_name, fields in schema_fields.items():
        s_count = get_samples_count_per_schema(schema_name)
        import pdb

        pdb.set_trace()
        if s_count == 0:
            continue
        field_df = pd.DataFrame.from_dict(fields, index=[0])
        field_df = (field_df(s_count)).round(2)

        counts = {}
        for field, value in fields.items():
            if value not in counts:
                counts[value] = 0
            counts[value] += 1

    return
