import pytest
from django.conf import settings
from graphene import Node
from prices import TaxedMoney

from saleor.checkout.utils import add_variant_to_checkout
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.models import Payment
from tests.api.utils import get_graphql_content


@pytest.fixture()
def checkout_with_variant(checkout, variant):
    add_variant_to_checkout(checkout, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_shipping_method(checkout_with_variant, shipping_method):
    checkout = checkout_with_variant

    checkout.shipping_method = shipping_method
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_charged_payment(checkout_with_billing_address):
    checkout = checkout_with_billing_address

    total = checkout.get_total()
    taxed_total = TaxedMoney(total, total)
    payment = Payment.objects.create(
        gateway=settings.DUMMY,
        is_active=True,
        total=taxed_total.gross.amount,
        currency="USD",
    )

    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.checkout = checkout_with_billing_address
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    return checkout


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_checkout(api_client, graphql_address_data, variant, count_queries):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
          }
          currency
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
          }
          product {
            id
            name
            thumbnail {
              url
              alt
            }
            thumbnail2x: thumbnail(size: 510) {
              url
            }
          }
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

        fragment Address on Address {
          id
          firstName
          lastName
          companyName
          streetAddress1
          streetAddress2
          city
          postalCode
          country {
            code
            country
          }
          countryArea
          phone
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
          }
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
        }

        mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
          checkoutCreate(input: $checkoutInput) {
            errors {
              field
              message
            }
            checkout {
              ...Checkout
            }
          }
        }
    """
    variables = {
        "checkoutInput": {
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "lines": [
                {
                    "quantity": 1,
                    "variantId": Node.to_global_id("ProductVariant", variant.pk),
                }
            ],
        }
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_shipping_to_checkout(
    api_client,
    graphql_address_data,
    variant,
    checkout_with_variant,
    shipping_method,
    count_queries,
):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
          }
          currency
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
          }
          product {
            id
            name
            thumbnail {
              url
              alt
            }
            thumbnail2x: thumbnail(size: 510) {
              url
            }
          }
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

        fragment Address on Address {
          id
          firstName
          lastName
          companyName
          streetAddress1
          streetAddress2
          city
          postalCode
          country {
            code
            country
          }
          countryArea
          phone
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
          }
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
        }

        mutation updateCheckoutShippingOptions(
          $checkoutId: ID!
          $shippingMethodId: ID!
        ) {
          checkoutShippingMethodUpdate(
            checkoutId: $checkoutId
            shippingMethodId: $shippingMethodId
          ) {
            errors {
              field
              message
            }
            checkout {
              ...Checkout
            }
          }
        }
    """
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_variant.pk),
        "shippingMethodId": Node.to_global_id("ShippingMethod", shipping_method.pk),
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_billing_address_to_checkout(
    api_client, graphql_address_data, checkout_with_shipping_method, count_queries
):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
          }
          currency
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
          }
          product {
            id
            name
            thumbnail {
              url
              alt
            }
            thumbnail2x: thumbnail(size: 510) {
              url
            }
          }
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

        fragment Address on Address {
          id
          firstName
          lastName
          companyName
          streetAddress1
          streetAddress2
          city
          postalCode
          country {
            code
            country
          }
          countryArea
          phone
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
          }
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
        }

        mutation updateCheckoutBillingAddress(
          $checkoutId: ID!
          $billingAddress: AddressInput!
        ) {
          checkoutBillingAddressUpdate(
            checkoutId: $checkoutId
            billingAddress: $billingAddress
          ) {
            errors {
              field
              message
            }
            checkout {
              ...Checkout
            }
          }
        }
    """
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_shipping_method.pk),
        "billingAddress": graphql_address_data,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_payment_charge(
    api_client, graphql_address_data, checkout_with_billing_address, count_queries
):
    query = """
        mutation createPayment($input: PaymentInput!, $checkoutId: ID!) {
          checkoutPaymentCreate(input: $input, checkoutId: $checkoutId) {
            errors {
              field
              message
            }
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_billing_address.pk),
        "input": {
            "billingAddress": graphql_address_data,
            "amount": 1000,  # 10.00 USD * 100
            "gateway": settings.DUMMY.upper(),
            "token": "charged",
        },
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout(api_client, checkout_with_charged_payment, count_queries):
    query = """
        mutation completeCheckout($checkoutId: ID!) {
          checkoutComplete(checkoutId: $checkoutId) {
            errors {
              field
              message
            }
            order {
              id
              token
            }
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_charged_payment.pk)
    }

    get_graphql_content(api_client.post_graphql(query, variables))
