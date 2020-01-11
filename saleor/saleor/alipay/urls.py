
from django.conf.urls import url
from . import views

urlpatterns=[
    url(r'^alipay_result', views.alipay_result),
    url(r'^payOrder/$', views.payOrder),
    url(r'^wxpay_result', views.wxpay_result),
]
