# django-api-mixins

[![PyPI version](https://badge.fury.io/py/django-api-mixins.svg)](https://badge.fury.io/py/django-api-mixins)
[![PyPI](https://img.shields.io/pypi/v/django-api-mixins)](https://pypi.org/project/django-api-mixins/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/django-api-mixins)](https://pypi.org/project/django-api-mixins/)
[![Django](https://img.shields.io/badge/Django-3.2%2B-blue)](https://www.djangoproject.com/)

**Django REST Framework API Mixins** - A collection of powerful, reusable mixins for Django REST Framework ViewSets and APIViews to simplify common API development patterns. Perfect for building REST APIs with Django.

**📦 Available on PyPI**: [https://pypi.org/project/django-api-mixins/](https://pypi.org/project/django-api-mixins/)

**Keywords**: Django REST Framework, DRF, Django API, ViewSets, APIViews, Mixins, Django Mixins, REST API, Serializers, Queryset Filtering

## Features

- **APIMixin**: Dynamic serializer selection based on action (create, update, list, retrieve)
- **ModelMixin**: Automatic filter field generation for Django models
- **ModelFilterFieldsMixin**: Automatically sets `filterset_fields` from models with `get_filter_fields()` (requires `django-filter`)
- **OpenAPIFilterParametersMixin**: Adds OpenAPI/Swagger filter parameters for APIView (requires `django-filter` and `drf-spectacular`)
- **RelationshipFilterMixin**: Automatic filtering for reverse relationships and direct fields
- **RoleBasedFilterMixin**: Role-based queryset filtering for multi-tenant applications

## Installation

**Basic installation:**
```bash
pip install django-api-mixins
```

**With optional dependencies:**
```bash
# For ModelFilterFieldsMixin (requires django-filter)
pip install django-api-mixins[filters]

# For OpenAPIFilterParametersMixin (requires drf-spectacular)
pip install django-api-mixins[spectacular]

# Install all optional dependencies
pip install django-api-mixins[all]
```

## Requirements

**Core dependencies (required):**
- Python 3.8+
- Django 3.2+
- Django REST Framework 3.12+

**Optional dependencies:**
- `django-filter>=23.0` - Required for `ModelFilterFieldsMixin` and `OpenAPIFilterParametersMixin`
- `drf-spectacular>=0.26.0` - Required for `OpenAPIFilterParametersMixin`

## Quick Start

### APIMixin

Use different serializers for different actions (create, update, list, retrieve):

```python
from rest_framework import viewsets
from django_api_mixins import APIMixin

class UserViewSet(APIMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer  # Default serializer
    create_serializer_class = UserCreateSerializer  # For POST requests
    update_serializer_class = UserUpdateSerializer  # For PUT/PATCH requests
    list_serializer_class = UserListSerializer  # For GET list requests
    retrieve_serializer_class = UserDetailSerializer  # For GET detail requests
```

The mixin also automatically handles list data in requests:

```python
# POST /api/users/
# Body: [{"name": "User1"}, {"name": "User2"}]
# Automatically sets many=True for list data
```

### ModelMixin

Automatically generate filter fields for all model fields:

```python
from django.db import models
from django_api_mixins import ModelMixin

class Product(models.Model, ModelMixin):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

# Automatically generates filter fields:
# - name: exact, in, isnull
# - price: exact, in, isnull, gte, lte
# - created_at: exact, in, isnull, gte, lte
# - is_active: exact, in, isnull
```

Use in your ViewSet with Django Filter Backend:

```python
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django_api_mixins import ModelMixin

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = Product.get_filter_fields()  # Use auto-generated fields
```

Filter related models:

```python
# Get filter fields for a related model
filter_fields = Product.get_filter_fields_for_related_model('category')
# Returns: {'category__name': [...], 'category__id': [...], ...}

# Get filter fields for a foreign key field
filter_fields = Order.get_filter_fields_for_foreign_fields('product')
# Returns: {'product__name': [...], 'product__price': [...], ...}
```

### ModelFilterFieldsMixin

**⚠️ Requires**: `django-filter` package. Install with `pip install django-filter` or `pip install django-api-mixins[filters]`

Automatically sets `filterset_fields` from a model that uses `ModelMixin` (or any model with a `get_filter_fields()` class method). Works with APIView, GenericAPIView, and ViewSets.

```python
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django_api_mixins import ModelFilterFieldsMixin

# ViewSet / GenericAPIView: filter fields come from queryset.model
class UnitViewSet(ModelFilterFieldsMixin, viewsets.ModelViewSet):
    queryset = Unit.objects.all()  # Unit must have ModelMixin or get_filter_fields()
    serializer_class = UnitSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields auto-set from Unit.get_filter_fields()

# APIView: set model so the mixin can resolve filter fields
from rest_framework.views import APIView

class UnitListAPIView(ModelFilterFieldsMixin, APIView):
    model = Unit  # required for APIView
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        return Unit.objects.all()
    
    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        # ... rest of your logic

# Optional: use a different model for filter fields than the queryset model
class MyViewSet(ModelFilterFieldsMixin, viewsets.ModelViewSet):
    queryset = SomeProxy.objects.all()
    filterset_model = Unit  # use Unit.get_filter_fields() instead of SomeProxy
    filter_backends = [DjangoFilterBackend]
```

**Note**: If `django-filter` is not installed, you'll get a clear error message with installation instructions when you try to use this mixin.

### OpenAPIFilterParametersMixin

**⚠️ Requires**: Both `django-filter` and `drf-spectacular` packages. Install with `pip install django-filter drf-spectacular` or `pip install django-api-mixins[all]`

Adds OpenAPI/Swagger filter parameters for plain APIView so Swagger shows the same filter query params as GenericAPIView/ViewSet. For GenericAPIView/ViewSet this mixin is a no-op (Spectacular already adds params).

```python
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django_api_mixins import OpenAPIFilterParametersMixin, ModelFilterFieldsMixin

# With Swagger/OpenAPI filter parameters
class UnitListAPIView(OpenAPIFilterParametersMixin, ModelFilterFieldsMixin, APIView):
    model = Unit  # required
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        return Unit.objects.all()
    
    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        # ... rest of your logic
        # Filter parameters will appear in Swagger/OpenAPI docs

# Without Swagger params: use only ModelFilterFieldsMixin
class UnitListAPIView(ModelFilterFieldsMixin, APIView):
    model = Unit
    filter_backends = [DjangoFilterBackend]
    # Filtering works, but params won't appear in OpenAPI docs
```

**Note**: If `django-filter` or `drf-spectacular` is not installed, you'll get a clear error message with installation instructions when you try to use this mixin.

### RelationshipFilterMixin

Automatically apply filters for reverse relationships and direct fields:

```python
from rest_framework import viewsets
from django_api_mixins import RelationshipFilterMixin

class OrderViewSet(RelationshipFilterMixin, viewsets.ModelViewSet):
    queryset = Order.objects.all()
    
    # Define which reverse relationship filters to allow
    reverse_relation_filters = [
        'customer__name',
        'customer__email',
        'product__category__name',
    ]
    
    # Define which filters support list/array values
    listable_filters = ['customer__id', 'product__id']
```

**Important**: Place the mixin BEFORE the ViewSet class:

```python
# ✅ Correct
class OrderViewSet(RelationshipFilterMixin, viewsets.ModelViewSet):
    pass

# ❌ Wrong
class OrderViewSet(viewsets.ModelViewSet, RelationshipFilterMixin):
    pass
```

Usage examples:

```python
# Filter by customer name
GET /api/orders/?customer__name=John

# Filter by multiple customer IDs (listable filter)
GET /api/orders/?customer__id=1,2,3
# or
GET /api/orders/?customer__id=[1,2,3]

# Filter by product category
GET /api/orders/?product__category__name=Electronics
```

### RoleBasedFilterMixin

Automatically filter querysets based on user roles:

```python
from rest_framework import viewsets
from django_api_mixins import RoleBasedFilterMixin

class OrderViewSet(RoleBasedFilterMixin, viewsets.ModelViewSet):
    queryset = Order.objects.all()
    
    # Required: field name to filter on
    role_filter_field = 'operator_type'
    
    # Optional: roles that see all data
    admin_roles = ['admin', 'super_admin']
    
    # Optional: roles that see no data
    excluded_roles = ['guest']
    
    # Optional: custom role to field value mapping
    role_mapping = {
        'custom_role': 'custom_value',
        'manager': 'MGR',
    }
```

**Important**: Place the mixin BEFORE the ViewSet class:

```python
# ✅ Correct
class OrderViewSet(RoleBasedFilterMixin, viewsets.ModelViewSet):
    pass

# ❌ Wrong
class OrderViewSet(viewsets.ModelViewSet, RoleBasedFilterMixin):
    pass
```

How it works:

1. Extracts the user's role from `user.role.name`
2. Admin roles see all data (no filtering)
3. Excluded roles see no data (empty queryset)
4. Other roles are filtered by `role_filter_field = role_name` (or mapped value)

Example:

```python
# User with role.name = 'operator'
# Model has operator_type field
# Automatically filters: Order.objects.filter(operator_type='operator')

# User with role.name = 'admin'
# Sees all orders (no filtering)

# User with role.name = 'guest'
# Sees no orders (queryset.none())
```

## FieldLookup Enum

The package includes a `FieldLookup` enum for consistent lookup naming:

```python
from django_api_mixins import FieldLookup

FieldLookup.EXACT      # "exact"
FieldLookup.ICONTAINS  # "icontains"
FieldLookup.CONTAINS   # "contains"
FieldLookup.ISNULL     # "isnull"
FieldLookup.GTE        # "gte"
FieldLookup.LTE        # "lte"
FieldLookup.IN         # "in"
```

## Combining Mixins

You can combine multiple mixins:

```python
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django_api_mixins import (
    APIMixin,
    ModelFilterFieldsMixin,
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
)

class OrderViewSet(
    ModelFilterFieldsMixin,  # Auto-set filterset_fields from model
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
    APIMixin,
    viewsets.ModelViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    create_serializer_class = OrderCreateSerializer
    filter_backends = [DjangoFilterBackend]
    
    role_filter_field = 'operator_type'
    reverse_relation_filters = ['customer__name', 'product__category__name']
    listable_filters = ['customer__id']
```

**Note**: The order of mixins matters! Place filtering mixins before the ViewSet class.

**Optional Dependencies**: If using `ModelFilterFieldsMixin` or `OpenAPIFilterParametersMixin`, make sure to install the required dependencies:
- `ModelFilterFieldsMixin` requires: `django-filter`
- `OpenAPIFilterParametersMixin` requires: `django-filter` and `drf-spectacular`

## Contributing

Contributions are welcome! Here’s how to contribute:

1. **Fork the repository** on GitHub and clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/django-api-mixins.git
   cd django-api-mixins
   ```

2. **Create a virtual environment** and install the package in editable mode with dev dependencies:
   ```bash
   python -m venv venv
   # On Windows: venv\Scripts\activate
   # On macOS/Linux: source venv/bin/activate
   pip install -e ".[all]"
   pip install -r requirements-dev.txt   # if present
   ```

3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or: git checkout -b fix/your-bugfix-name
   ```

4. **Make your changes** — keep code style consistent and add/update tests as needed.

5. **Run tests** (and linting, if configured):
   ```bash
   pytest
   # or: python -m pytest
   ```

6. **Commit and push** to your fork:
   ```bash
   git add .
   git commit -m "Brief description of your change"
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** from your branch to the main repository’s default branch. Describe what you changed and why; link any related issues.

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/subhrans/django-api-mixins).

## PyPI

This package is published on PyPI and can be installed via pip:

```bash
pip install django-api-mixins
```

**PyPI Project Page**: [https://pypi.org/project/django-api-mixins/](https://pypi.org/project/django-api-mixins/)

**Latest Version**: 0.1.3 (Released: Feb 22, 2026)
