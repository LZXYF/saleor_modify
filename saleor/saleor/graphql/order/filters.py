import django_filters
from django.db.models import Sum

from ...order.models import Order
from ..core.filters import ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import filter_by_query_param
from .enums import OrderStatusFilter


def filter_payment_status(qs, _, value):
    if value:
        qs = qs.filter(payments__is_active=True, payments__charge_status__in=value)
    return qs


def filter_status(qs, _, value):
    query_objects = qs.none()

    if value:
        query_objects |= qs.filter(status__in=value)

    if OrderStatusFilter.READY_TO_FULFILL in value:
        # to use & between queries both of them need to have applied the same
        # annotate
        qs = qs.annotate(amount_paid=Sum("payments__captured_amount"))
        query_objects |= qs.ready_to_fulfill()

    if OrderStatusFilter.READY_TO_CAPTURE in value:
        qs = qs.distinct()
        query_objects = query_objects.distinct()
        query_objects |= qs.ready_to_capture()

    return qs & query_objects


def filter_customer(qs, _, value):
    customer_fields = [
        "user_email",
        "user__first_name",
        "user__last_name",
        "user__email",
    ]
    qs = filter_by_query_param(qs, value, customer_fields)
    return qs


def filter_created_range(qs, _, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte:
        qs = qs.filter(created__date__gte=gte)
    if lte:
        qs = qs.filter(created__date__lte=lte)
    return qs


class DraftOrderFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)

    class Meta:
        model = Order
        fields = ["customer", "created"]


class OrderFilter(DraftOrderFilter):
    payment_status = ListObjectTypeFilter(
        input_class=PaymentChargeStatusEnum, method=filter_payment_status
    )
    status = ListObjectTypeFilter(input_class=OrderStatusFilter, method=filter_status)
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)

    class Meta:
        model = Order
        fields = ["payment_status", "status", "customer", "created"]
