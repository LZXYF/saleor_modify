import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.taxes import interface as tax_interface, zero_taxed_money
from ....order import events, models
from ....order.utils import cancel_order, recalculate_order
from ....payment import CustomPaymentChoices, PaymentError
from ....payment.utils import (
    clean_mark_order_as_paid,
    gateway_capture,
    gateway_refund,
    gateway_void,
    mark_order_as_paid,
)
from ....shipping.models import ShippingMethod as ShippingMethodModel
from ...account.types import AddressInput
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...order.mutations.draft_orders import DraftOrderUpdate
from ...order.types import Order, OrderEvent
from ...shipping.types import ShippingMethod


def clean_order_update_shipping(order, method):
    if not order.shipping_address:
        raise ValidationError(
            {
                "order": "Cannot choose a shipping method for an order without "
                "the shipping address."
            }
        )

    valid_methods = ShippingMethodModel.objects.applicable_shipping_methods(
        price=order.get_subtotal().gross.amount,
        weight=order.get_total_weight(),
        country_code=order.shipping_address.country.code,
    )
    valid_methods = valid_methods.values_list("id", flat=True)
    if method.pk not in valid_methods:
        raise ValidationError(
            {"shipping_method": "Shipping method cannot be used with this order."}
        )


def clean_order_cancel(order):
    if order and not order.can_cancel():
        raise ValidationError({"order": "This order can't be canceled."})


def clean_payment(payment):
    if not payment:
        raise ValidationError(
            {"payment": "There's no payment associated with the order."}
        )


def clean_order_capture(payment):
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {"payment": "Only pre-authorized payments can be captured"}
        )


def clean_void_payment(payment):
    """Check for payment errors."""
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError({"payment": "Only pre-authorized payments can be voided"})


def clean_refund_payment(payment):
    clean_payment(payment)
    if payment.gateway == CustomPaymentChoices.MANUAL:
        raise ValidationError({"payment": "Manual payments can not be refunded."})


def try_payment_action(order, user, payment, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_failed_event(
            order=order, user=user, message=message, payment=payment
        )
        raise ValidationError({"payment": message})
    return True


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")


class OrderUpdate(DraftOrderUpdate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an order to update.")
        input = OrderUpdateInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates an order."
        model = models.Order
        permissions = ("order.manage_orders",)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.save()


class OrderUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description="ID of the selected shipping method.", name="shippingMethod"
    )


class OrderUpdateShipping(BaseMutation):
    order = graphene.Field(Order, description="Order with updated shipping method.")

    class Arguments:
        id = graphene.ID(
            required=True,
            name="order",
            description="ID of the order to update a shipping method.",
        )
        input = OrderUpdateShippingInput(
            description="Fields required to change " "shipping method of the order."
        )

    class Meta:
        description = "Updates a shipping method of the order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        data = data.get("input")

        if not data["shipping_method"]:
            if not order.is_draft() and order.is_shipping_required():
                raise ValidationError(
                    {"shipping_method": "Shipping method is required for this order."}
                )

            order.shipping_method = None
            order.shipping_price = zero_taxed_money()
            order.shipping_method_name = None
            order.save(
                update_fields=[
                    "shipping_method",
                    "shipping_price_net",
                    "shipping_price_gross",
                    "shipping_method_name",
                ]
            )
            return OrderUpdateShipping(order=order)

        method = cls.get_node_or_error(
            info,
            data["shipping_method"],
            field="shipping_method",
            only_type=ShippingMethod,
        )

        clean_order_update_shipping(order, method)

        order.shipping_method = method
        order.shipping_price = tax_interface.calculate_order_shipping(order)
        order.shipping_method_name = method.name
        order.save(
            update_fields=[
                "shipping_method",
                "shipping_method_name",
                "shipping_price_net",
                "shipping_price_gross",
            ]
        )
        # Post-process the results
        recalculate_order(order)

        return OrderUpdateShipping(order=order)


class OrderAddNoteInput(graphene.InputObjectType):
    message = graphene.String(description="Note message.", name="message")


class OrderAddNote(BaseMutation):
    order = graphene.Field(Order, description="Order with the note added.")
    event = graphene.Field(OrderEvent, description="Order note created.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the order to add a note for.",
            name="order",
        )
        input = OrderAddNoteInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        description = "Adds note to the order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        event = events.order_note_added_event(
            order=order, user=info.context.user, message=data.get("input")["message"]
        )
        return OrderAddNote(order=order, event=event)


class OrderCancel(BaseMutation):
    order = graphene.Field(Order, description="Canceled order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to cancel.")
        restock = graphene.Boolean(
            required=True, description="Determine if lines will be restocked or not."
        )

    class Meta:
        description = "Cancel an order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, restock, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        clean_order_cancel(order)
        cancel_order(user=info.context.user, order=order, restock=restock)
        return OrderCancel(order=order)


class OrderMarkAsPaid(BaseMutation):
    order = graphene.Field(Order, description="Order marked as paid.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to mark paid.")

    class Meta:
        description = "Mark order as manually paid."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)

        try_payment_action(
            order, info.context.user, None, clean_mark_order_as_paid, order
        )

        mark_order_as_paid(order, info.context.user)
        return OrderMarkAsPaid(order=order)


class OrderCapture(BaseMutation):
    order = graphene.Field(Order, description="Captured order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to capture.")
        amount = Decimal(required=True, description="Amount of money to capture.")

    class Meta:
        description = "Capture an order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, amount, **data):
        if amount <= 0:
            raise ValidationError({"amount": "Amount should be a positive number."})

        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_order_capture(payment)

        try_payment_action(
            order, info.context.user, payment, gateway_capture, payment, amount
        )

        events.payment_captured_event(
            order=order, user=info.context.user, amount=amount, payment=payment
        )
        return OrderCapture(order=order)


class OrderVoid(BaseMutation):
    order = graphene.Field(Order, description="A voided order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to void.")

    class Meta:
        description = "Void an order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_void_payment(payment)

        try_payment_action(order, info.context.user, payment, gateway_void, payment)

        events.payment_voided_event(
            order=order, user=info.context.user, payment=payment
        )
        return OrderVoid(order=order)


class OrderRefund(BaseMutation):
    order = graphene.Field(Order, description="A refunded order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to refund.")
        amount = Decimal(required=True, description="Amount of money to refund.")

    class Meta:
        description = "Refund an order."
        permissions = ("order.manage_orders",)

    @classmethod
    def perform_mutation(cls, _root, info, amount, **data):
        if amount <= 0:
            raise ValidationError({"amount": "Amount should be a positive number."})

        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_refund_payment(payment)

        try_payment_action(
            order, info.context.user, payment, gateway_refund, payment, amount
        )

        events.payment_refunded_event(
            order=order, user=info.context.user, amount=amount, payment=payment
        )
        return OrderRefund(order=order)
