"""
Django REST Framework API Mixins

A collection of useful mixins for Django REST Framework ViewSets and APIViews.
"""

from .mixins import (
    APIMixin,
    ModelMixin,
    ModelFilterFieldsMixin,
    OpenAPIFilterParametersMixin,
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
)
from .lookups import FieldLookup

__version__ = "0.1.2"
__all__ = [
    "APIMixin",
    "ModelMixin",
    "ModelFilterFieldsMixin",
    "OpenAPIFilterParametersMixin",
    "RelationshipFilterMixin",
    "RoleBasedFilterMixin",
    "FieldLookup",
]
