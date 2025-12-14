import django_filters
from django.db.models import Q
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    created_at = django_filters.DateFromToRangeFilter()
    phone_starts_with = django_filters.CharFilter(method="filter_phone_starts_with")
    def filter_phone_starts_with(self, queryset, name, value):
        return queryset.filter(phone__startswith=value)

    class Meta:
        model = Customer
        fields = [
            "name",
            "email",
            "created_at",
        ]


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price = django_filters.RangeFilter()
    stock = django_filters.RangeFilter()
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")

    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = [
            "name",
            "price",
            "stock",
        ]


class OrderFilter(django_filters.FilterSet):
    total_amount = django_filters.RangeFilter()
    order_date = django_filters.DateFromToRangeFilter()
    customer_name = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = django_filters.CharFilter(field_name="product__name", lookup_expr="icontains")
    product_id = django_filters.NumberFilter(field_name="product__id")

    class Meta:
        model = Order
        fields = [
            "total_amount",
            "order_date",
            "customer_name",
            "product_name",
            "product_id",
        ]
