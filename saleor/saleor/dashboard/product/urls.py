from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.product_list, name="product-list"),
    url(r"^(?P<pk>[0-9]+)/$", views.product_details, name="product-details"),
    url(
        r"^(?P<pk>[0-9]+)/publish/$",
        views.product_toggle_is_published,
        name="product-publish",
    ),
    url(
        r"^add/select-type/$", views.product_select_type, name="product-add-select-type"
    ),
    url(r"^add/(?P<type_pk>[0-9]+)/$", views.product_create, name="product-add"),
    url(r"^(?P<pk>[0-9]+)/update/$", views.product_edit, name="product-update"),
    url(r"^(?P<pk>[0-9]+)/delete/$", views.product_delete, name="product-delete"),
    url(r"^bulk-update/$", views.product_bulk_update, name="product-bulk-update"),
    url(r"^ajax/products/$", views.ajax_products_list, name="ajax-products"),
    url(r"^types/$", views.product_type_list, name="product-type-list"),
    url(r"^types/add/$", views.product_type_create, name="product-type-add"),
    url(
        r"^types/(?P<pk>[0-9]+)/update/$",
        views.product_type_edit,
        name="product-type-update",
    ),
    url(
        r"^types/(?P<pk>[0-9]+)/delete/$",
        views.product_type_delete,
        name="product-type-delete",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/$",
        views.variant_details,
        name="variant-details",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/variants/add/$",
        views.variant_create,
        name="variant-add",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/update/$",
        views.variant_edit,
        name="variant-update",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/delete/$",
        views.variant_delete,
        name="variant-delete",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/images/$",
        views.variant_images,
        name="variant-images",
    ),
    url(
        r"^ajax/variants/$",
        views.ajax_available_variants_list,
        name="ajax-available-variants",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/$",
        views.product_images,
        name="product-image-list",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/add/$",
        views.product_image_create,
        name="product-image-add",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/$",
        views.product_image_edit,
        name="product-image-update",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/delete/$",
        views.product_image_delete,
        name="product-image-delete",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/reorder/$",
        views.ajax_reorder_product_images,
        name="product-images-reorder",
    ),
    url(
        r"^(?P<product_pk>[0-9]+)/images/upload/$",
        views.ajax_upload_image,
        name="product-images-upload",
    ),
    url(r"attributes/$", views.attribute_list, name="attributes"),
    url(
        r"attributes/(?P<pk>[0-9]+)/$",
        views.attribute_details,
        name="attribute-details",
    ),
    url(r"attributes/add/$", views.attribute_create, name="attribute-add"),
    url(
        r"attributes/(?P<pk>[0-9]+)/update/$",
        views.attribute_edit,
        name="attribute-update",
    ),
    url(
        r"attributes/(?P<pk>[0-9]+)/delete/$",
        views.attribute_delete,
        name="attribute-delete",
    ),
    url(
        r"attributes/(?P<attribute_pk>[0-9]+)/value/add/$",
        views.attribute_value_create,
        name="attribute-value-add",
    ),
    url(
        r"attributes/(?P<attribute_pk>[0-9]+)/value/(?P<value_pk>[0-9]+)/update/$",  # noqa
        views.attribute_value_edit,
        name="attribute-value-update",
    ),
    url(
        r"attributes/(?P<attribute_pk>[0-9]+)/value/(?P<value_pk>[0-9]+)/delete/$",  # noqa
        views.attribute_value_delete,
        name="attribute-value-delete",
    ),
    url(
        r"attributes/(?P<attribute_pk>[0-9]+)/values/reorder/$",
        views.ajax_reorder_attribute_values,
        name="attribute-values-reorder",
    ),
]
