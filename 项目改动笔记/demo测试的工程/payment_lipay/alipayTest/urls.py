from . import views
from django.conf.urls import url

urlpatterns=[
    url(r"^$", views.index),
    # url(r"^/orders/(?P<order_id>\d+)/payment/$", views.pay),
    url(r'^alipay2/$', views.alipay2),
    url(r'^alipay/$', views.alipay),
    url(r'^alipay_result/', views.alipay_result),
    url(r'^alipay_result2/', views.alipay_result2),
    # url('pay_page/', views.pay_page, name='pay_page'),
]