from collections import defaultdict
from typing import Iterable

from django_prices.templatetags import prices_i18n

from ...core.taxes import display_gross_prices
from ...core.taxes.interface import apply_taxes_to_product, show_taxes_on_storefront
from ...core.utils import to_local_currency
from ...discount import DiscountInfo
from ...seo.schema.product import variant_json_ld
from .availability import get_product_availability


def get_variant_picker_data(
    product,
    discounts: Iterable[DiscountInfo] = None,
    taxes=None,
    local_currency=None,
    country=None,
):
    availability = get_product_availability(
        product, discounts, country, local_currency, taxes
    )
    variants = product.variants.all()
    data = {"variantAttributes": [], "variants": []}

    variant_attributes = product.product_type.variant_attributes.all()
    print("这是product--------------------")
    print(product)
    print(variant_attributes)
    # Collect only available variants
    filter_available_variants = defaultdict(list)

    for variant in variants:
        data['testtest'] = 'ddddddddddddcdd' 
        price = apply_taxes_to_product(
            variant.product, variant.get_price(discounts), country, taxes=taxes
        )
        price_undiscounted = apply_taxes_to_product(
            variant.product, variant.get_price(), country, taxes=taxes
        )
        if local_currency:
            price_local_currency = to_local_currency(price, local_currency)
        else:
            price_local_currency = None
        in_stock = variant.is_in_stock()
        schema_data = variant_json_ld(price.net, variant, in_stock)
        variant_data = {
            "id": variant.id,
            "availability": in_stock,
            "price": price_as_dict(price),
            "priceUndiscounted": price_as_dict(price_undiscounted),
            "attributes": variant.attributes,
            "priceLocalCurrency": price_as_dict(price_local_currency),
            "schemaData": schema_data,
            'dkftest':variant.dkftest,
        }
        data["variants"].append(variant_data)

        for variant_key, variant_value in variant.attributes.items():
            filter_available_variants[int(variant_key)].append(int(variant_value))

    for attribute in variant_attributes:
        available_variants = filter_available_variants.get(attribute.pk, None)

        if available_variants:
            data["variantAttributes"].append(
                {
                    "pk": attribute.pk,
                    "name": attribute.translated.name,
                    "slug": attribute.translated.slug,
                    "values": [
                        {
                            "pk": value.pk,
                            "name": value.translated.name,
                            "slug": value.translated.slug,
                            "type_ini":value.translated.type_ini,
                        }
                        for value in attribute.values.filter(
                            pk__in=available_variants
                        ).prefetch_related("translations")
                    ],
                }
            )

    product_price = apply_taxes_to_product(product, product.price, country, taxes=taxes)
    tax_rates = 0
    if product_price.tax and product_price.net:
        tax_rates = int((product_price.tax / product_price.net) * 100)

    data["availability"] = {
        "discount": price_as_dict(availability.discount),
        "taxRate": tax_rates,
        "priceRange": price_range_as_dict(availability.price_range),
        "priceRangeUndiscounted": price_range_as_dict(
            availability.price_range_undiscounted
        ),
        "priceRangeLocalCurrency": price_range_as_dict(
            availability.price_range_local_currency
        ),
    }
    data["priceDisplay"] = {
        "displayGross": display_gross_prices(),
        "handleTaxes": show_taxes_on_storefront(),
    }
    return data


def price_as_dict(price):
    if price is None:
        return None
    return {
        "currency": price.currency,
        "gross": price.gross.amount,
        "grossLocalized": prices_i18n.amount(price.gross),
        "net": price.net.amount,
        "netLocalized": prices_i18n.amount(price.net),
    }


def price_range_as_dict(price_range):
    if not price_range:
        return None
    return {
        "minPrice": price_as_dict(price_range.start),
        "maxPrice": price_as_dict(price_range.stop),
    }
