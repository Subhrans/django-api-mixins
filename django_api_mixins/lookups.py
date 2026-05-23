from enum import Enum


class FieldLookup(Enum):
    EXACT = "exact"
    ICONTAINS = "icontains"
    CONTAINS = "contains"
    ISNULL = "isnull"
    GTE = "gte"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"