# django-api-mixins

[![PyPI version](https://badge.fury.io/py/django-api-mixins.svg)](https://badge.fury.io/py/django-api-mixins)
[![PyPI](https://img.shields.io/pypi/v/django-api-mixins)](https://pypi.org/project/django-api-mixins/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A collection of useful mixins for Django REST Framework ViewSets and APIViews to simplify common API patterns.

**📦 Available on PyPI**: [https://pypi.org/project/django-api-mixins/](https://pypi.org/project/django-api-mixins/)

## Features

- **APIMixin**: Dynamic serializer selection based on action (create, update, list, retrieve)
- **ModelMixin**: Automatic filter field generation for Django models
- **RelationshipFilterMixin**: Automatic filtering for reverse relationships and direct fields
- **RoleBasedFilterMixin**: Role-based queryset filtering for multi-tenant applications

## Installation

```bash
pip install django-api-mixins
```

## Requirements

- Python 3.8+
- Django 3.2+
- Django REST Framework 3.12+

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
from django_api_mixins import (
    APIMixin,
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
)

class OrderViewSet(
    RelationshipFilterMixin,
    RoleBasedFilterMixin,
    APIMixin,
    viewsets.ModelViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    create_serializer_class = OrderCreateSerializer
    
    role_filter_field = 'operator_type'
    reverse_relation_filters = ['customer__name', 'product__category__name']
    listable_filters = ['customer__id']
```

**Note**: The order of mixins matters! Place filtering mixins before the ViewSet class.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

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

**Latest Version**: 0.1.1 (Released: Feb 20, 2026)
