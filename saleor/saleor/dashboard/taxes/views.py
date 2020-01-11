import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from django.views.decorators.http import require_POST
from django_countries.fields import Country
from django_prices_vatlayer.models import VAT

from ...core.taxes.vatlayer import TaxRateType, get_taxes_for_country
from ...core.utils import get_paginator_items
from ...dashboard.taxes.filters import TaxFilter
from ...dashboard.taxes.forms import TaxesConfigurationForm
from ...dashboard.views import staff_member_required

logger = logging.getLogger(__name__)

# FIXME these views belong to vatlayer module.


@staff_member_required
def tax_list(request):
    if settings.VATLAYER_ACCESS_KEY:
        taxes = VAT.objects.order_by("country_code")
        tax_filter = TaxFilter(request.GET, queryset=taxes)
        taxes = get_paginator_items(
            tax_filter.qs, settings.DASHBOARD_PAGINATE_BY, request.GET.get("page")
        )
        ctx = {
            "taxes": taxes,
            "filter_set": tax_filter,
            "is_empty": not tax_filter.queryset.exists(),
        }
    else:
        ctx = {"taxes": [], "filter_set": None, "is_empty": True}
    return TemplateResponse(request, "dashboard/taxes/list.html", ctx)


@staff_member_required
def tax_details(request, country_code):
    if not settings.VATLAYER_ACCESS_KEY:
        return HttpResponseNotFound()
    tax = get_object_or_404(VAT, country_code=country_code)
    tax_rates = get_taxes_for_country(Country(country_code))
    translations = dict(TaxRateType.CHOICES)
    tax_rates = [
        (translations.get(rate_name, rate_name), tax["value"])
        for rate_name, tax in tax_rates.items()
    ]
    ctx = {"tax": tax, "tax_rates": sorted(tax_rates)}
    return TemplateResponse(request, "dashboard/taxes/details.html", ctx)


@staff_member_required
@permission_required("site.manage_settings")
def configure_taxes(request):
    site_settings = request.site.settings
    taxes_form = TaxesConfigurationForm(request.POST or None, instance=site_settings)
    if taxes_form.is_valid():
        taxes_form.save()
        msg = pgettext_lazy("Dashboard message", "Updated taxes settings")
        messages.success(request, msg)
        return redirect("dashboard:taxes")
    ctx = {"site": site_settings, "taxes_form": taxes_form}
    return TemplateResponse(request, "dashboard/taxes/form.html", ctx)


@staff_member_required
@require_POST
@permission_required("site.manage_settings")
def fetch_tax_rates(request):
    try:
        call_command("get_vat_rates")
        msg = pgettext_lazy("Dashboard message", "Tax rates updated successfully")
        messages.success(request, msg)
    except ImproperlyConfigured as exc:
        logger.exception(exc)
        msg = pgettext_lazy(
            "Dashboard message",
            "Could not fetch tax rates. "
            "Make sure you have supplied a valid API Access Key.<br/>"
            "Check the server logs for more information about this error.",
        )
        messages.warning(request, msg)
    return redirect("dashboard:taxes")
