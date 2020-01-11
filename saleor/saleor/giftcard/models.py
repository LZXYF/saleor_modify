from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import pgettext_lazy
from django_prices.models import MoneyField


class GiftCardQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date),
            start_date__lte=date,
            is_active=True,
        )


class GiftCard(models.Model):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )
    created = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    last_used_on = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    initial_balance = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    current_balance = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    objects = GiftCardQueryset.as_manager()

    class Meta:
        permissions = (
            (
                "manage_gift_card",
                pgettext_lazy("Permission description", "Manage gift cards."),
            ),
        )

    @property
    def display_code(self):
        return "****%s" % self.code[-4:]
