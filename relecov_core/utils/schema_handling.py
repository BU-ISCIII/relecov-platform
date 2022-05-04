import json
import os
from relecov_core.utils import store_file


def load_schema(json_file):
    """Store json file in the defined folder and store information in database"""

    if not os.path.isfile(json_file):
        return
    try:
        schema_data = josn.load(json_file)
    except:
        return
    import pdb; pdb.set_trace()
    store_file(json_file)
