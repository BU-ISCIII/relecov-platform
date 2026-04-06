from .sample_per_lab import register as register_sample_per_lab
from .sample_variant import register as register_sample_variant
from .samples_received_map import register as register_samples_received_map

_REGISTERED = False


def register_all():
    global _REGISTERED
    if _REGISTERED:
        return
    register_sample_per_lab()
    register_sample_variant()
    register_samples_received_map()
    _REGISTERED = True
