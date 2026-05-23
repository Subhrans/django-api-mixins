"""
Django REST Framework API Mixins

A collection of useful mixins for Django REST Framework ViewSets and APIViews.
"""
from .filter_backends import NotInFilterBackend
from .mixins import (
    APIMixin,
    ModelMixin,
    ModelFilterFieldsMixin,
    OpenAPIFilterParametersMixin,
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
)
from .lookups import FieldLookup

__version__ = "2.0.0"
__all__ = [
    "APIMixin",
    "ModelMixin",
    "ModelFilterFieldsMixin",
    "OpenAPIFilterParametersMixin",
    "RelationshipFilterMixin",
    "RoleBasedFilterMixin",
    "FieldLookup",
    "NotInFilterBackend",
]
