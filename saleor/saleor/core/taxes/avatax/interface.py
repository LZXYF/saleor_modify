import logging
from decimal import Decimal
from typing import TYPE_CHECKING, List, Union
from urllib.parse import urljoin

from django.conf import settings
from prices import Money, TaxedMoney

from ....checkout import models as checkout_models
from .. import TaxType, zero_taxed_money
from ..errors import TaxError
from . import (
    META_FIELD,
    CustomerErrors,
    TransactionType,
    _validate_checkout,
    _validate_order,
    api_post_request,
    generate_request_data_from_checkout,
    get_api_url,
    get_cached_tax_codes_or_fetch,
    get_checkout_tax_data,
    get_order_tax_data,
)

if TYPE_CHECKING:
    from ....checkout.models import Checkout
    from ....order.models import Order, OrderLine

logger = logging.getLogger(__name__)


def calculate_checkout_total(
    checkout: "checkout_models.Checkout", discounts: List["DiscountInfo"]
):
    checkout_total = checkout.get_total(discounts=discounts)
    if not _validate_checkout(checkout):
        return TaxedMoney(net=checkout_total, gross=checkout_total)
    response = get_checkout_tax_data(checkout, discounts)
    if not response or "error" in response:
        return TaxedMoney(net=checkout_total, gross=checkout_total)

    currency = response.get("currencyCode")
    tax = Decimal(response.get("totalTax", 0.0))
    total_net = Decimal(response.get("totalAmount", 0.0))
    total_gross = Money(amount=total_net + tax, currency=currency)
    total_net = Money(amount=total_net, currency=currency)
    total = TaxedMoney(net=total_net, gross=total_gross)
    voucher_amount = checkout.discount_amount
    if voucher_amount:
        total -= voucher_amount
    return max(total, zero_taxed_money(total.currency))


def calculate_checkout_subtotal(
    checkout: "checkout_models.Checkout", discounts: List["DiscountInfo"]
):
    sub_total = checkout.get_subtotal(discounts)
    if not _validate_checkout(checkout):
        return TaxedMoney(net=sub_total, gross=sub_total)

    response = get_checkout_tax_data(checkout, discounts)
    if not response or "error" in response:
        return TaxedMoney(net=sub_total, gross=sub_total)

    currency = response.get("currencyCode")
    sub_tax = Decimal(0.0)
    sub_net = Decimal(0.0)
    for line in response.get("lines", []):
        if line["itemCode"] == "Shipping":
            continue
        sub_tax += Decimal(line["tax"])
        sub_net += Decimal(line.get("lineAmount", 0.0))

    sub_total_gross = Money(sub_net + sub_tax, currency)
    sub_total_net = Money(sub_net, currency)
    return TaxedMoney(net=sub_total_net, gross=sub_total_gross)


def calculate_checkout_shipping(
    checkout: "checkout_models.Checkout", discounts: List["DiscountInfo"]
):
    shipping_price = checkout.get_shipping_price()
    if not _validate_checkout(checkout):
        return TaxedMoney(net=shipping_price, gross=shipping_price)

    response = get_checkout_tax_data(checkout, discounts)
    if not response or "error" in response:
        return TaxedMoney(net=shipping_price, gross=shipping_price)

    shipping_tax = Decimal(0.0)
    shipping_net = shipping_price.amount
    currency = response.get("currencyCode")
    for line in response.get("lines", []):
        if line["itemCode"] == "Shipping":
            shipping_net = Decimal(line["lineAmount"])
            shipping_tax = Decimal(line["tax"])
            break

    shipping_gross = Money(amount=shipping_net + shipping_tax, currency=currency)
    shipping_net = Money(amount=shipping_net, currency=currency)
    return TaxedMoney(net=shipping_net, gross=shipping_gross)


def preprocess_order_creation(checkout: "Checkout", discounts: List["DiscountInfo"]):
    """Confirm that all data is correct and we can proceed with creation of order.
    Raise error when can't receive taxes"""

    data = generate_request_data_from_checkout(
        checkout,
        transaction_token=str(checkout.token),
        transaction_type=TransactionType.ORDER,
        discounts=discounts,
    )
    transaction_url = urljoin(get_api_url(), "transactions/createoradjust")
    response = api_post_request(transaction_url, data)
    if not response or "error" in response:
        msg = response.get("error", {}).get("message", "")
        error_code = response.get("error", {}).get("code", "")
        logger.warning(
            "Unable to calculate taxes for checkout %s, error_code: %s, error_msg: %s",
            checkout.token,
            error_code,
            msg,
        )
        customer_msg = CustomerErrors.get_error_msg(response.get("error", {}))
        raise TaxError(customer_msg)


def postprocess_order_creation(order: "Order"):
    # FIXME after we introduce plugin architecture, this logic could be a celery task

    data = get_order_tax_data(
        order, commit=settings.AVATAX_AUTOCOMMIT, force_refresh=True
    )

    transaction_url = urljoin(get_api_url(), "transactions/createoradjust")
    api_post_request(transaction_url, data)


def calculate_checkout_line_total(
    checkout_line: "checkout_models.CheckoutLine", discounts: List["DiscountInfo"]
):
    checkout = checkout_line.checkout
    total = checkout_line.get_total(discounts)
    if not _validate_checkout(checkout):
        return TaxedMoney(net=total, gross=total)
    taxes_data = get_checkout_tax_data(checkout, discounts)
    currency = taxes_data.get("currencyCode")
    for line in taxes_data.get("lines", []):
        if line.get("itemCode") == checkout_line.variant.sku:
            tax = Decimal(line.get("tax", 0.0))
            line_net = Decimal(line["lineAmount"])
            line_gross = Money(amount=line_net + tax, currency=currency)
            line_net = Money(amount=line_net, currency=currency)
            return TaxedMoney(net=line_net, gross=line_gross)

    total = checkout_line.get_total(discounts)
    return TaxedMoney(net=total, gross=total)


def calculate_order_line_unit(order_line: "OrderLine"):
    order = order_line.order
    if _validate_order(order):
        taxes_data = get_order_tax_data(order)
        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line.get("itemCode") == order_line.variant.sku:
                tax = Decimal(line.get("tax", 0.0)) / order_line.quantity
                net = Decimal(line.get("lineAmount", 0.0)) / order_line.quantity

                gross = Money(amount=net + tax, currency=currency)
                net = Money(amount=net, currency=currency)
                return TaxedMoney(net=net, gross=gross)
    return order_line.unit_price


def calculate_order_shipping(order: "Order"):
    if not _validate_order(order):
        return zero_taxed_money(order.total.currency)
    taxes_data = get_order_tax_data(order, False)
    currency = taxes_data.get("currencyCode")
    for line in taxes_data.get("lines", []):
        if line["itemCode"] == "Shipping":
            tax = Decimal(line.get("tax", 0.0))
            net = Decimal(line.get("lineAmount", 0.0))
            gross = Money(amount=net + tax, currency=currency)
            net = Money(amount=net, currency=currency)
            return TaxedMoney(net=net, gross=gross)
    return TaxedMoney(
        net=order.shipping_method.price, gross=order.shipping_method.price
    )


def get_tax_rate_type_choices() -> List[TaxType]:
    return [
        TaxType(code=tax_code, description=desc)
        for tax_code, desc in get_cached_tax_codes_or_fetch().items()
    ]


def assign_tax_to_object_meta(obj: Union["Product", "ProductType"], tax_code: str):
    codes = get_cached_tax_codes_or_fetch()
    if tax_code not in codes:
        return

    tax_description = codes[tax_code]
    if not hasattr(obj, "meta"):
        return
    if "taxes" not in obj.meta:
        obj.meta["taxes"] = {}
    obj.meta["taxes"]["avatax"] = {"code": tax_code, "description": tax_description}


def get_tax_from_object_meta(obj: Union["Product", "ProductType"]) -> TaxType:
    if not hasattr(obj, "meta"):
        return TaxType(code="", description="")

    tax = obj.meta.get("taxes", {}).get(META_FIELD, {})
    return TaxType(code=tax.get("code", ""), description=tax.get("description", ""))
