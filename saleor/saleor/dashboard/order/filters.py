from django import forms
from django.db.models import F, Max, Q
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import (
    CharFilter,
    ChoiceFilter,
    DateFromToRangeFilter,
    NumberFilter,
    OrderingFilter,
    RangeFilter,
)

from ...core.filters import SortedFilterSet
from ...order import OrderStatus
from ...order.models import Order
from ...payment import ChargeStatus
from ..widgets import DateRangeWidget, MoneyRangeWidget

SORT_BY_FIELDS = [
    ("pk", "pk"),
    ("payments__charge_status", "payment_status"),
    ("user__email", "email"),
    ("created", "created"),
    ("total_net", "total"),
]

SORT_BY_FIELDS_LABELS = {
    "pk": pgettext_lazy("Order list sorting option", "#"),
    "payments__charge_status": pgettext_lazy("Order list sorting option", "payment"),
    "user__email": pgettext_lazy("Order list sorting option", "email"),
    "created": pgettext_lazy("Order list sorting option", "created"),
    "total_net": pgettext_lazy("Order list sorting option", "created"),
}


class OrderFilter(SortedFilterSet):
    id = NumberFilter(label=pgettext_lazy("Order list filter label", "ID"))
    name_or_email = CharFilter(
        label=pgettext_lazy("Order list filter label", "Customer name or email"),
        method="filter_by_order_customer",
    )
    created = DateFromToRangeFilter(
        label=pgettext_lazy("Order list filter label", "Placed on"),
        field_name="created",
        widget=DateRangeWidget,
    )
    status = ChoiceFilter(
        label=pgettext_lazy("Order list filter label", "Order status"),
        choices=OrderStatus.CHOICES,
        empty_label=pgettext_lazy("Filter empty choice label", "All"),
        widget=forms.Select,
    )
    payment_status = ChoiceFilter(
        label=pgettext_lazy("Order list filter label", "Payment status"),
        method="filter_by_payment_status",
        distinct=True,
        choices=ChargeStatus.CHOICES,
        empty_label=pgettext_lazy("Filter empty choice label", "All"),
        widget=forms.Select,
    )
    total_net = RangeFilter(
        label=pgettext_lazy("Order list filter label", "Total"), widget=MoneyRangeWidget
    )
    sort_by = OrderingFilter(
        label=pgettext_lazy("Order list filter label", "Sort by"),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS,
    )

    class Meta:
        model = Order
        fields = []

    def filter_by_order_customer(self, queryset, name, value):
        return queryset.filter(
            Q(user__email__icontains=value)
            | Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
            | Q(user__default_billing_address__first_name__icontains=value)
            | Q(user__default_billing_address__last_name__icontains=value)
        )

    def filter_by_payment_status(self, queryset, name, value):
        annotated_queryset = queryset.annotate(last_payment_pk=Max("payments__pk"))
        query_order_with_payments = Q(
            payments__pk=F("last_payment_pk"), payments__charge_status=value
        )
        query_order_without_payments = Q(payments__isnull=True)
        if value == ChargeStatus.NOT_CHARGED:
            return annotated_queryset.filter(
                query_order_with_payments | query_order_without_payments
            )
        return annotated_queryset.filter(query_order_with_payments)

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            "Number of matching records in the dashboard orders list",
            "Found %(counter)d matching order",
            "Found %(counter)d matching orders",
            number=counter,
        ) % {"counter": counter}
