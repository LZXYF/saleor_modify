from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator
from django.urls import reverse, reverse_lazy
from django.utils.translation import npgettext_lazy, pgettext_lazy

from ...account.i18n import (
    AddressForm as StorefrontAddressForm,
    PossiblePhoneNumberFormField,
)
from ...account.models import User
from ...checkout.forms import QuantityField
from ...core.exceptions import InsufficientStock
from ...core.taxes import interface as tax_interface, zero_taxed_money
from ...discount.models import Voucher
from ...discount.utils import decrease_voucher_usage, increase_voucher_usage
from ...order import OrderStatus, events
from ...order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ...order.utils import (
    add_variant_to_order,
    cancel_fulfillment,
    cancel_order,
    change_order_line_quantity,
    fulfill_order_line,
    recalculate_order,
)
from ...payment import ChargeStatus, CustomPaymentChoices, PaymentError
from ...payment.utils import (
    clean_mark_order_as_paid,
    gateway_capture,
    gateway_refund,
    gateway_void,
    mark_order_as_paid,
)
from ...product.models import Product, ProductVariant
from ...product.utils import allocate_stock, deallocate_stock
from ...shipping.models import ShippingMethod
from ..forms import AjaxSelect2ChoiceField
from ..widgets import PhonePrefixWidget
from .utils import remove_customer_from_order, update_order_with_user_addresses


class CreateOrderFromDraftForm(forms.ModelForm):
    """Mark draft order as ready to fulfill."""

    notify_customer = forms.BooleanField(
        label=pgettext_lazy(
            "Send email to customer about order created by staff users",
            "Send email with order confirmation to the customer",
        ),
        required=False,
        initial=True,
    )

    class Meta:
        model = Order
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.get_user_current_email():
            self.fields.pop("notify_customer")

    def clean(self):
        super().clean()
        errors = []
        if self.instance.get_total_quantity() == 0:
            errors.append(
                forms.ValidationError(
                    pgettext_lazy(
                        "Create draft order form error",
                        "Could not create order without any products",
                    )
                )
            )
        if self.instance.is_shipping_required():
            method = self.instance.shipping_method
            shipping_address = self.instance.shipping_address
            shipping_not_valid = (
                method
                and shipping_address
                and shipping_address.country.code not in method.shipping_zone.countries
            )  # noqa
            if shipping_not_valid:
                errors.append(
                    forms.ValidationError(
                        pgettext_lazy(
                            "Create draft order form error",
                            "Shipping method is not valid for chosen shipping "
                            "address",
                        )
                    )
                )
        if errors:
            raise forms.ValidationError(errors)
        return self.cleaned_data

    def save(self):
        self.instance.status = OrderStatus.UNFULFILLED
        if self.instance.user:
            self.instance.user_email = self.instance.user.email
        remove_shipping_address = False
        if not self.instance.is_shipping_required():
            self.instance.shipping_method_name = None
            self.instance.shipping_price = zero_taxed_money()
            if self.instance.shipping_address:
                remove_shipping_address = True
        super().save()
        if remove_shipping_address:
            self.instance.shipping_address.delete()
        return self.instance


class OrderCustomerForm(forms.ModelForm):
    """Set customer details in an order."""

    update_addresses = forms.BooleanField(
        label=pgettext_lazy(
            "Update an order with user default addresses",
            "Set billing and shipping address in order to customer defaults",
        ),
        initial=True,
        required=False,
    )
    user = AjaxSelect2ChoiceField(
        queryset=User.objects.all(),
        fetch_data_url=reverse_lazy("dashboard:ajax-users-list"),
        required=False,
        label=pgettext_lazy(
            "Order form: editing customer details - selecting a customer", "Customer"
        ),
    )

    class Meta:
        model = Order
        fields = ["user", "user_email"]
        labels = {"user_email": pgettext_lazy("Order customer email", "Email")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        if user:
            self.fields["user"].set_initial(user, label=user.get_ajax_label())

    def clean(self):
        cleaned_data = super().clean()
        user_email = cleaned_data.get("user_email")
        user = cleaned_data.get("user")
        if user and user_email:
            raise forms.ValidationError(
                pgettext_lazy(
                    "Edit customer details in order form error",
                    "An order can be related either with an email or an existing "
                    "user account",
                )
            )
        return self.cleaned_data

    def save(self):
        super().save()
        if self.cleaned_data.get("update_addresses"):
            update_order_with_user_addresses(self.instance)
        return self.instance


class OrderRemoveCustomerForm(forms.ModelForm):
    """Remove customer data from an order."""

    class Meta:
        model = Order
        fields = []

    def save(self):
        remove_customer_from_order(self.instance)
        return self.instance


class OrderShippingForm(forms.ModelForm):
    """Set shipping name and shipping price in an order."""

    shipping_method = AjaxSelect2ChoiceField(
        queryset=ShippingMethod.objects.all(),
        min_input=0,
        label=pgettext_lazy("Shipping method form field label", "Shipping method"),
    )

    class Meta:
        model = Order
        fields = ["shipping_method"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        method_field = self.fields["shipping_method"]
        fetch_data_url = reverse(
            "dashboard:ajax-order-shipping-methods",
            kwargs={"order_pk": self.instance.id},
        )
        method_field.set_fetch_data_url(fetch_data_url)

        method = self.instance.shipping_method
        if method:
            method_field.set_initial(method, label=method.get_ajax_label())

        if self.instance.shipping_address:
            country_code = self.instance.shipping_address.country.code
            queryset = method_field.queryset.filter(
                shipping_zone__countries__contains=country_code
            )
            method_field.queryset = queryset

    def save(self, commit=True):
        method = self.instance.shipping_method
        self.instance.shipping_method_name = method.name
        self.instance.shipping_price = tax_interface.calculate_order_shipping(
            self.instance
        )
        recalculate_order(self.instance)
        return super().save(commit)


class OrderRemoveShippingForm(forms.ModelForm):
    """Remove shipping name and shipping price from an order."""

    class Meta:
        model = Order
        fields = []

    def save(self, commit=True):
        self.instance.shipping_method = None
        self.instance.shipping_method_name = None
        self.instance.shipping_price = zero_taxed_money()
        recalculate_order(self.instance)
        return super().save(commit)


class OrderEditDiscountForm(forms.ModelForm):
    """Edit discount amount in an order."""

    class Meta:
        model = Order
        fields = ["discount_amount"]
        labels = {
            "discount_amount": pgettext_lazy(
                "Order discount amount fixed value", "Discount amount"
            )
        }

    def save(self, commit=True):
        recalculate_order(self.instance, update_voucher_discount=False)
        return super().save(commit)


class OrderEditVoucherForm(forms.ModelForm):
    """Edit discount amount in an order."""

    voucher = AjaxSelect2ChoiceField(
        queryset=Voucher.objects.all(),
        fetch_data_url=reverse_lazy("dashboard:ajax-vouchers"),
        min_input=0,
        label=pgettext_lazy("Order voucher", "Voucher"),
    )

    class Meta:
        model = Order
        fields = ["voucher"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_voucher = self.instance.voucher
        if self.instance.voucher:
            self.fields["voucher"].set_initial(self.instance.voucher)

    def save(self, commit=True):
        voucher = self.instance.voucher
        if self.old_voucher != voucher:
            if self.old_voucher:
                decrease_voucher_usage(self.old_voucher)
            increase_voucher_usage(voucher)
        self.instance.discount_name = voucher.name or ""
        self.instance.translated_discount_name = (
            voucher.translated.name if voucher.translated.name != voucher.name else ""
        )
        recalculate_order(self.instance)
        return super().save(commit)


class OrderNoteForm(forms.Form):
    message = forms.CharField(
        label=pgettext_lazy("Order note", "Note"), widget=forms.Textarea()
    )


class BasePaymentForm(forms.Form):

    amount = forms.DecimalField(
        label=pgettext_lazy(
            "Payment management form (capture, refund, void)", "Amount"
        ),
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    clean_error = pgettext_lazy(
        "Payment form error", "This payment action can not be performed."
    )

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop("payment")
        super().__init__(*args, **kwargs)

    def payment_error(self, message):
        self.add_error(
            None,
            pgettext_lazy("Payment form error", "Payment gateway error: %s") % message,
        )

    def try_payment_action(self, user, action, *args):
        try:
            action(self.payment, *args)
        except (PaymentError, ValueError) as e:
            message = str(e)
            self.payment_error(message)
            events.payment_failed_event(
                order=self.payment.order,
                user=user,
                message=message,
                payment=self.payment,
            )
            return False
        return True


class CapturePaymentForm(BasePaymentForm):

    clean_error = pgettext_lazy(
        "Payment form error", "Only pre-authorized payments can be captured"
    )

    def clean(self):
        if not self.payment.can_capture():
            raise forms.ValidationError(self.clean_error)

    def capture(self, user):
        return self.try_payment_action(
            user, gateway_capture, self.cleaned_data["amount"]
        )


class RefundPaymentForm(BasePaymentForm):

    clean_error = pgettext_lazy(
        "Payment form error", "Only confirmed payments can be refunded"
    )

    def clean(self):
        if not self.payment.can_refund():
            raise forms.ValidationError(self.clean_error)

        if self.payment.gateway == CustomPaymentChoices.MANUAL:
            raise forms.ValidationError(
                pgettext_lazy(
                    "Payment form error", "Manual payments can not be refunded"
                )
            )

    def refund(self, user):
        return self.try_payment_action(
            user, gateway_refund, self.cleaned_data["amount"]
        )


class VoidPaymentForm(BasePaymentForm):

    clean_error = pgettext_lazy(
        "Payment form error", "Only pre-authorized payments can be voided"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment = kwargs.pop("payment")
        # The amount field is popped out
        # since there is no amount argument for void operation
        self.fields.pop("amount")

    def clean(self):
        if not self.payment.can_void():
            raise forms.ValidationError(self.clean_error)

    def void(self, user):
        return self.try_payment_action(user, gateway_void)


class OrderMarkAsPaidForm(forms.Form):
    """Mark order as manually paid."""

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        try:
            clean_mark_order_as_paid(self.order)
        except PaymentError as e:
            raise forms.ValidationError(str(e))

    def save(self):
        mark_order_as_paid(self.order, self.user)


class CancelOrderLineForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop("line")
        super().__init__(*args, **kwargs)

    def cancel_line(self, user):
        if self.line.variant and self.line.variant.track_inventory:
            deallocate_stock(self.line.variant, self.line.quantity)
        order = self.line.order
        change_order_line_quantity(user, self.line, self.line.quantity, 0)
        recalculate_order(order)


class ChangeQuantityForm(forms.ModelForm):
    quantity = QuantityField(
        validators=[MinValueValidator(1)],
        label=pgettext_lazy("Integer number", "Quantity"),
    )

    class Meta:
        model = OrderLine
        fields = ["quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_quantity = self.instance.quantity
        self.fields["quantity"].initial = self.initial_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        delta = quantity - self.initial_quantity
        variant = self.instance.variant
        if variant and delta > variant.quantity_available:
            raise forms.ValidationError(
                npgettext_lazy(
                    "Change quantity form error",
                    "Only %(remaining)d remaining in stock.",
                    "Only %(remaining)d remaining in stock.",
                    number="remaining",
                )
                % {"remaining": (self.initial_quantity + variant.quantity_available)}
            )  # noqa
        return quantity

    def save(self, user):
        quantity = self.cleaned_data["quantity"]
        variant = self.instance.variant
        if variant and variant.track_inventory:
            # update stock allocation
            delta = quantity - self.initial_quantity
            allocate_stock(variant, delta)
        change_order_line_quantity(user, self.instance, self.initial_quantity, quantity)
        recalculate_order(self.instance.order)
        return self.instance


class CancelOrderForm(forms.Form):
    """Allow canceling an entire order.

    Deallocate or increase corresponding stocks for each order line.
    """

    restock = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order")
        super().__init__(*args, **kwargs)
        self.fields["restock"].label = npgettext_lazy(
            "Cancel order form action",
            "Restock %(quantity)d item",
            "Restock %(quantity)d items",
            number="quantity",
        ) % {"quantity": self.order.get_total_quantity()}

    def clean(self):
        data = super().clean()
        if not self.order.can_cancel():
            raise forms.ValidationError(
                pgettext_lazy("Cancel order form error", "This order can't be canceled")
            )
        return data

    def cancel_order(self, user):
        cancel_order(user, self.order, self.cleaned_data.get("restock"))


class CancelFulfillmentForm(forms.Form):
    """Allow canceling an entire fulfillment.

    Increase corresponding stocks for each fulfillment line.
    """

    restock = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        self.fulfillment = kwargs.pop("fulfillment")
        super().__init__(*args, **kwargs)
        self.fields["restock"].label = npgettext_lazy(
            "Cancel fulfillment form action",
            "Restock %(quantity)d item",
            "Restock %(quantity)d items",
            number="quantity",
        ) % {"quantity": self.fulfillment.get_total_quantity()}

    def clean(self):
        data = super().clean()
        if not self.fulfillment.can_edit():
            raise forms.ValidationError(
                pgettext_lazy(
                    "Cancel fulfillment form error",
                    "This fulfillment can't be canceled",
                )
            )
        return data

    def cancel_fulfillment(self, user):
        cancel_fulfillment(user, self.fulfillment, self.cleaned_data.get("restock"))


class FulfillmentTrackingNumberForm(forms.ModelForm):
    """Update tracking number in fulfillment group."""

    send_mail = forms.BooleanField(
        initial=True,
        required=False,
        label=pgettext_lazy(
            "Send mail to customer", "Send notification email to customer"
        ),
    )

    class Meta:
        model = Fulfillment
        fields = ["tracking_number"]
        labels = {
            "tracking_number": pgettext_lazy("Fulfillment record", "Tracking number")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.order.get_user_current_email():
            self.fields.pop("send_mail")


class OrderRemoveVoucherForm(forms.ModelForm):
    """Remove voucher from order. Decrease usage and recalculate order."""

    class Meta:
        model = Order
        fields = []

    def clean(self):
        data = super().clean()
        if not self.instance.voucher:
            raise forms.ValidationError(
                pgettext_lazy("Remove voucher form error", "This order has no voucher")
            )
        return data

    def remove_voucher(self):
        decrease_voucher_usage(self.instance.voucher)
        self.instance.discount_amount = 0
        self.instance.discount_name = ""
        self.instance.translated_discount_name = ""
        self.instance.voucher = None
        recalculate_order(self.instance)


PAYMENT_STATUS_CHOICES = [
    ("", pgettext_lazy("Payment status field value", "All"))
] + ChargeStatus.CHOICES


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(choices=PAYMENT_STATUS_CHOICES)


class AddVariantToOrderForm(forms.Form):
    """Allow adding lines with given quantity to an order."""

    variant = AjaxSelect2ChoiceField(
        queryset=ProductVariant.objects.filter(product__in=Product.objects.published()),
        fetch_data_url=reverse_lazy("dashboard:ajax-available-variants"),
        label=pgettext_lazy(
            "Order form: subform to add variant to order form: variant field", "Variant"
        ),
    )
    quantity = QuantityField(
        label=pgettext_lazy("Add variant to order form label", "Quantity"),
        validators=[MinValueValidator(1)],
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order")
        self.discounts = kwargs.pop("discounts")
        super().__init__(*args, **kwargs)

    def clean(self):
        """Check if given quantity is available in stocks."""
        cleaned_data = super().clean()
        variant = cleaned_data.get("variant")
        quantity = cleaned_data.get("quantity")
        if variant and quantity is not None:
            try:
                variant.check_quantity(quantity)
            except InsufficientStock as e:
                error = forms.ValidationError(
                    pgettext_lazy(
                        "Add item form error",
                        "Could not add item. "
                        "Only %(remaining)d remaining in stock."
                        % {"remaining": e.item.quantity_available},
                    )
                )
                self.add_error("quantity", error)
        return cleaned_data

    def save(self, user):
        """Add variant to order.

        Updates stocks and order.
        """
        variant = self.cleaned_data.get("variant")
        quantity = self.cleaned_data.get("quantity")
        line = add_variant_to_order(self.order, variant, quantity, self.discounts)
        events.draft_order_added_products_event(
            order=self.order, user=user, order_lines=[(line.quantity, line)]
        )
        recalculate_order(self.order)


class AddressForm(StorefrontAddressForm):
    phone = PossiblePhoneNumberFormField(
        widget=PhonePrefixWidget,
        required=False,
        label=pgettext_lazy(
            "Order form: address subform - phone number input field", "Phone number"
        ),
    )

    def clean(self):
        data = super().clean()
        return data


class FulfillmentForm(forms.ModelForm):
    """Create fulfillment group for a given order."""

    send_mail = forms.BooleanField(
        initial=True,
        required=False,
        label=pgettext_lazy(
            "Send mail to customer", "Send shipment details to your customer now"
        ),
    )

    class Meta:
        model = Fulfillment
        fields = ["tracking_number"]
        labels = {
            "tracking_number": pgettext_lazy("Order tracking number", "Tracking number")
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop("order")
        super().__init__(*args, **kwargs)
        self.instance.order = order
        if not order.get_user_current_email():
            self.fields.pop("send_mail")


class BaseFulfillmentLineFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

    def clean(self):
        total_quantity = sum(
            form.cleaned_data.get("quantity", 0) for form in self.forms
        )
        if total_quantity <= 0:
            raise forms.ValidationError("Total quantity must be larger than 0.")


class FulfillmentLineForm(forms.ModelForm):
    """Fulfill order line with given quantity by decreasing stock."""

    class Meta:
        model = FulfillmentLine
        fields = ["order_line", "quantity"]

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        order_line = self.cleaned_data.get("order_line")
        if quantity > order_line.quantity_unfulfilled:
            raise forms.ValidationError(
                npgettext_lazy(
                    "Fulfill order line form error",
                    "%(quantity)d item remaining to fulfill.",
                    "%(quantity)d items remaining to fulfill.",
                    number="quantity",
                )
                % {
                    "quantity": order_line.quantity_unfulfilled,
                    "order_line": order_line,
                }
            )
        return quantity

    def save(self, commit=True):
        fulfill_order_line(self.instance.order_line, self.instance.quantity)
        return super().save(commit)
