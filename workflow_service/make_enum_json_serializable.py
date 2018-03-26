""" Module that monkey-patches the json module when it's imported so
JSONEncoder.default() automatically checks to see if the object being encoded
is an Enum type and, if so, returns its name.
"""
from enum import Enum
from json import JSONEncoder

_SAVED_DEFAULT = JSONEncoder().default  # Save default method.


def _new_default(_, obj):
    if isinstance(obj, Enum):
        return obj.name  # could also be obj.value
    return _SAVED_DEFAULT


JSONEncoder.default = _new_default  # Set new default method.
