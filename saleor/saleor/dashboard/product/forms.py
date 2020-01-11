import bleach
from django import forms
from django.conf import settings
from django.db.models import Count, Q
from django.forms.models import ModelChoiceIterator
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from mptt.forms import TreeNodeChoiceField

from ...core.taxes import include_taxes_in_prices
from ...core.taxes.interface import get_tax_from_object_meta, get_tax_rate_type_choices
from ...core.weight import WeightField
from ...product.models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
    VariantImage,
)
from ...product.tasks import update_variants_names
from ...product.thumbnails import create_product_thumbnails
from ...product.utils.attributes import get_name_from_attributes
from ..forms import ModelChoiceOrCreationField, OrderedModelMultipleChoiceField
from ..seo.fields import SeoDescriptionField, SeoTitleField
from ..seo.utils import prepare_seo_description
from ..widgets import RichTextEditorWidget
from . import ProductBulkAction
from .widgets import ImagePreviewWidget


class RichTextField(forms.CharField):
    """A field for rich text editor, providing backend sanitization."""

    widget = RichTextEditorWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_text = pgettext_lazy(
            "Help text in rich-text editor field",
            "Select text to enable text-formatting tools.",
        )

    def to_python(self, value):
        tags = settings.ALLOWED_TAGS or bleach.ALLOWED_TAGS
        attributes = settings.ALLOWED_ATTRIBUTES or bleach.ALLOWED_ATTRIBUTES
        styles = settings.ALLOWED_STYLES or bleach.ALLOWED_STYLES
        value = super().to_python(value)
        value = bleach.clean(value, tags=tags, attributes=attributes, styles=styles)
        return value


class ProductTypeSelectorForm(forms.Form):
    """Form that allows selecting product type."""

    product_type = forms.ModelChoiceField(
        queryset=ProductType.objects.all(),
        label=pgettext_lazy("Product type form label", "Product type"),
        widget=forms.RadioSelect,
        empty_label=None,
    )


class ProductTypeForm(forms.ModelForm):
    tax_rate = forms.ChoiceField(
        required=False, label=pgettext_lazy("Product type tax rate type", "Tax rate")
    )
    weight = WeightField(
        label=pgettext_lazy("ProductType weight", "Weight"),
        help_text=pgettext_lazy(
            "ProductVariant weight help text",
            "Default weight that will be used for calculating shipping"
            " price for products of that type.",
        ),
    )
    product_attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.none(),
        required=False,
        label=pgettext_lazy(
            "Product type attributes", "Attributes common to all variants."
        ),
    )
    variant_attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.none(),
        required=False,
        label=pgettext_lazy(
            "Product type attributes", "Attributes specific to each variant."
        ),
    )

    class Meta:
        model = ProductType
        exclude = []
        labels = {
            "name": pgettext_lazy("Item name", "Name"),
            "has_variants": pgettext_lazy("Enable variants", "Enable variants"),
            "is_shipping_required": pgettext_lazy(
                "Shipping toggle", "Require shipping"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tax_rate"].choices = [
            (tax.code, tax.description) for tax in get_tax_rate_type_choices()
        ]
        unassigned_attrs_q = Q(
            product_type__isnull=True, product_variant_type__isnull=True
        )

        if self.instance.pk:
            product_attrs_qs = Attribute.objects.filter(
                Q(product_type=self.instance) | unassigned_attrs_q
            )
            variant_attrs_qs = Attribute.objects.filter(
                Q(product_variant_type=self.instance) | unassigned_attrs_q
            )
            product_attrs_initial = self.instance.product_attributes.all()
            variant_attrs_initial = self.instance.variant_attributes.all()
        else:
            unassigned_attrs = Attribute.objects.filter(unassigned_attrs_q)
            product_attrs_qs = unassigned_attrs
            variant_attrs_qs = unassigned_attrs
            product_attrs_initial = []
            variant_attrs_initial = []

        self.fields["product_attributes"].queryset = product_attrs_qs
        self.fields["variant_attributes"].queryset = variant_attrs_qs
        self.fields["product_attributes"].initial = product_attrs_initial
        self.fields["variant_attributes"].initial = variant_attrs_initial

    def clean(self):
        data = super().clean()
        has_variants = self.cleaned_data["has_variants"]
        product_attr = set(self.cleaned_data.get("product_attributes", []))
        variant_attr = set(self.cleaned_data.get("variant_attributes", []))
        if not has_variants and variant_attr:
            msg = pgettext_lazy(
                "Product type form error", "Product variants are disabled."
            )
            self.add_error("variant_attributes", msg)
        if product_attr & variant_attr:
            msg = pgettext_lazy(
                "Product type form error",
                "A single attribute can't belong to both a product " "and its variant.",
            )
            self.add_error("variant_attributes", msg)

        if not self.instance.pk:
            return data

        self.check_if_variants_changed(has_variants)
        variant_attr_ids = [attr.pk for attr in variant_attr]
        update_variants_names.delay(self.instance.pk, variant_attr_ids)
        return data

    def check_if_variants_changed(self, has_variants):
        variants_changed = self.fields["has_variants"].initial != has_variants
        if variants_changed:
            query = self.instance.products.all()
            query = query.annotate(variants_counter=Count("variants"))
            query = query.filter(variants_counter__gt=1)
            if query.exists():
                msg = pgettext_lazy(
                    "Product type form error",
                    "Some products of this type have more than " "one variant.",
                )
                self.add_error("has_variants", msg)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        new_product_attrs = self.cleaned_data.get("product_attributes", [])
        new_variant_attrs = self.cleaned_data.get("variant_attributes", [])
        instance.product_attributes.set(new_product_attrs)
        instance.variant_attributes.set(new_variant_attrs)
        return instance


class AttributesMixin:
    """Form mixin that dynamically adds attribute fields."""

    available_attributes = Attribute.objects.none()

    # Name of a field in self.instance that hold attributes HStore
    model_attributes_field = None

    def __init__(self, *args, **kwargs):
        if not self.model_attributes_field:
            raise Exception(
                "model_attributes_field must be set in subclasses of "
                "AttributesMixin."
            )

    def prepare_fields_for_attributes(self):
        initial_attrs = getattr(self.instance, self.model_attributes_field)
        for attribute in self.available_attributes:
            field_defaults = {
                "label": attribute.name,
                "required": False,
                "initial": initial_attrs.get(str(attribute.pk)),
            }
            if attribute.has_values():
                field = ModelChoiceOrCreationField(
                    queryset=attribute.values.all(), **field_defaults
                )
            else:
                field = forms.CharField(**field_defaults)
            self.fields[attribute.get_formfield_name()] = field

    def iter_attribute_fields(self):
        for attr in self.available_attributes:
            yield self[attr.get_formfield_name()]

    def get_saved_attributes(self):
        attributes = {}
        for attr in self.available_attributes:
            value = self.cleaned_data.pop(attr.get_formfield_name())
            if value:
                # if the passed attribute value is a string,
                # create the attribute value.
                if not isinstance(value, AttributeValue):
                    value = AttributeValue(
                        attribute_id=attr.pk, name=value, slug=slugify(value)
                    )
                    value.save()
                attributes[smart_text(attr.pk)] = smart_text(value.pk)
        return attributes


class ProductForm(forms.ModelForm, AttributesMixin):
    tax_rate = forms.ChoiceField(
        required=False, label=pgettext_lazy("Product tax rate type", "Tax rate")
    )

    category = TreeNodeChoiceField(
        queryset=Category.objects.all(), label=pgettext_lazy("Category", "Category")
    )
    collections = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Collection.objects.all(),
        label=pgettext_lazy("Add to collection select", "Collections"),
    )
    description = RichTextField(
        label=pgettext_lazy("Description", "Description"), required=True
    )
    weight = WeightField(
        required=False,
        label=pgettext_lazy("ProductType weight", "Weight"),
        help_text=pgettext_lazy(
            "Product weight field help text",
            "Weight will be used to calculate shipping price, "
            "if empty, equal to default value used on the ProductType.",
        ),
    )

    model_attributes_field = "attributes"

    class Meta:
        model = Product
        exclude = ["attributes", "product_type", "updated_at", "description_json"]
        labels = {
            "name": pgettext_lazy("Item name", "Name"),
            "price": pgettext_lazy("Currency amount", "Price"),
            "publication_date": pgettext_lazy(
                "Availability date", "Publish product on"
            ),
            "is_published": pgettext_lazy("Product published toggle", "Published"),
            "charge_taxes": pgettext_lazy(
                "Charge taxes on product", "Charge taxes on this product"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_type = self.instance.product_type
        product_tax_rate = get_tax_from_object_meta(self.instance).code
        self.initial["tax_rate"] = (
            product_tax_rate or get_tax_from_object_meta(product_type).code
        )
        self.available_attributes = product_type.product_attributes.prefetch_related(
            "values"
        ).all()
        self.prepare_fields_for_attributes()
        self.fields["collections"].initial = Collection.objects.filter(
            products__name=self.instance
        )
        self.fields["seo_description"] = SeoDescriptionField(
            extra_attrs={
                "data-bind": self["description"].auto_id,
                "data-materialize": self["description"].html_name,
            }
        )
        self.fields["seo_title"] = SeoTitleField(
            extra_attrs={"data-bind": self["name"].auto_id}
        )
        self.fields["tax_rate"].choices = [
            (tax.code, tax.description) for tax in get_tax_rate_type_choices()
        ]
        if include_taxes_in_prices():
            self.fields["price"].label = pgettext_lazy(
                "Currency gross amount", "Gross price"
            )
        else:
            self.fields["price"].label = pgettext_lazy(
                "Currency net amount", "Net price"
            )

        if not product_type.is_shipping_required:
            del self.fields["weight"]
        else:
            self.fields["weight"].widget.attrs[
                "placeholder"
            ] = product_type.weight.value

    def clean_seo_description(self):
        seo_description = prepare_seo_description(
            seo_description=self.cleaned_data["seo_description"],
            html_description=self.data["description"],
            max_length=self.fields["seo_description"].max_length,
        )
        return seo_description

    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        instance = super().save()
        instance.collections.clear()
        for collection in self.cleaned_data["collections"]:
            instance.collections.add(collection)
        return instance


class ProductVariantForm(forms.ModelForm, AttributesMixin):
    model_attributes_field = "attributes"
    weight = WeightField(
        required=False,
        label=pgettext_lazy("ProductVariant weight", "Weight"),
        help_text=pgettext_lazy(
            "ProductVariant weight help text",
            "Weight will be used to calculate shipping price. "
            "If empty, weight from Product or ProductType will be used.",
        ),
    )

    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "price_override",
            "weight",
            "quantity",
            "cost_price",
            "track_inventory",
        ]
        labels = {
            "sku": pgettext_lazy("SKU", "SKU"),
            "price_override": pgettext_lazy("Override price", "Selling price override"),
            "quantity": pgettext_lazy("Integer number", "Number in stock"),
            "cost_price": pgettext_lazy("Currency amount", "Cost price"),
            "track_inventory": pgettext_lazy(
                "Track inventory field", "Track inventory"
            ),
        }
        help_texts = {
            "track_inventory": pgettext_lazy(
                "product variant handle stock field help text",
                "Automatically track this product's inventory",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.product.pk:
            self.fields["price_override"].widget.attrs[
                "placeholder"
            ] = self.instance.product.price.amount
            qs = self.instance.product.product_type.variant_attributes.all()
            self.available_attributes = qs.prefetch_related("values")
            self.prepare_fields_for_attributes()

        if include_taxes_in_prices():
            self.fields["price_override"].label = pgettext_lazy(
                "Override price", "Selling gross price override"
            )
            self.fields["cost_price"].label = pgettext_lazy(
                "Currency amount", "Cost gross price"
            )
        else:
            self.fields["price_override"].label = pgettext_lazy(
                "Override price", "Selling net price override"
            )
            self.fields["cost_price"].label = pgettext_lazy(
                "Currency amount", "Cost net price"
            )

        if not self.instance.product.product_type.is_shipping_required:
            del self.fields["weight"]
        else:
            self.fields["weight"].widget.attrs["placeholder"] = (
                getattr(self.instance.product.weight, "value", None)
                or self.instance.product.product_type.weight.value
            )

    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        attrs = self.instance.product.product_type.variant_attributes.prefetch_related(
            "values__translations"
        )
        self.instance.name = get_name_from_attributes(self.instance, attrs)
        return super().save(commit=commit)


class CachingModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        for obj in self.queryset:
            yield self.choice(obj)


class CachingModelChoiceField(forms.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, "_choices"):
            return self._choices
        return CachingModelChoiceIterator(self)

    choices = property(_get_choices, forms.ChoiceField._set_choices)


class VariantBulkDeleteForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=ProductVariant.objects)

    def delete(self):
        items = ProductVariant.objects.filter(pk__in=self.cleaned_data["items"])
        items.delete()


class ProductImageForm(forms.ModelForm):
    use_required_attribute = False
    variants = forms.ModelMultipleChoiceField(
        queryset=ProductVariant.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = ProductImage
        exclude = ("product", "sort_order")
        labels = {
            "image": pgettext_lazy("Product image", "Image"),
            "alt": pgettext_lazy("Description", "Description"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            self.fields["image"].widget = ImagePreviewWidget()

    def save(self, commit=True):
        image = super().save(commit=commit)
        create_product_thumbnails.delay(image.pk)
        return image


class VariantImagesSelectForm(forms.Form):
    images = forms.ModelMultipleChoiceField(
        queryset=VariantImage.objects.none(),
        widget=CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop("variant")
        super().__init__(*args, **kwargs)
        self.fields["images"].queryset = self.variant.product.images.all()
        self.fields["images"].initial = self.variant.images.all()

    def save(self):
        images = []
        self.variant.images.clear()
        for image in self.cleaned_data["images"]:
            images.append(VariantImage(variant=self.variant, image=image))
        VariantImage.objects.bulk_create(images)


class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        exclude = []
        labels = {
            "name": pgettext_lazy("Product display name", "Display name"),
            "slug": pgettext_lazy("Product internal name", "Internal name"),
        }


class AttributeValueForm(forms.ModelForm):
    class Meta:
        model = AttributeValue
        fields = ["attribute", "name", "type_ini"]
        widgets = {"attribute": forms.widgets.HiddenInput(),
                "type_ini": forms.Select(choices =[
                    (1,'char'),
                    (2,'upload'),
                    (3,"molecule")
                    ])
                }
        labels = {"name": pgettext_lazy("Item name", "Name"),
                "type_ini": "custom_type"
                }

    def save(self, commit=True):
        self.instance.slug = slugify(self.instance.name)
        return super().save(commit=commit)


class ReorderAttributeValuesForm(forms.ModelForm):
    ordered_values = OrderedModelMultipleChoiceField(
        queryset=AttributeValue.objects.none()
    )

    class Meta:
        model = Attribute
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["ordered_values"].queryset = self.instance.values.all()

    def save(self):
        for order, value in enumerate(self.cleaned_data["ordered_values"]):
            value.sort_order = order
            value.save()
        return self.instance


class ReorderProductImagesForm(forms.ModelForm):
    ordered_images = OrderedModelMultipleChoiceField(
        queryset=ProductImage.objects.none()
    )

    class Meta:
        model = Product
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["ordered_images"].queryset = self.instance.images.all()

    def save(self):
        for order, image in enumerate(self.cleaned_data["ordered_images"]):
            image.sort_order = order
            image.save()
        return self.instance


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ("image",)
        labels = {"image": pgettext_lazy("Product image", "Image")}

    def __init__(self, *args, **kwargs):
        product = kwargs.pop("product")
        super().__init__(*args, **kwargs)
        self.instance.product = product

    def save(self, commit=True):
        image = super().save(commit=commit)
        create_product_thumbnails.delay(image.pk)
        return image


class ProductBulkUpdate(forms.Form):
    """Perform one selected bulk action on all selected products."""

    action = forms.ChoiceField(choices=ProductBulkAction.CHOICES)
    products = forms.ModelMultipleChoiceField(queryset=Product.objects.all())

    def save(self):
        action = self.cleaned_data["action"]
        if action == ProductBulkAction.PUBLISH:
            self._publish_products()
        elif action == ProductBulkAction.UNPUBLISH:
            self._unpublish_products()

    def _publish_products(self):
        self.cleaned_data["products"].update(is_published=True)

    def _unpublish_products(self):
        self.cleaned_data["products"].update(is_published=False)
