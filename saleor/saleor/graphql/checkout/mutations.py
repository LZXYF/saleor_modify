import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ...checkout import models
from ...checkout.utils import (
    abort_order_data,
    add_promo_code_to_checkout,
    add_variant_to_checkout,
    add_voucher_to_checkout,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clean_checkout,
    create_order,
    get_or_create_user_checkout,
    get_voucher_for_checkout,
    prepare_order_data,
    recalculate_checkout_discount,
    remove_promo_code_from_checkout,
    remove_voucher_from_checkout,
)
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...core.taxes.errors import TaxError
from ...core.taxes.interface import calculate_checkout_subtotal
from ...discount import models as voucher_model
from ...payment import PaymentError
from ...payment.interface import AddressData
from ...payment.utils import gateway_process_payment, store_customer_id
from ...shipping.models import ShippingMethod as ShippingMethodModel
from ..account.i18n import I18nMixin
from ..account.types import AddressInput, User
from ..core.mutations import BaseMutation, ModelMutation
from ..core.utils import from_global_id_strict_type
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from .types import Checkout, CheckoutLine


def clean_shipping_method(checkout, method, discounts, country_code=None, remove=True):
    # FIXME Add tests for this function
    if not method:
        return None

    if not checkout.is_shipping_required():
        raise ValidationError("This checkout does not requires shipping.")

    if not checkout.shipping_address:
        raise ValidationError(
            "Cannot choose a shipping method for a checkout without the "
            "shipping address."
        )

    valid_methods = ShippingMethodModel.objects.applicable_shipping_methods(
        price=calculate_checkout_subtotal(checkout, discounts).gross.amount,
        weight=checkout.get_total_weight(),
        country_code=country_code or checkout.shipping_address.country.code,
    )
    valid_methods = valid_methods.values_list("id", flat=True)

    if method.pk not in valid_methods and not remove:
        raise ValidationError("Shipping method cannot be used with this checkout.")

    if remove:
        checkout.shipping_method = None
        checkout.save(update_fields=["shipping_method"])


def check_lines_quantity(variants, quantities):
    """Check if stock is sufficient for each line in the list of dicts."""
    for variant, quantity in zip(variants, quantities):
        if quantity > settings.MAX_CHECKOUT_LINE_QUANTITY:
            raise ValidationError(
                {
                    "quantity": "Cannot add more than %d times this item."
                    "" % settings.MAX_CHECKOUT_LINE_QUANTITY
                }
            )
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            message = (
                "Could not add item "
                + "%(item_name)s. Only %(remaining)d remaining in stock."
                % {
                    "remaining": e.item.quantity_available,
                    "item_name": e.item.display_product(),
                }
            )
            raise ValidationError({"quantity": message})


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(required=True, description="The number of items purchased.")
    variant_id = graphene.ID(required=True, description="ID of the ProductVariant.")


class CheckoutCreateInput(graphene.InputObjectType):
    lines = graphene.List(
        CheckoutLineInput,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
        required=True,
    )
    email = graphene.String(description="The customer's email address.")
    shipping_address = AddressInput(
        description=("The mailing address to where the checkout will be shipped.")
    )
    billing_address = AddressInput(description="Billing address of the customer.")


class CheckoutCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description="Fields required to create checkout."
        )

    class Meta:
        description = "Create a new checkout."
        model = models.Checkout
        return_field_name = "checkout"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        user = info.context.user
        lines = data.pop("lines", None)
        if lines:
            variant_ids = [line.get("variant_id") for line in lines]
            variants = cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)
            quantities = [line.get("quantity") for line in lines]

            check_lines_quantity(variants, quantities)

            cleaned_input["variants"] = variants
            cleaned_input["quantities"] = quantities

        default_shipping_address = None
        default_billing_address = None
        if user.is_authenticated:
            default_billing_address = user.default_billing_address
            default_shipping_address = user.default_shipping_address

        if "shipping_address" in data:
            shipping_address = cls.validate_address(data["shipping_address"])
            cleaned_input["shipping_address"] = shipping_address
        else:
            cleaned_input["shipping_address"] = default_shipping_address

        if "billing_address" in data:
            billing_address = cls.validate_address(data["billing_address"])
            cleaned_input["billing_address"] = billing_address
        else:
            cleaned_input["billing_address"] = default_billing_address

        # Use authenticated user's email as default email
        if user.is_authenticated:
            email = data.pop("email", None)
            cleaned_input["email"] = email or user.email

        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        shipping_address = cleaned_input.get("shipping_address")
        billing_address = cleaned_input.get("billing_address")
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

        instance.save()

        variants = cleaned_input.get("variants")
        quantities = cleaned_input.get("quantities")
        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_checkout(instance, variant, quantity)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user

        # `perform_mutation` is overridden to properly get or create a checkout
        # instance here and abort mutation if needed.
        if user.is_authenticated:
            checkout, created = get_or_create_user_checkout(user)
            # If user has an active checkout, return it without any
            # modifications.
            if not created:
                return CheckoutCreate(checkout=checkout)
        else:
            checkout = models.Checkout()

        cleaned_input = cls.clean_input(info, checkout, data.get("input"))
        checkout = cls.construct_instance(checkout, cleaned_input)
        cls.clean_instance(checkout)
        cls.save(info, checkout, cleaned_input)
        cls._save_m2m(info, checkout, cleaned_input)
        return CheckoutCreate(checkout=checkout)


class CheckoutLinesAdd(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated Checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="The ID of the Checkout.", required=True)
        lines = graphene.List(
            CheckoutLineInput,
            required=True,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        )

    class Meta:
        description = "Adds a checkout line to the existing checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, lines, replace=False):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        variant_ids = [line.get("variant_id") for line in lines]
        variants = cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)
        quantities = [line.get("quantity") for line in lines]

        check_lines_quantity(variants, quantities)

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout,
            method=checkout.shipping_method,
            discounts=info.context.discounts,
        )

        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                add_variant_to_checkout(checkout, variant, quantity, replace=replace)

        recalculate_checkout_discount(checkout, info.context.discounts)

        return CheckoutLinesAdd(checkout=checkout)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description="An updated Checkout.")

    class Meta:
        description = "Updates CheckoutLine in the existing Checkout."

    @classmethod
    def perform_mutation(cls, root, info, checkout_id, lines):
        return super().perform_mutation(root, info, checkout_id, lines, replace=True)


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="The ID of the Checkout.", required=True)
        line_id = graphene.ID(description="ID of the CheckoutLine to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, line_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field="line_id"
        )

        if line and line in checkout.lines.all():
            line.delete()

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout,
            method=checkout.shipping_method,
            discounts=info.context.discounts,
        )

        recalculate_checkout_discount(checkout, info.context.discounts)

        return CheckoutLineDelete(checkout=checkout)


class CheckoutCustomerAttach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the Checkout.")
        customer_id = graphene.ID(required=True, description="The ID of the customer.")

    class Meta:
        description = "Sets the customer as the owner of the Checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, customer_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        customer = cls.get_node_or_error(
            info, customer_id, only_type=User, field="customer_id"
        )
        checkout.user = customer
        checkout.save(update_fields=["user"])
        return CheckoutCustomerAttach(checkout=checkout)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID", required=True)

    class Meta:
        description = "Removes the user assigned as the owner of the checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        checkout.user = None
        checkout.save(update_fields=["user"])
        return CheckoutCustomerDetach(checkout=checkout)


class CheckoutShippingAddressUpdate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="An updated checkout")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the Checkout.")
        shipping_address = AddressInput(
            required=True,
            description="The mailing address to where the checkout will be shipped.",
        )

    class Meta:
        description = "Update shipping address in the existing Checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_address):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        shipping_address = cls.validate_address(
            shipping_address, instance=checkout.shipping_address
        )

        # FIXME test if below function is called
        clean_shipping_method(
            checkout=checkout,
            method=checkout.shipping_method,
            discounts=info.context.discounts,
        )

        with transaction.atomic():
            shipping_address.save()
            change_shipping_address_in_checkout(checkout, shipping_address)
        recalculate_checkout_discount(checkout, info.context.discounts)

        return CheckoutShippingAddressUpdate(checkout=checkout)


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description="An updated checkout")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the Checkout.")
        billing_address = AddressInput(
            required=True, description=("The billing address of the checkout.")
        )

    class Meta:
        description = "Update billing address in the existing Checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, billing_address):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        billing_address = cls.validate_address(
            billing_address, instance=checkout.billing_address
        )
        with transaction.atomic():
            billing_address.save()
            change_billing_address_in_checkout(checkout, billing_address)
        return CheckoutBillingAddressUpdate(checkout=checkout)


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID")
        email = graphene.String(required=True, description="email")

    class Meta:
        description = "Updates email address in the existing Checkout object."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, email):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        checkout.email = email
        cls.clean_instance(checkout)
        checkout.save(update_fields=["email"])
        return CheckoutEmailUpdate(checkout=checkout)


class CheckoutShippingMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID")
        shipping_method_id = graphene.ID(required=True, description="Shipping method")

    class Meta:
        description = "Updates the shipping address of the checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_method_id):
        checkout_id = from_global_id_strict_type(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        checkout = models.Checkout.objects.prefetch_related(
            "lines__variant__product__collections"
        ).get(pk=checkout_id)
        shipping_method = cls.get_node_or_error(
            info,
            shipping_method_id,
            only_type=ShippingMethod,
            field="shipping_method_id",
        )

        clean_shipping_method(
            checkout=checkout,
            method=shipping_method,
            discounts=info.context.discounts,
            remove=False,
        )

        checkout.shipping_method = shipping_method
        checkout.save(update_fields=["shipping_method"])
        recalculate_checkout_discount(checkout, info.context.discounts)

        return CheckoutShippingMethodUpdate(checkout=checkout)


class CheckoutComplete(BaseMutation):
    order = graphene.Field(Order, description="Placed order")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID", required=True)
        store_source = graphene.Boolean(
            default_value=False,
            description=(
                "Determines whether to store the payment source for future usage."
            ),
        )

    class Meta:
        description = (
            "Completes the checkout. As a result a new order is created and "
            "a payment charge is made. This action requires a successful "
            "payment before it can be performed."
        )

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, store_source):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        user = info.context.user
        clean_checkout(checkout, info.context.discounts)

        payment = checkout.get_last_active_payment()

        with transaction.atomic():
            try:
                order_data = prepare_order_data(
                    checkout=checkout,
                    tracking_code=analytics.get_client_id(info.context),
                    discounts=info.context.discounts,
                )
            except InsufficientStock as e:
                raise ValidationError(f"Insufficient product stock: {e.item}")
            except voucher_model.NotApplicable:
                raise ValidationError("Voucher not applicable")
            except TaxError as tax_error:
                return ValidationError(
                    "Unable to calculate taxes - %s" % str(tax_error)
                )

        try:
            billing_address = order_data["billing_address"]  # type: models.Address
            shipping_address = order_data["shipping_address"]  # type: models.Address
            txn = gateway_process_payment(
                payment=payment,
                payment_token=payment.token,
                billing_address=AddressData(**billing_address.as_data()),
                shipping_address=AddressData(**shipping_address.as_data()),
                store_source=store_source,
            )
            if txn.is_success and txn.customer_id and user.is_authenticated:
                store_customer_id(user, payment.gateway, txn.customer_id)

        except PaymentError as e:
            abort_order_data(order_data)
            raise ValidationError(str(e))

        # create the order into the database
        order = create_order(checkout=checkout, order_data=order_data, user=user)

        # remove checkout after order is successfully paid
        checkout.delete()

        # return the success response with the newly created order data
        return CheckoutComplete(order=order)


class CheckoutUpdateVoucher(BaseMutation):
    checkout = graphene.Field(Checkout, description="An checkout with updated voucher")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID", required=True)
        voucher_code = graphene.String(description="Voucher code")

    class Meta:
        description = (
            "DEPRECATED: Use CheckoutAddPromoCode or CheckoutRemovePromoCode instead. "
            "Adds voucher to the checkout. Query it without voucher_code "
            "field to remove voucher from checkout."
        )

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, voucher_code=None):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        if voucher_code:
            try:
                voucher = voucher_model.Voucher.objects.active(date=timezone.now()).get(
                    code=voucher_code
                )
            except voucher_model.Voucher.DoesNotExist:
                raise ValidationError(
                    {"voucher_code": "Voucher with given code does not exist."}
                )

            try:
                add_voucher_to_checkout(checkout, voucher)
            except voucher_model.NotApplicable:
                raise ValidationError(
                    {"voucher_code": "Voucher is not applicable to that checkout."}
                )
        else:
            existing_voucher = get_voucher_for_checkout(checkout)
            if existing_voucher:
                remove_voucher_from_checkout(checkout)

        return CheckoutUpdateVoucher(checkout=checkout)


class CheckoutAddPromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher"
    )

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID", required=True)
        promo_code = graphene.String(
            description="Gift card code or voucher code", required=True
        )

    class Meta:
        description = "Adds a gift card or a voucher to a checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, promo_code):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        add_promo_code_to_checkout(checkout, promo_code, info.context.discounts)
        return CheckoutAddPromoCode(checkout=checkout)


class CheckoutRemovePromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher"
    )

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID", required=True)
        promo_code = graphene.String(
            description="Gift card code or voucher code", required=True
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, promo_code):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        remove_promo_code_from_checkout(checkout, promo_code)
        return CheckoutUpdateVoucher(checkout=checkout)
