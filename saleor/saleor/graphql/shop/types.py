import graphene
from django.conf import settings
from django_countries import countries
from django_prices_vatlayer.models import VAT
from graphql_jwt.decorators import permission_required
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ...core.permissions import get_permissions
from ...core.utils import get_client_ip, get_country_by_ip
from ...menu import models as menu_models
from ...product import models as product_models
from ...site import models as site_models
from ..account.types import Address
from ..core.enums import WeightUnitsEnum
from ..core.types.common import CountryDisplay, LanguageDisplay, PermissionDisplay
from ..core.utils import get_node_optimized, str_to_enum
from ..menu.types import Menu
from ..product.types import Collection
from ..translations.enums import LanguageCodeEnum
from ..translations.resolvers import resolve_translation
from ..translations.types import ShopTranslation
from ..utils import format_permissions_for_display
from .enums import AuthorizationKeyType


class Navigation(graphene.ObjectType):
    main = graphene.Field(Menu, description="Main navigation bar.")
    secondary = graphene.Field(Menu, description="Secondary navigation bar.")

    class Meta:
        description = "Represents shop's navigation menus."


class AuthorizationKey(graphene.ObjectType):
    name = AuthorizationKeyType(
        description="Name of the authorization backend.", required=True
    )
    key = graphene.String(description="Authorization key (client ID).", required=True)


class Domain(graphene.ObjectType):
    host = graphene.String(description="The host name of the domain.", required=True)
    ssl_enabled = graphene.Boolean(
        description="Inform if SSL is enabled.", required=True
    )
    url = graphene.String(description="Shop's absolute URL.", required=True)

    class Meta:
        description = "Represents shop's domain."


class Geolocalization(graphene.ObjectType):
    country = graphene.Field(
        CountryDisplay, description="Country of the user acquired by his IP address."
    )

    class Meta:
        description = "Represents customers's geolocalization data."


class Shop(graphene.ObjectType):
    geolocalization = graphene.Field(
        Geolocalization, description="Customer's geolocalization data."
    )
    authorization_keys = graphene.List(
        AuthorizationKey,
        description="""List of configured authorization keys. Authorization
               keys are used to enable third party OAuth authorization
               (currently Facebook or Google).""",
        required=True,
    )
    countries = graphene.List(
        CountryDisplay,
        description="List of countries available in the shop.",
        required=True,
    )
    currencies = graphene.List(
        graphene.String, description="List of available currencies.", required=True
    )
    default_currency = graphene.String(
        description="Default shop's currency.", required=True
    )
    default_country = graphene.Field(
        CountryDisplay, description="Default shop's country"
    )
    description = graphene.String(description="Shop's description.")
    domain = graphene.Field(Domain, required=True, description="Shop's domain data.")
    homepage_collection = graphene.Field(
        Collection, description="Collection displayed on homepage"
    )
    languages = graphene.List(
        LanguageDisplay,
        description="List of the shops's supported languages.",
        required=True,
    )
    name = graphene.String(description="Shop's name.", required=True)
    navigation = graphene.Field(Navigation, description="Shop's navigation.")
    permissions = graphene.List(
        PermissionDisplay, description="List of available permissions.", required=True
    )
    phone_prefixes = graphene.List(
        graphene.String, description="List of possible phone prefixes.", required=True
    )
    header_text = graphene.String(description="Header text")
    include_taxes_in_prices = graphene.Boolean(
        description="Include taxes in prices", required=True
    )
    display_gross_prices = graphene.Boolean(
        description="Display prices with tax in store", required=True
    )
    charge_taxes_on_shipping = graphene.Boolean(
        description="Charge taxes on shipping", required=True
    )
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking"
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit")
    translation = graphene.Field(
        ShopTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=("Returns translated Shop fields for the given language code."),
    )
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products"
    )

    default_digital_max_downloads = graphene.Int(
        description="Default number of max downloads per digital content url"
    )
    default_digital_url_valid_days = graphene.Int(
        description=("Default number of days which digital content url will be valid")
    )
    company_address = graphene.Field(
        Address, description="Company address", required=False
    )

    class Meta:
        description = """
        Represents a shop resource containing general shop\'s data
        and configuration."""

    @staticmethod
    @permission_required("site.manage_settings")
    def resolve_authorization_keys(_, _info):
        return site_models.AuthorizationKey.objects.all()

    @staticmethod
    def resolve_countries(_, _info):
        taxes = {vat.country_code: vat for vat in VAT.objects.all()}
        return [
            CountryDisplay(
                code=country[0], country=country[1], vat=taxes.get(country[0])
            )
            for country in countries
        ]

    @staticmethod
    def resolve_currencies(_, _info):
        return settings.AVAILABLE_CURRENCIES

    @staticmethod
    def resolve_domain(_, info):
        site = info.context.site
        return Domain(
            host=site.domain,
            ssl_enabled=settings.ENABLE_SSL,
            url=info.context.build_absolute_uri("/"),
        )

    @staticmethod
    def resolve_geolocalization(_, info):
        client_ip = get_client_ip(info.context)
        country = get_country_by_ip(client_ip)
        if country:
            return Geolocalization(
                country=CountryDisplay(code=country.code, country=country.name)
            )
        return Geolocalization(country=None)

    @staticmethod
    def resolve_default_currency(_, _info):
        return settings.DEFAULT_CURRENCY

    @staticmethod
    def resolve_description(_, info):
        return info.context.site.settings.description

    @staticmethod
    def resolve_homepage_collection(_, info):
        collection_pk = info.context.site.settings.homepage_collection_id
        qs = product_models.Collection.objects.all()
        return get_node_optimized(qs, {"pk": collection_pk}, info)

    @staticmethod
    def resolve_languages(_, _info):
        return [
            LanguageDisplay(
                code=LanguageCodeEnum[str_to_enum(language[0])], language=language[1]
            )
            for language in settings.LANGUAGES
        ]

    @staticmethod
    def resolve_name(_, info):
        return info.context.site.name

    @staticmethod
    def resolve_navigation(_, info):
        site_settings = info.context.site.settings
        qs = menu_models.Menu.objects.all()
        top_menu = get_node_optimized(qs, {"pk": site_settings.top_menu_id}, info)
        bottom_menu = get_node_optimized(qs, {"pk": site_settings.bottom_menu_id}, info)
        return Navigation(main=top_menu, secondary=bottom_menu)

    @staticmethod
    @permission_required("account.manage_users")
    def resolve_permissions(_, _info):
        permissions = get_permissions()
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_phone_prefixes(_, _info):
        return list(COUNTRY_CODE_TO_REGION_CODE.keys())

    @staticmethod
    def resolve_header_text(_, info):
        return info.context.site.settings.header_text

    @staticmethod
    def resolve_include_taxes_in_prices(_, info):
        return info.context.site.settings.include_taxes_in_prices

    @staticmethod
    def resolve_display_gross_prices(_, info):
        return info.context.site.settings.display_gross_prices

    @staticmethod
    def resolve_charge_taxes_on_shipping(_, info):
        return info.context.site.settings.charge_taxes_on_shipping

    @staticmethod
    def resolve_track_inventory_by_default(_, info):
        return info.context.site.settings.track_inventory_by_default

    @staticmethod
    def resolve_default_weight_unit(_, info):
        return info.context.site.settings.default_weight_unit

    @staticmethod
    def resolve_default_country(_, _info):
        default_country_code = settings.DEFAULT_COUNTRY
        default_country_name = countries.countries.get(default_country_code)
        if default_country_name:
            vat = VAT.objects.filter(country_code=default_country_code).first()
            default_country = CountryDisplay(
                code=default_country_code, country=default_country_name, vat=vat
            )
        else:
            default_country = None
        return default_country

    @staticmethod
    def resolve_company_address(_, info):
        return info.context.site.settings.company_address

    @staticmethod
    def resolve_translation(_, info, language_code):
        return resolve_translation(info.context.site.settings, info, language_code)

    @staticmethod
    @permission_required("site.manage_settings")
    def resolve_automatic_fulfillment_digital_products(_, info):
        site_settings = info.context.site.settings
        return site_settings.automatic_fulfillment_digital_products

    @staticmethod
    @permission_required("site.manage_settings")
    def resolve_default_digital_max_downloads(_, info):
        return info.context.site.settings.default_digital_max_downloads

    @staticmethod
    @permission_required("site.manage_settings")
    def resolve_default_digital_url_valid_days(_, info):
        return info.context.site.settings.default_digital_url_valid_days
