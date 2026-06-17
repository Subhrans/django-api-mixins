from ..lookups import FieldLookup

try:
    from django_filters.rest_framework import DjangoFilterBackend
except ImportError:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        f"NotInFilterBackend requires 'django-filter' package. "
        "Install it with: pip install django-filter\n"
        "Or install with optional dependencies: pip install django-api-mixins[filters]"
    )



class NotInFilterBackend(DjangoFilterBackend):
    CUSTOM_LOOKUP_MAPPINGS = {
        FieldLookup.NOT_IN.value: {
            "actual_lookup": FieldLookup.IN.value,
            "exclude": True,
        },
    }

    def filter_queryset(self, request, queryset, view):

        queryset = super().filter_queryset(
            request,
            queryset,
            view
        )

        exclude_filters = {}

        for param, value in request.query_params.items():

            if "__" not in param:
                continue

            field_name, lookup = param.rsplit("__", 1)

            config = self.CUSTOM_LOOKUP_MAPPINGS.get(lookup)

            if not config:
                continue

            actual_lookup = config["actual_lookup"]

            final_key = f"{field_name}__{actual_lookup}"

            if actual_lookup == FieldLookup.IN.value:
                value = value.split(",")

            if config["exclude"]:
                exclude_filters[final_key] = value

        if exclude_filters:
            queryset = queryset.exclude(**exclude_filters)

        return queryset