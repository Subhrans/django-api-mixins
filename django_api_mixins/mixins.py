from copy import deepcopy

from django.db.models import (
    BooleanField,
    DateField,
    DateTimeField,
    TimeField,
    IntegerField,
    SmallIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    BigIntegerField,
    FloatField,
    DecimalField,
    DurationField, FileField, JSONField
)
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.db.models.fields.related import ForeignKey

from .lookups import FieldLookup


class RelationshipFilterMixin:
    """
    A mixin to automatically apply filters for reverse relationships and direct fields to querysets.
    It only applies the filters defined in `reverse_relation_filters` on the view.

    Supports:
      - Reverse relation filters via double-underscore paths
      - __in lookups for listable filters
      - Boolean value auto-conversion

    Note:
        In order to use this mixin class, you need to call it before any APIview or viewsets class being called.
        Example:
            class ABCView(RelationshipFilterMixin, APIView)
            class ABCView(RelationshipFilterMixin, ModelViewSet)

        Don't:
            class ABCView(APIView, RelationshipFilterMixin)
            class ABCView(ModelViewSet, RelationshipFilterMixin)
    """

    reverse_relation_filters = []
    listable_filters = []

    def parse_to_list(self, input_string: str):
        """
        Allow user to search data in list form.
        Example:
            query_params_can be vendor = ['ab','bc']
        Acceptable input:
            ['ab','bc']
            "['ab','bc']"
            'ab,bc'
        """

        if isinstance(input_string, list):
            return input_string
        # Check if the string starts and ends with square brackets
        if input_string.startswith("[") and input_string.endswith("]"):
            # Remove brackets and split by commas
            return [item.strip() for item in input_string.strip("[]").split(",")]
        else:
            # If not in brackets, assume it's a single value and return as a list
            return input_string.strip().split(",")

    def convert_to_boolean_if_needed(self, model, field_path, value):
        """If the target field is BooleanField, convert string to bool."""
        try:
            split_field_paths = field_path.split("__")
            if split_field_paths[-1] == "isnull":
                field_name = field_path.split("__")[-2]
            else:
                field_name = field_path.split("__")[-1]
            field_obj = model._meta.get_field(field_name)
            if (isinstance(field_obj, BooleanField) or isinstance(field_obj, ForeignKey)) and value is not None:
                return value.lower() == "true"
        except Exception:
            pass
        return value

    def collect_filters(self):
        """Return a dict of filters from query params matching allowed filter lists."""
        params = self.request.query_params
        if not params:
            return {}

        allowed_filters = set(self.reverse_relation_filters) | set(self.listable_filters)
        filter_data = {
            field: params.get(field) for field in allowed_filters if params.get(field) is not None
        }
        return deepcopy(filter_data)

    def apply_all_filters(self, queryset):
        """Apply both reverse and listable filters in one pass."""
        filter_data = self.collect_filters()
        if not filter_data:
            return queryset

        final_filters = {}
        model = queryset.model
        for filter_key, raw_value in filter_data.items():
            value = self.convert_to_boolean_if_needed(model, filter_key, raw_value)

            if filter_key in self.listable_filters:
                final_filters[f"{filter_key}__in"] = self.parse_to_list(value)
            else:
                final_filters[filter_key] = value

        return queryset.filter(Q(**final_filters))

    def get_queryset(self):
        """
        Overrides `get_queryset` to apply dynamic filters automatically.
        """
        # Call the parent class's `get_queryset` to get the base queryset
        queryset = super().get_queryset()
        return self.apply_all_filters(queryset)


class RoleBasedFilterMixin:
    """
    A mixin to automatically filter querysets based on user role.
    
    This mixin automatically filters data based on the logged-in user's role, similar to
    Django permissions but for queryset filtering. It maps user roles to model field values
    and filters the queryset accordingly.
    
    Configuration:
        - role_filter_field: The model field name to filter on (e.g., 'operator_type')
        - admin_roles: List of role names that should see all data (default: ['admin'])
        - excluded_roles: List of role names that should see no data (default: [])
        - role_mapping: Dict mapping role names to field values (optional, defaults to role name = field value)
    
    Usage:
        class MyViewSet(RoleBasedFilterMixin, ModelViewSet):
            role_filter_field = 'operator_type'
            # Optional: customize admin roles
            admin_roles = ['admin', 'super_admin']
            # Optional: exclude certain roles
            excluded_roles = ['guest']
            # Optional: custom role mapping
            role_mapping = {
                'custom_role': 'custom_value'
            }
    
    Note:
        Place this mixin BEFORE the ViewSet class in the inheritance order.
        Example:
            class MyView(RoleBasedFilterMixin, ModelViewSet)  # Correct
            class MyView(ModelViewSet, RoleBasedFilterMixin)  # Wrong
    """
    
    # Configuration attributes (can be overridden in subclasses)
    role_filter_field = None  # Required: field name to filter on (e.g., 'operator_type')
    admin_roles = ['admin']  # Roles that see all data
    excluded_roles = []  # Roles that see no data
    role_mapping = {}  # Custom mapping: {role_name: field_value}
    
    def get_role_filter_field(self):
        """Get the field name to filter on. Must be set in subclass."""
        if not self.role_filter_field:
            raise ValueError(
                f"{self.__class__.__name__} must define 'role_filter_field' attribute. "
                f"Example: role_filter_field = 'operator_type'"
            )
        return self.role_filter_field
    
    def get_user_role_name(self, user):
        """Extract role name from user object."""
        if not user or not hasattr(user, 'role'):
            return None
        role = getattr(user, 'role', None)
        if not role:
            return None
        return getattr(role, 'name', None)
    
    def get_field_value_for_role(self, role_name):
        """
        Get the field value to filter on for a given role.
        Uses role_mapping if available, otherwise uses role_name directly.
        """
        if role_name in self.role_mapping:
            return self.role_mapping[role_name]
        return role_name
    
    def apply_role_filter(self, queryset, user):
        """
        Apply role-based filtering to the queryset.
        
        Returns:
            Filtered queryset based on user role
        """
        if not user or not user.is_authenticated:
            return queryset
        
        role_name = self.get_user_role_name(user)
        if not role_name:
            return queryset
        
        # Admin roles see all data
        if role_name in self.admin_roles:
            return queryset
        
        # Excluded roles see no data
        if role_name in self.excluded_roles:
            return queryset.none()
        
        # Get field value for this role
        field_value = self.get_field_value_for_role(role_name)
        field_name = self.get_role_filter_field()
        
        # Apply filter
        filter_kwargs = {field_name: field_value}
        return queryset.filter(**filter_kwargs)
    
    def get_queryset(self):
        """
        Override get_queryset to automatically apply role-based filtering.
        """
        queryset = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if user:
            queryset = self.apply_role_filter(queryset, user)
        return queryset

class ModelFilterFieldsMixin:
    """
    View mixin that sets `filterset_fields` from a model that uses ModelMixin
    (or any model with a `get_filter_fields()` class method).

    **Requires**: `django-filter` package. Install with:
        pip install django-filter
    Or install with optional dependencies:
        pip install django-api-mixins[filters]

    Works with:
      - rest_framework.views.APIView (set `model` on the view)
      - rest_framework.generics.GenericAPIView / ListAPIView etc. (uses queryset.model)
      - rest_framework.viewsets.ViewSet / ModelViewSet (uses queryset.model)

    Only sets `filterset_fields` when the view does not already define it
    (so you can still set filterset_fields explicitly to override).

    Usage:

        # ViewSet / GenericAPIView: filter fields come from queryset.model
        class UnitViewSet(ModelFilterFieldsMixin, ModelViewSet):
            queryset = Unit.objects.all()
            serializer_class = UnitSerializer
            # filterset_fields auto-set from Unit.get_filter_fields()

        # APIView: set model so the mixin can resolve filter fields
        class UnitListAPIView(ModelFilterFieldsMixin, APIView):
            model = Unit
            def get_queryset(self):
                return Unit.objects.all()
            ...

        # Optional: use a different model for filter fields than the queryset model
        class MyViewSet(ModelFilterFieldsMixin, ModelViewSet):
            queryset = SomeProxy.objects.all()
            filterset_model = Unit  # use Unit.get_filter_fields()
    """

    filterset_model = None  # optional: use this model for filter fields instead of queryset.model

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Check for django-filter dependency
        try:
            import django_filters
        except ImportError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{cls.__name__} uses ModelFilterFieldsMixin which requires 'django-filter' package. "
                "Install it with: pip install django-filter\n"
                "Or install with optional dependencies: pip install django-api-mixins[filters]"
            )
        super().__init_subclass__(**kwargs)
        model = getattr(cls, "model", None)
        if model is None:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{cls.__name__} uses ModelFilterFieldsMixin but does not set "
                "'model'. Set model = YourModel on the view so the mixin can resolve filter fields."
            )
        get_filter_fields = getattr(model, "get_filter_fields", None)
        if not callable(get_filter_fields):
            return
        # Set filterset_fields on the view *class* so DjangoFilterBackend and (optionally)
        # drf-spectacular see them. Skip if the subclass already defines filterset_fields.
        if "filterset_fields" not in cls.__dict__:
            cls.filterset_fields = get_filter_fields()


    def _set_filterset_fields_from_model(self, model):
        """Set self.filterset_fields from model.get_filter_fields() if the model supports it."""
        if model is None:
            return
        get_filter_fields = getattr(model, "get_filter_fields", None)
        if not callable(get_filter_fields):
            return
        if "filterset_fields" in type(self).__dict__:
            return
        self.filterset_fields = get_filter_fields()

    def get_queryset(self):
        queryset = super().get_queryset()
        model = self.filterset_model if self.filterset_model is not None else getattr(queryset, "model", None)
        if model is not None:
            self._set_filterset_fields_from_model(model)
        return queryset

    def get_filter_backends(self):
        """Return the list of filter backend classes. For APIView; GenericAPIView overrides this."""
        # Ensure django-filter is available
        try:
            from django_filters.rest_framework import DjangoFilterBackend
        except ImportError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} uses ModelFilterFieldsMixin which requires 'django-filter' package. "
                "Install it with: pip install django-filter\n"
                "Or install with optional dependencies: pip install django-api-mixins[filters]"
            )
        from rest_framework.settings import api_settings
        return getattr(self, "filter_backends", None) or api_settings.DEFAULT_FILTER_BACKENDS or []

    def filter_queryset(self, queryset):
        """Apply filter backends to the queryset. For APIView; GenericAPIView overrides this."""
        for backend in self.get_filter_backends():
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


class OpenAPIFilterParametersMixin:
    """
    Plug-and-play mixin: injects OpenAPI filter parameters for plain APIView
    so Swagger (drf-spectacular) shows the same filter query params as
    GenericAPIView/ViewSet.

    **Requires**: Both `django-filter` and `drf-spectacular` packages. Install with:
        pip install django-filter drf-spectacular
    Or install with optional dependencies:
        pip install django-api-mixins[all]

    Use together with ModelFilterFieldsMixin when you want filter params in docs
    for APIView. For GenericAPIView/ViewSet this mixin is a no-op (Spectacular
    already adds params). Requires drf-spectacular. Omit this mixin if you
    don't need filter params in OpenAPI or stop using Spectacular.

    Usage (plain APIView only; set model on the view):

        class UnitListAPIView(OpenAPIFilterParametersMixin, ModelFilterFieldsMixin, APIView):
            model = Unit  # required
            ...

        # Without Swagger params (e.g. no drf-spectacular): use only ModelFilterFieldsMixin
        class UnitListAPIView(ModelFilterFieldsMixin, APIView):
            model = Unit
            ...
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        from rest_framework.generics import GenericAPIView
        if GenericAPIView in cls.__mro__:
            return
        
        # Check for django-filter dependency
        try:
            from django_filters.rest_framework import DjangoFilterBackend
        except ImportError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{cls.__name__} uses OpenAPIFilterParametersMixin which requires 'django-filter' package. "
                "Install it with: pip install django-filter\n"
                "Or install with optional dependencies: pip install django-api-mixins[filters]"
            )
        
        # Check for drf-spectacular dependency
        try:
            from drf_spectacular.utils import extend_schema, extend_schema_view
        except ImportError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{cls.__name__} uses OpenAPIFilterParametersMixin which requires 'drf-spectacular' package. "
                "Install it with: pip install drf-spectacular\n"
                "Or install with optional dependencies: pip install django-api-mixins[spectacular] or django-api-mixins[all]"
            )
        
        model = getattr(cls, "model", None)
        if model is None:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                f"{cls.__name__} uses OpenAPIFilterParametersMixin but does not set "
                "'model'. Set model = YourModel on the view so the mixin can resolve filter fields for OpenAPI."
            )
        # So get() can apply filtering without the view defining filter_backends
        if "filter_backends" not in cls.__dict__:
            cls.filter_backends = [DjangoFilterBackend]
        
        params = OpenAPIFilterParametersMixin._build_openapi_filter_parameters(model)
        if params:
            # Attach to GET so Spectacular shows params on the correct operation (APIView has no "list" action)
            extend_schema_view(get=extend_schema(parameters=params))(cls)
        params = OpenAPIFilterParametersMixin._build_openapi_filter_parameters(model)
        if params:
            # Attach to GET so Spectacular shows params on the correct operation (APIView has no "list" action)
            extend_schema_view(get=extend_schema(parameters=params))(cls)
    
    def get_filter_backends(self):
        """Return the list of filter backend classes. For APIView; GenericAPIView overrides this."""
        from rest_framework.settings import api_settings
        return api_settings.DEFAULT_FILTER_BACKENDS or []

    @staticmethod
    def _build_openapi_filter_parameters(model):
        """
        Build OpenApiParameter list from model using the same path as Spectacular
        for GenericAPIView/ViewSet: call DjangoFilterExtension.get_schema_operation_parameters()
        directly so we get identical params and bypass _is_list_view().
        Returns [] if drf-spectacular is unavailable or the call fails.
        """
        get_filter_fields = getattr(model, "get_filter_fields", None)
        if not callable(get_filter_fields):
            return []
        filterset_fields = get_filter_fields()
        if not filterset_fields:
            return []

        from rest_framework.settings import api_settings
        filter_backends = api_settings.DEFAULT_FILTER_BACKENDS or []

        try:
            from rest_framework.generics import ListAPIView
            from django_filters.rest_framework import DjangoFilterBackend
            from drf_spectacular.extensions import OpenApiFilterExtension
        except ImportError as e:
            # This should not happen if __init_subclass__ checks passed, but handle gracefully
            return []

        try:
            if not hasattr(model, "objects"):
                return []
            queryset = model.objects.none()
            temp_view = type(
                "_TempFilterSchemaView",
                (ListAPIView,),
                {
                    "queryset": queryset,
                    "filterset_fields": filterset_fields,
                    "filter_backends": filter_backends,
                    "serializer_class": None,
                },
            )
            backend = DjangoFilterBackend()
            extension = OpenApiFilterExtension.get_match(backend)
            if extension is None:
                raise ValueError("No extension match")
            # AutoSchema(view=..., path=..., method=...) fails in some versions (ViewInspector API).
            # Pass a minimal object with .view so the extension can build params from the filterset.
            class _ViewContext:
                view = temp_view
            raw_params = extension.get_schema_operation_parameters(_ViewContext())
            if not raw_params:
                return []
            # Extension returns OpenAPI-style dicts; extend_schema expects OpenApiParameter.
            from drf_spectacular.utils import OpenApiParameter
            return [
                OpenApiParameter(
                    name=p["name"],
                    type=p.get("schema"),
                    location=OpenApiParameter.QUERY,
                    description=p.get("description", ""),
                    required=p.get("required", False),
                )
                for p in raw_params
            ]
        except (TypeError, ValueError, Exception):
            pass
        return []



class ModelMixin:
    @classmethod
    def _build_default_filter_fields(cls):
        """
        Dynamically build FILTER_FIELDS for all concrete model fields.
        - All fields: exact, in, isnull
        - Numeric/Date/Time-like: gte, lte additionally
        """
        filter_fields = {}
        numeric_or_temporal_types = (
            IntegerField,
            SmallIntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            BigIntegerField,
            FloatField,
            DecimalField,
            DurationField,
            DateField,
            DateTimeField,
            TimeField,
        )
        for field in cls._meta.get_fields():
            # Only include concrete, non-M2M fields
            if not getattr(field, "concrete", False) or getattr(field, "many_to_many", False):
                continue

            if isinstance(field, FileField):
                continue

            field_name = field.name
            lookups = [
                FieldLookup.EXACT.value,
                FieldLookup.IN.value,
                FieldLookup.ISNULL.value,
            ]
            # if field.name == "result":
            #     breakpoint()
            if isinstance(field, JSONField):
                # filter_fields[field_name] = ["icontains"]  # avoid exact/in/gte/lte
                continue
                # continue

            if isinstance(field, numeric_or_temporal_types):
                lookups.extend([
                    FieldLookup.GTE.value,
                    FieldLookup.LTE.value,
                ])
            filter_fields[field_name] = lookups
        return filter_fields

    @classmethod
    def get_filter_fields(cls):
        # if  "apps.assembly" in cls.__module__:
        #     breakpoint()
        return cls._build_default_filter_fields()

    @classmethod
    def get_filter_fields_for_related_model(cls, prefix):
        filter_fields = cls.get_filter_fields()
        new_filter_fields = dict()
        for key, value in filter_fields.items():
            new_filter_fields[f"{prefix}__{key}"] = value
        return new_filter_fields

    @classmethod
    def get_filter_fields_for_foreign_fields(cls, prefix):
        try:
            field = cls._meta.get_field(prefix)
        except FieldDoesNotExist:
            return {}
        if not isinstance(field, ForeignKey):
            return {}
        related_model = field.related_model
        if not (hasattr(related_model, "_build_default_filter_fields") and callable(getattr(related_model, "_build_default_filter_fields"))):
            return {}
        filter_fields = related_model._build_default_filter_fields()
        return {f"{prefix}__{key}": value for key, value in filter_fields.items()}


class APIMixin:
    serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    retrieve_serializer_class = None
    list_serializer_class = None

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        if self.action == "create" and getattr(self, "create_serializer_class"):
            return self.create_serializer_class
        if self.action in ["update","partial_update"] and getattr(self, "update_serializer_class"):
            return self.update_serializer_class
        elif self.action == "list" and getattr(self, "list_serializer_class"):
            return self.list_serializer_class
        elif self.action == "retrieve" and getattr(self, "retrieve_serializer_class"):
            return self.retrieve_serializer_class
        return serializer_class

    def get_serializer(self, *args, **kwargs):
        if isinstance(self.request.data, list):
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)