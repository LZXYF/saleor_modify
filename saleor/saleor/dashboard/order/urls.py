from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.order_list, name="orders"),
    url(r"^add/$", views.order_create, name="order-create"),
    url(
        r"^(?P<order_pk>\d+)/create/$",
        views.create_order_from_draft,
        name="create-order-from-draft",
    ),
    url(r"^(?P<order_pk>\d+)/$", views.order_details, name="order-details"),
    url(r"^(?P<order_pk>\d+)/add-note/$", views.order_add_note, name="order-add-note"),
    url(r"^(?P<order_pk>\d+)/cancel/$", views.cancel_order, name="order-cancel"),
    url(
        r"^(?P<order_pk>\d+)/address/(?P<address_type>billing|shipping)/$",
        views.order_address,
        name="address-edit",
    ),
    url(
        r"^(?P<order_pk>\d+)/edit-customer/$",
        views.order_customer_edit,
        name="order-customer-edit",
    ),
    url(
        r"^(?P<order_pk>\d+)/remove-customer/$",
        views.order_customer_remove,
        name="order-customer-remove",
    ),
    url(
        r"^(?P<order_pk>\d+)/edit-shipping/$",
        views.order_shipping_edit,
        name="order-shipping-edit",
    ),
    url(
        r"^(?P<order_pk>\d+)/remove-shipping/$",
        views.order_shipping_remove,
        name="order-shipping-remove",
    ),
    url(
        r"^(?P<order_pk>\d+)/edit-discount/$",
        views.order_discount_edit,
        name="order-discount-edit",
    ),
    url(
        r"^(?P<order_pk>\d+)/edit-voucher/$",
        views.order_voucher_edit,
        name="order-voucher-edit",
    ),
    url(
        r"^(?P<order_pk>\d+)/remove-voucher/$",
        views.order_voucher_remove,
        name="order-voucher-remove",
    ),
    url(
        r"^(?P<order_pk>\d+)/delete/$",
        views.remove_draft_order,
        name="draft-order-delete",
    ),
    url(
        r"^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/capture/$",
        views.capture_payment,
        name="capture-payment",
    ),
    url(
        r"^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/void/$",
        views.void_payment,
        name="void-payment",
    ),
    url(
        r"^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/refund/$",
        views.refund_payment,
        name="refund-payment",
    ),
    url(
        r"^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/change/$",
        views.orderline_change_quantity,
        name="orderline-change-quantity",
    ),
    url(
        r"^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/cancel/$",
        views.orderline_cancel,
        name="orderline-cancel",
    ),
    url(
        r"^(?P<order_pk>\d+)/add-variant/$",
        views.add_variant_to_order,
        name="add-variant-to-order",
    ),
    url(
        r"^(?P<order_pk>\d+)/fulfill/$",
        views.fulfill_order_lines,
        name="fulfill-order-lines",
    ),
    url(
        r"^(?P<order_pk>\d+)/fulfillment/(?P<fulfillment_pk>\d+)/cancel/$",
        views.cancel_fulfillment,
        name="fulfillment-cancel",
    ),
    url(
        r"^(?P<order_pk>\d+)/fulfillment/(?P<fulfillment_pk>\d+)/tracking/$",
        views.change_fulfillment_tracking,
        name="fulfillment-change-tracking",
    ),
    url(
        r"^(?P<order_pk>\d+)/fulfillment/(?P<fulfillment_pk>\d+)/packing-slips/$",  # noqa
        views.fulfillment_packing_slips,
        name="fulfillment-packing-slips",
    ),
    url(r"^(?P<order_pk>\d+)/invoice/$", views.order_invoice, name="order-invoice"),
    url(
        r"^(?P<order_pk>\d+)/mark-as-paid/$",
        views.mark_order_as_paid,
        name="order-mark-as-paid",
    ),
    url(
        r"^(?P<order_pk>\d+)/ajax/shipping-methods/$",
        views.ajax_order_shipping_methods_list,
        name="ajax-order-shipping-methods",
    ),
]
