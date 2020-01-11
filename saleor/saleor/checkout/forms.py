"""Checkout-related forms and fields."""
from typing import Any

from django import forms
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_countries.fields import Country, LazyTypedChoiceField

from ..core.exceptions import InsufficientStock
from ..core.taxes import display_gross_prices
from ..core.taxes.interface import apply_taxes_to_shipping, calculate_checkout_subtotal
from ..core.utils import format_money
from ..discount.models import NotApplicable, Voucher
from ..shipping.models import ShippingMethod, ShippingZone
from ..shipping.utils import get_shipping_price_estimate
from .models import Checkout

# 有关上传文件需要导入的东西
import time, re, os, shutil
lecule_num = 10
get_molecule_num = 1
class QuantityField(forms.IntegerField):
    """A specialized integer field with initial quantity and min/max values."""

    def __init__(self, **kwargs):
        super().__init__(
            min_value=0,
            max_value=settings.MAX_CHECKOUT_LINE_QUANTITY,
            initial=1,
            **kwargs,
        )


class AddToCheckoutForm(forms.Form):
    """Add-to-checkout form.

    Allows selection of a product variant and quantity.

    The save method adds it to the checkout.
    """

    quantity = QuantityField(
        label=pgettext_lazy("Add to checkout form field label", "Quantity")
    )
    error_messages = {
        "not-available": pgettext_lazy(
            "Add to checkout form error",
            "Sorry. This product is currently not available.",
        ),
        "empty-stock": pgettext_lazy(
            "Add to checkout form error",
            "Sorry. This product is currently out of stock.",
        ),
        # 有关文件上传的提示信息声明
        'max-molecule-num-reached': pgettext_lazy(
            'Add to cart form error',
            'Please Submit ONE Molecule.'),
        "variant-too-many-in-checkout": pgettext_lazy(
            "Add to checkout form error",
            "Sorry. You can't add more than %d times this item.",
        ),
        "variant-does-not-exists": pgettext_lazy(
            "Add to checkout form error", "Oops. We could not find that product."
        ),
        "insufficient-stock": npgettext_lazy(
            "Add to checkout form error",
            "Only %d remaining in stock.",
            "Only %d remaining in stock.",
        ),
    }
# 修改这里，使能接收上传的文件内容和文件名称
    def __init__(self, *args, **kwargs):
        self.checkout = kwargs.pop("checkout")
        self.product = kwargs.pop("product")
        self.discounts = kwargs.pop("discounts", ())
        self.country = kwargs.pop("country", {})
        self.taxes = kwargs.pop("taxes", None)
        self.upload_file = kwargs.pop('upload_file', {})
        self.user_upload_name = kwargs.pop('user_upload_name', ())
        super().__init__(*args, **kwargs)

    def add_error_i18n(self, field, error_name, fmt: Any = tuple()):
        self.add_error(field, self.error_messages[error_name] % fmt)

    def clean(self):
        """Clean the form.

        Makes sure the total quantity in checkout (taking into account what was
        already there) does not exceed available quantity.
        """
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        if quantity is None:
            return cleaned_data
        variant = self.get_variant(cleaned_data)
        if variant is None:
            self.add_error_i18n(NON_FIELD_ERRORS, "variant-does-not-exists")
        else:
            line = self.checkout.get_line(variant)
            used_quantity = line.quantity if line else 0
            new_quantity = quantity + used_quantity

            if new_quantity > settings.MAX_CHECKOUT_LINE_QUANTITY:
                self.add_error_i18n(
                    "quantity",
                    "variant-too-many-in-checkout",
                    settings.MAX_CHECKOUT_LINE_QUANTITY,
                )
                return cleaned_data

            try:
                # 这里也添加了个if
                if self.user_upload_name != None and self.user_upload_name != '' and self.user_upload_name != ' ':
                    tmp_file = self.handle_uploaded_file(self.upload_file)
                    names = self.get_ids_from_file(tmp_file)
                    if  names == False:
                        msg = self.error_messages['max-molecule-num-reached']
                        self.add_error('quantity', msg)
                    os.system('rm -rf ' + tmp_file)
                variant.check_quantity(new_quantity)
            except InsufficientStock as e:
                remaining = e.item.quantity_available - used_quantity
                if remaining:
                    self.add_error_i18n("quantity", "insufficient-stock", remaining)
                else:
                    self.add_error_i18n("quantity", "empty-stock")
        return cleaned_data

    # 保存这里也要进行修改
    def save(self):
        """Add the selected product variant and quantity to the checkout."""
        from .utils import add_variant_to_checkout
        variant = self.get_variant(self.cleaned_data)
        quantity = self.cleaned_data["quantity"]
        # 增加下面两行代码
        upload_file = self.upload_file
        user_upload_name = self.user_upload_name
        # 第一步先增加参数，第二步再去修改这个函数的内容：在同级目录的utls文件中 
        print("111111111111111111111111111111111111111111")
        print("上传的文件",upload_file)
        print("param_file的类型是：",type(upload_file))

        add_variant_to_checkout(
                self.checkout, 
                variant, 
                quantity,
                param_file=upload_file,
                user_upload_name=user_upload_name
        )

    def get_variant(self, cleaned_data):
        """Return a product variant that matches submitted values.
        This allows specialized implementations to select the variant based on
        multiple fields (like size and color) instead of having a single
        variant selection widget.
        """
        raise NotImplementedError()

    # 有关文件的函数8——检查mol类型文件
    def get_ids_from_sdf_mol(self, file):
        try:
            names = []
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                conts = f.read()
                blocks = conts.split('$$$$')
                if len(blocks) > 2:
                    return False
                num = 1
                for bloc in blocks:
                    if len(bloc) >= 10:
                        t_name = bloc.split()[0]
                        name = re.sub(r, '_', t_name)
                        name = name.replace('\\', '_')
                        names.append(name)
                        num += 1
                    if num > 1:
                        break
                if names == []:
                    return False
                else:
                    return names
        except:
            return False


    # 有关文件的函数10——解析txt类型的文件
    def revise_txt_param(self, filename):
        try:
            with open(filename, 'r', encoding='gbk', errors='ignore') as f:
                ind = 1
                revised_conts = ''
                conts = f.read()
                blocks = conts.split('\n')
                if len(blocks) > 2:
                    return False
                for bloc in blocks:
                    c = ''
                    if len(bloc) >= 1:
                        if len(bloc.split()) == 1:
                            c = bloc.split()[0] + '\tname_' + str(ind) + '\n'
                            ind += 1
                        else:
                            if bloc[-1] != '\n':
                                c = bloc + '\n'
                            else:
                                c = bloc
                        revised_conts += c
            fid = open(filename, 'w')
            fid.write(revised_conts)
            fid.close()
            return True
        except:
            return False
        
    # 有关文件的函数9——检查txt类型的文件
    def get_ids_from_txt(self, file):
        if self.revise_txt_param(file) == False:
            print("解析就返回了False")
            return False
        try:
            names = []
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                conts = f.read()
                blocks = conts.split('\n')
                num = 1
                for bloc in blocks:
                    print("bloc的内容:",bloc)
                    print("bloc的长度：",len(bloc))
                    print("num的值：",num)
                    if len(bloc) >= 1:
                        t_name = bloc.split()[1]
                        name = re.sub(r, '_', t_name)
                        name = name.replace('\\', '_')
                        names.append(name)
                        num += 1
                    if num > get_molecule_num:
                        break
                if names == []:
                    print("names最后是空")
                    return False
                else:
                    return names
        except:
            return False

    # 有关文件的函数7——处理文件类型
    def get_ids_from_file(self, file):
        try:
            ext = os.path.splitext(file)[1][1:]
            if ext == 'sdf' or ext == 'mol':
                print("执行不是txt=====================")
                return self.get_ids_from_sdf_mol(file)
            elif ext == 'txt':
                print("执行的是txt==========================")
                # return self.get_ids_from_txt(file)
                return True   # 这里不进行内容校验
            else:
                print("执行的else===============")
                return False
        except:
            return False


    # 有关上传文件函数6——处理文件上传
    def handle_uploaded_file(self, file):
        temp_name = '/home/dkf/soft/saleor/media/saved_files/param_files/temp_' + str(file)
        destination = open(temp_name,'wb+')
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()
        return temp_name


class ReplaceCheckoutLineForm(AddToCheckoutForm):
    """Replace quantity in checkout form.

    Similar to AddToCheckoutForm but its save method replaces the quantity.
    """

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop("variant")
        super().__init__(*args, product=self.variant.product, **kwargs)
        self.fields["quantity"].widget.attrs = {
            "min": 1,
            "max": settings.MAX_CHECKOUT_LINE_QUANTITY,
        }

    def clean_quantity(self):
        """Clean the quantity field.

        Checks if target quantity does not exceed the currently available
        quantity.
        """
        quantity = self.cleaned_data["quantity"]
        try:
            self.variant.check_quantity(quantity)
        except InsufficientStock as e:
            msg = self.error_messages["insufficient-stock"]
            raise forms.ValidationError(msg % e.item.quantity_available)
        return quantity

    def clean(self):
        """Clean the form skipping the add-to-form checks."""
        # explicitly skip parent's implementation
        # pylint: disable=E1003
        return super(AddToCheckoutForm, self).clean()

    def get_variant(self, cleaned_data):
        """Return the matching variant.

        In this case we explicitly know the variant as we're modifying an
        existing line in checkout.
        """
        return self.variant

    def save(self):
        """Replace the selected product's quantity in checkout."""
        from .utils import add_variant_to_checkout

        variant = self.get_variant(self.cleaned_data)
        quantity = self.cleaned_data["quantity"]
        add_variant_to_checkout(self.checkout, variant, quantity, replace=True)


class CountryForm(forms.Form):
    """Country selection form."""

    country = LazyTypedChoiceField(
        label=pgettext_lazy("Country form field label", "Country"), choices=[]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available_countries = {
            (country.code, country.name)
            for shipping_zone in ShippingZone.objects.all()
            for country in shipping_zone.countries
        }
        self.fields["country"].choices = sorted(
            available_countries, key=lambda choice: choice[1]
        )

    def get_shipping_price_estimate(self, price, weight):
        """Return a shipping price range for given order for the selected
        country.
        """
        country = self.cleaned_data["country"]
        if isinstance(country, str):
            country = Country(country)
        return get_shipping_price_estimate(price, weight, country)


class AnonymousUserShippingForm(forms.ModelForm):
    """Additional shipping information form for users who are not logged in."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "shipping email"}),
        label=pgettext_lazy("Address form field label", "Email"),
    )

    class Meta:
        model = Checkout
        fields = ["email"]


class AnonymousUserBillingForm(forms.ModelForm):
    """Additional billing information form for users who are not logged in."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "billing email"}),
        label=pgettext_lazy("Address form field label", "Email"),
    )

    class Meta:
        model = Checkout
        fields = ["email"]


class AddressChoiceForm(forms.Form):
    """Choose one of user's addresses or to create new one."""

    NEW_ADDRESS = "new_address"
    CHOICES = [
        (
            NEW_ADDRESS,
            pgettext_lazy("Shipping addresses form choice", "Enter a new address"),
        )
    ]

    address = forms.ChoiceField(
        label=pgettext_lazy("Shipping addresses form field label", "Address"),
        choices=CHOICES,
        initial=NEW_ADDRESS,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        addresses = kwargs.pop("addresses")
        super().__init__(*args, **kwargs)
        address_choices = [(address.id, str(address)) for address in addresses]
        self.fields["address"].choices = self.CHOICES + address_choices


class BillingAddressChoiceForm(AddressChoiceForm):
    """Choose one of user's addresses, a shipping one or to create new."""

    NEW_ADDRESS = "new_address"
    SHIPPING_ADDRESS = "shipping_address"
    CHOICES = [
        (
            NEW_ADDRESS,
            pgettext_lazy("Billing addresses form choice", "Enter a new address"),
        ),
        (
            SHIPPING_ADDRESS,
            pgettext_lazy("Billing addresses form choice", "Same as shipping"),
        ),
    ]

    address = forms.ChoiceField(
        label=pgettext_lazy("Billing addresses form field label", "Address"),
        choices=CHOICES,
        initial=SHIPPING_ADDRESS,
        widget=forms.RadioSelect,
    )


class ShippingMethodChoiceField(forms.ModelChoiceField):
    """Shipping method choice field.

    Uses a radio group instead of a dropdown and includes estimated shipping
    prices.
    """

    shipping_address = None
    widget = forms.RadioSelect()

    def label_from_instance(self, obj):
        """Return a friendly label for the shipping method."""
        if display_gross_prices():
            price = apply_taxes_to_shipping(
                obj.price, shipping_address=self.shipping_address
            ).gross
        else:
            price = obj.price
        price_html = format_money(price)
        label = mark_safe("%s %s" % (obj.name, price_html))
        return label


class CheckoutShippingMethodForm(forms.ModelForm):
    shipping_method = ShippingMethodChoiceField(
        queryset=ShippingMethod.objects.all(),
        label=pgettext_lazy("Shipping method form field label", "Shipping method"),
        empty_label=None,
    )

    class Meta:
        model = Checkout
        fields = ["shipping_method"]

    def __init__(self, *args, **kwargs):
        discounts = kwargs.pop("discounts")
        super().__init__(*args, **kwargs)
        shipping_address = self.instance.shipping_address
        country_code = shipping_address.country.code
        qs = ShippingMethod.objects.applicable_shipping_methods(
            price=calculate_checkout_subtotal(self.instance, discounts).gross,
            weight=self.instance.get_total_weight(),
            country_code=country_code,
        )
        self.fields["shipping_method"].queryset = qs
        self.fields["shipping_method"].shipping_address = shipping_address

        if self.initial.get("shipping_method") is None:
            shipping_methods = qs.all()
            if shipping_methods:
                self.initial["shipping_method"] = shipping_methods[0]


class CheckoutNoteForm(forms.ModelForm):
    """Save note in checkout."""

    note = forms.CharField(
        max_length=250,
        required=False,
        strip=True,
        label=False,
        widget=forms.Textarea({"rows": 3}),
    )

    class Meta:
        model = Checkout
        fields = ["note"]


class VoucherField(forms.ModelChoiceField):

    default_error_messages = {
        "invalid_choice": pgettext_lazy(
            "Voucher form error", "Discount code incorrect or expired"
        )
    }


class CheckoutVoucherForm(forms.ModelForm):
    """Apply voucher to a checkout form."""

    voucher = VoucherField(
        queryset=Voucher.objects.none(),
        to_field_name="code",
        help_text=pgettext_lazy(
            "Checkout discount form label for voucher field",
            "Gift card or discount code",
        ),
        widget=forms.TextInput,
    )

    class Meta:
        model = Checkout
        fields = ["voucher"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["voucher"].queryset = Voucher.objects.active(date=timezone.now())

    def clean(self):
        from .utils import get_voucher_discount_for_checkout

        cleaned_data = super().clean()
        if "voucher" in cleaned_data:
            voucher = cleaned_data["voucher"]
            try:
                discount_amount = get_voucher_discount_for_checkout(
                    voucher, self.instance
                )
                cleaned_data["discount_amount"] = discount_amount
            except NotApplicable as e:
                self.add_error("voucher", smart_text(e))
        return cleaned_data

    def save(self, commit=True):
        voucher = self.cleaned_data["voucher"]
        self.instance.voucher_code = voucher.code
        self.instance.discount_name = voucher.name
        self.instance.translated_discount_name = (
            voucher.translated.name if voucher.translated.name != voucher.name else ""
        )
        self.instance.discount_amount = self.cleaned_data["discount_amount"]
        return super().save(commit)
