import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import permission_required

from ....product import models
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import Upload
from ..types import DigitalContent, ProductVariant


class DigitalContentInput(graphene.InputObjectType):
    use_default_settings = graphene.Boolean(
        description="Use default digital content settings for this product",
        required=True,
    )
    max_downloads = graphene.Int(
        description=(
            "Determines how many times a download link can be accessed by a " "customer"
        ),
        required=False,
    )
    url_valid_days = graphene.Int(
        description=(
            "Determines for how many days a download link is active since it "
            "was generated."
        ),
        required=False,
    )
    automatic_fulfillment = graphene.Boolean(
        description=("Overwrite default automatic_fulfillment setting for variant"),
        required=False,
    )


class DigitalContentUploadInput(DigitalContentInput):
    content_file = Upload(
        required=True, description="Represents an file in a multipart request."
    )


class DigitalContentCreate(BaseMutation):
    variant = graphene.Field(ProductVariant)
    content = graphene.Field(DigitalContent)

    class Arguments:
        variant_id = graphene.ID(
            description="ID of a product variant to upload digital content.",
            required=True,
        )
        input = DigitalContentUploadInput(
            required=True, description="Fields required to create a digital content."
        )

    class Meta:
        description = """Create new digital content. This mutation must
        be sent as a `multipart` request. More detailed specs of the upload
        format can be found here:
        https://github.com/jaydenseric/graphql-multipart-request-spec"""

    @classmethod
    @permission_required("product.manage_products")
    def clean_input(cls, info, data, instance):
        if hasattr(instance, "digital_content"):
            instance.digital_content.delete()

        use_default_settings = data.get("use_default_settings")
        if use_default_settings:
            return data

        required_fields = ["max_downloads", "url_valid_days", "automatic_fulfillment"]

        if not all(field in data for field in required_fields):
            msg = (
                "Use default settings is disabled. Provide all "
                "missing configuration fields: "
            )
            missing_fields = set(required_fields).difference(set(data))
            if missing_fields:
                msg += "{}, " * len(missing_fields)
                raise ValidationError(msg.format(*missing_fields))

        return data

    @classmethod
    @permission_required("product.manage_products")
    def perform_mutation(cls, _root, info, variant_id, **data):
        variant = cls.get_node_or_error(
            info, variant_id, "id", only_type=ProductVariant
        )

        clean_input = cls.clean_input(info, data.get("input"), variant)

        content_data = info.context.FILES.get(clean_input["content_file"])
        digital_content = models.DigitalContent(content_file=content_data)
        digital_content.use_default_settings = clean_input.get(
            "use_default_settings", False
        )

        digital_content.max_downloads = clean_input.get("max_downloads")
        digital_content.url_valid_days = clean_input.get("url_valid_days")
        digital_content.automatic_fulfillment = clean_input.get(
            "automatic_fulfillment", False
        )

        variant.digital_content = digital_content
        variant.digital_content.save()
        return DigitalContentCreate(content=digital_content)


class DigitalContentDelete(BaseMutation):
    variant = graphene.Field(ProductVariant)

    class Arguments:
        variant_id = graphene.ID(
            description=("ID of a product variant with digital content to remove."),
            required=True,
        )

    class Meta:
        description = "Remove digital content assigned to given variant"

    @classmethod
    @permission_required("product.manage_products")
    def mutate(cls, _root, info, variant_id):
        variant = cls.get_node_or_error(
            info, variant_id, "id", only_type=ProductVariant
        )

        if hasattr(variant, "digital_content"):
            variant.digital_content.delete()

        return DigitalContentDelete(variant=variant)


class DigitalContentUpdate(BaseMutation):
    variant = graphene.Field(ProductVariant)
    content = graphene.Field(DigitalContent)

    class Arguments:
        variant_id = graphene.ID(
            description=("ID of a product variant with digital content to update."),
            required=True,
        )
        input = DigitalContentInput(
            required=True, description="Fields required to update a digital content."
        )

    class Meta:
        description = "Update digital content"

    @classmethod
    @permission_required("product.manage_products")
    def clean_input(cls, info, data):
        use_default_settings = data.get("use_default_settings")
        if use_default_settings:
            return {"use_default_settings": use_default_settings}

        required_fields = ["max_downloads", "url_valid_days", "automatic_fulfillment"]

        if not all(field in data for field in required_fields):
            msg = (
                "Use default settings is disabled. Provide all "
                "missing configuration fields: "
            )
            missing_fields = set(required_fields).difference(set(data))
            if missing_fields:
                msg += "{}, " * len(missing_fields)
                raise ValidationError(msg.format(*missing_fields))

        return data

    @classmethod
    @permission_required("product.manage_products")
    def perform_mutation(cls, _root, info, variant_id, **data):
        variant = cls.get_node_or_error(
            info, variant_id, "id", only_type=ProductVariant
        )

        if not hasattr(variant, "digital_content"):
            msg = "Variant %s doesn't have any digital content" % variant.id
            raise ValidationError({"variantId": msg})

        clean_input = cls.clean_input(info, data.get("input"))

        digital_content = variant.digital_content

        digital_content.use_default_settings = clean_input.get(
            "use_default_settings", False
        )

        digital_content.max_downloads = clean_input.get("max_downloads")
        digital_content.url_valid_days = clean_input.get("url_valid_days")
        digital_content.automatic_fulfillment = clean_input.get(
            "automatic_fulfillment", False
        )

        variant.digital_content = digital_content
        variant.digital_content.save()

        return DigitalContentUpdate(content=digital_content, variant=variant)


class DigitalContentUrlCreateInput(graphene.InputObjectType):
    content = graphene.ID(
        description="Digital content ID which url will belong to",
        name="content",
        required=True,
    )


class DigitalContentUrlCreate(ModelMutation):
    class Arguments:
        input = DigitalContentUrlCreateInput(
            required=True, description="Fields required to create a new url."
        )

    class Meta:
        description = "Generate new url to digital content"
        model = models.DigitalContentUrl

    @classmethod
    @permission_required("product.manage_products")
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)
