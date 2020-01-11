import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ....product import models
from ...core.connection import CountableDjangoObjectType


class DigitalContentUrl(CountableDjangoObjectType):
    url = graphene.String(description="Url for digital content")

    class Meta:
        model = models.DigitalContentUrl
        only_fields = ["content", "created", "download_num", "token", "url"]
        interfaces = (relay.Node,)

    @staticmethod
    def resolve_url(root: models.DigitalContentUrl, *_args):
        return root.get_absolute_url()


class DigitalContent(CountableDjangoObjectType):
    urls = gql_optimizer.field(
        graphene.List(
            lambda: DigitalContentUrl,
            description="List of urls for the digital variant",
        ),
        model_field="urls",
    )

    class Meta:
        model = models.DigitalContent
        only_fields = [
            "automatic_fulfillment",
            "content_file",
            "max_downloads",
            "product_variant",
            "url_valid_days",
            "urls",
            "use_default_settings",
        ]
        interfaces = (relay.Node,)

    @staticmethod
    def resolve_urls(root: models.DigitalContent, info, **_kwargs):
        qs = root.urls.all()
        return gql_optimizer.query(qs, info)
