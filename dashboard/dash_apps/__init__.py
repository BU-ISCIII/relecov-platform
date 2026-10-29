from .needle_lineage import register as register_needle_lineage
from .variation_lineage import register as register_variation_lineage

_REGISTERED = False


def register_all():
    global _REGISTERED
    if _REGISTERED:
        return
    register_needle_lineage()
    register_variation_lineage()
    _REGISTERED = True
