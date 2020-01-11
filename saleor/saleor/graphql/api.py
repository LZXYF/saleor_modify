import graphene

from .account.schema import AccountMutations, AccountQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreMutations, CoreQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .giftcard.schema import GiftCardMutations, GiftCardQueries
from .menu.schema import MenuMutations, MenuQueries
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .translations.schema import TranslationQueries


class Query(
    AccountQueries,
    CheckoutQueries,
    CoreQueries,
    DiscountQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    TranslationQueries,
):
    node = graphene.Node.Field()


class Mutations(
    AccountMutations,
    CheckoutMutations,
    CoreMutations,
    DiscountMutations,
    GiftCardMutations,
    MenuMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
):
    pass


schema = graphene.Schema(Query, Mutations)
