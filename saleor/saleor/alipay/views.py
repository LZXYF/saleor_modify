import random
import time
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import redirect, render
from all_pay import PayOrder
from all_pay import Pay
from all_pay.wx import WxPay
from ..settings import AliPayConfig
from ..settings import WxPayConfig
# 注意：uid参数可不要，此处因生成订单号要使用，所以添加，测试证明沙箱环境下添加自定义参数回调函数也可正常访问，正式环境下还没有测试，待测试后再做说明

# 充值页面
# def pay_page(request):
#     return render(request, 'user_center/pay_page.html')

# def index(request):
#    return render(request,'index.html',None)


# 生成订单号(自定义)
def order_num(package_num,uid):
#    '''
#    商品代码后两位+下单时间后十二位+用户id后四位+随机数四位
#    :param package_num: 商品代码
#    :return: 唯一的订单号
#    '''
    local_time = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))[2:]
    result = str(package_num)[-2:] + local_time +uid[-4:]+str(random.randint(1000,9999))
    return result


# 获取一个用于支付的对象
def get_pay_object(way):
    # 沙箱环境地址：https://openhome.alipay.com/platform/appDaily.htm?tab=info
    # 正式启用时需要重新配置app_id ，merchant_private_key_path ，alipay_public_key_path
    app_id = AliPayConfig.app_id  # APPID  沙箱应用

    # 支付完成后支付宝向这里发送一个post请求，如果识别为局域网ip，支付宝找不到，alipay_result（）接受不到这个请求
    notify_url = AliPayConfig.notify_url

    # 支付完成后跳转的地址
    return_url = AliPayConfig.return_url

    # 应用私钥
    merchant_private_key_path = AliPayConfig.merchant_private_key_path
    # 支付宝公钥
    alipay_public_key_path = AliPayConfig.alipay_public_key_path # 验证支付宝回传消息使用
    if way == "ali":
        alipay = {
            'pay_type': 'ali_pay',
            'app_id': app_id,  # 必填 应用id
            'private_key_path': merchant_private_key_path,  # 必填 应用私钥
            'public_key_path': alipay_public_key_path,  # 必填 支付宝公钥
            'notify_url': notify_url,  # 异步回调地址
            'sign_type': 'RSA2',  # 签名算法 RSA 或者 RSA2
            'debug': True  # 是否是沙箱模式
            }
        return alipay
    else:
        wxpay = {
            'pay_type': 'wx_pay',  # 必填 区分支付类型
            'app_id': WxPayConfig.wx_app_id,  # 必填,应用id
            'mch_key': WxPayConfig.wx_mch_key,  # 必填,商户平台密钥
            'mch_id': WxPayConfig.wx_mch_id,  # 必填,微信支付分配的商户号
            'app_secret': WxPayConfig.wx_mch_key,  # 应用密钥
            'notify_url': WxPayConfig.wx_notify_url,  # 异步回调地址
            'api_cert_path': WxPayConfig.wx_apiclient_cert_path,  # API证书
            'api_key_path': WxPayConfig.wx_apiclient_key_path,  # API证书 key
            'trade_type':  'NATIVE'
        }
        return wxpay


# 支付视图函数,way是支付方式
def payOrder(request):
    token = request.session['token']
    del request.session['token']
    order_id = str(request.session['order_id'])
    del request.session['order_id']
    total = round(float(request.session['total']),2)
    del request.session['total']
    way = request.GET.get('way')
  #  '''根据当前用户的配置生成url，并跳转''，这是支付宝支付方式'
    if way == "ali":
        alipay = get_pay_object("ali")
        # 额外参数
        order = PayOrder.Builder().subject('支付宝测试订单').total_fee(total).out_trade_no(order_id+"-"+token).return_url(AliPayConfig.return_url).build()
        pay = Pay(alipay)  # 传入对应支付方式配置
        pay_url = pay.trade_page_pay(order)
        return redirect(pay_url)
    else:
        print("微信支付")
        wxpay = get_pay_object("wx")
        # 微信支付金额是以分为单位
        total = total*100
        order = PayOrder.Builder().subject('微信测试订单').product_id(order_id).total_fee(1).build()
        pay=Pay(wxpay)
        order_res=pay.trade_page_pay(order)
        # 支付url
	# print("order_res",order_res)
	# pay_url = "https://openapi.alipaydev.com/gateway.do?{0}".format(order_res)  # 支付宝网关地址（沙箱应用）
        print(order_res)
        # 生成微信支付二维码
        import qrcode
        
        qr=qrcode.QRCode(
                version=7,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
        qr.add_data(order_res)
        qr.make(fit=True)
        img = qr.make_image()
        img.save("saleor/static/imgs/"+ token +".png")
        return TemplateResponse(request, "order/wxpay.html", {'img': token+'.png'})


from ..payment.utils import (gateway_process_payment)

from ..payment.models import Payment
from ..order.models import Order

# 微信支付异步通知
def wxpay_result(request):
    params = trans_xml_to_dict(request.body)

    # 验证签名
    flag = verify(data)
    if flag and data['return_code'] == 'success':
    	# 修改后台数据库
        passback_params = params["out_trade_no"]
        token = passback_params[passback_params.index("-")+1:]
        order_id = passback_params[:passback_params.index("-")]
        payment = Payment.objects.get(order_id=order_id)
        order = Order.objects.get(pk=order_id)
        try:
            gateway_process_payment(
                payment=payment, payment_token=token
            )
        except Exception as exc:
            print(exc)
        else:
            if order.is_fully_paid():
            	return HttpResponse(trans_dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))
            return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
        return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))


# 微信异步通知验证工具函数
def trans_dict_to_xml(data_dict):
    """
    定义字典转XML的函数
    :param data_dict: 
    :return: 
    """
    data_xml = []
    for k in sorted(data_dict.keys()):  # 遍历字典排序后的key
        v = data_dict.get(k)  # 取出字典中key对应的value
        if k == 'detail' and not v.startswith('<![CDATA['):  # 添加XML标记
            v = '<![CDATA[{}]]>'.format(v)
        data_xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(data_xml))


def verify(data):
    sign = data.pop('sign', None)
    print("data: ", data)
    back_sign = getsign(data, "alphamalizhaojunalphamalizhaojun")
    if sign == back_sign:
        return True
    return False

import hashlib
def getsign(raw,mch_key):
    # """
    #         生成签名
    #         参考微信签名生成算法
    #         https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=4_3
    #         """
    raw = [(k, str(raw[k]) if isinstance(raw[k], (int, float)) else raw[k]) for k in sorted(raw.keys())]
    s = '&'.join('='.join(kv) for kv in raw if kv[1])
    s += '&key={0}'.format(mch_key)
    return hashlib.md5(s.encode("utf-8")).hexdigest().upper()


from bs4 import BeautifulSoup

def trans_xml_to_dict(data_xml):
    """
    定义XML转字典的函数
    :param data_xml:
    :return:
    """
    soup = BeautifulSoup(data_xml, features='xml')
    xml = soup.find('xml')  # 解析XML
    if not xml:
        return {}
    data_dict = dict([(item.name, item.text) for item in xml.find_all()])
    return data_dict




# 支付成功后回调函数（支付宝）
def alipay_result(request):
    alipay = get_pay_object("ali")
    pay = Pay(alipay)
    if request.method == "POST":  # POST方法后台回调，只能在外网服务器测试
        # 检测是否支付成功
        # 去请求体中获取所有返回的参数：状态/订单号
        post_dict = request.POST.dict()

        sign = post_dict.pop('sign', None)
        money = post_dict['total_amount']
        status = pay.parse_and_verify_result(post_dict)  # 验签
        print("status是多少：",status)
        if status:
        	# '''
        	# 支付成功后业务逻辑，这里有通知才是真正的完成了支付，return_url可以理解为理论上的成功，这个才是支付宝真的成功发送的请求
        	# '''
            return HttpResponse('success')
        else:
        	# '''
        	# 支付失败后业务逻辑
        	# '''
            return HttpResponse('')

    else:   # GET请求 前台回调
        params = request.GET.dict()
        print("params是什么样，",params)
        passback_params = params["out_trade_no"]
        token = passback_params[passback_params.index("-")+1:]
        order_id = passback_params[:passback_params.index("-")]
        payment = Payment.objects.get(order_id=order_id)
        print("payment是什么？？",payment)
        order = Order.objects.get(pk=order_id)
        print(payment)
        print("支付宝返回的token的值" , token)
        print("支付宝返回的订单的编号的值：",order_id)
        status = pay.parse_and_verify_result(params)  # 验签
        print("GET请求中，status是多少：",status)
        # status是一个对象，None时支付失败
        if status:
                try:
                    gateway_process_payment(
                        payment=payment, payment_token=token
                    )
                    print("**进入了try")
                except Exception as exc:
                    print("**发生了异常：",exc)
                else:
                    if order.is_fully_paid():
                        print("**马上重定向")
                        return redirect("order:payment-success", token=token)
                    return redirect(order.get_absolute_url())
        else:
            return HttpResponse('支付失败')
