import random
import time
from django.http import HttpResponse
from django.shortcuts import redirect, render
# from alipay import AliPay
from all_pay import PayOrder
from all_pay import Pay
from all_pay.wx import WxPay
from payment_lipay.settings import AliPayConfig
# 注意：uid参数可不要，此处因生成订单号要使用，所以添加，测试证明沙箱环境下添加自定义参数回调函数也可正常访问，正式环境下还没有测试，待测试后再做说明

# 充值页面
# def pay_page(request):
#     return render(request, 'user_center/pay_page.html')

def index(request):
    return render(request,'index.html',None)


# 生成订单号(自定义)
def order_num(package_num,uid):
    '''
    商品代码后两位+下单时间后十二位+用户id后四位+随机数四位
    :param package_num: 商品代码
    :return: 唯一的订单号
    '''
    local_time = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))[2:]
    result = str(package_num)[-2:] + local_time +uid[-4:]+str(random.randint(1000,9999))
    return result


# 获取一个Alipay对象
def get_ali_object():
    # 沙箱环境地址：https://openhome.alipay.com/platform/appDaily.htm?tab=info
    # 正式启用时需要重新配置app_id ，merchant_private_key_path ，alipay_public_key_path
    app_id = "2016092700607535"  # APPID  沙箱应用

    # 支付完成后支付宝向这里发送一个post请求，如果识别为局域网ip，支付宝找不到，alipay_result（）接受不到这个请求
    notify_url = AliPayConfig.notify_url

    # 支付完成后跳转的地址
    return_url = AliPayConfig.return_url

    # 应用私钥
    merchant_private_key_path = AliPayConfig.merchant_private_key_path
    # 支付宝公钥
    alipay_public_key_path = AliPayConfig.alipay_public_key_path # 验证支付宝回传消息使用
    wx_apiclient_cert_path = AliPayConfig.wx_apiclient_cert_path
    wx_apiclient_key_path = AliPayConfig.wx_apiclient_key_path
    app_private_key_string = open(merchant_private_key_path).read()
    alipay_public_key_string = open(alipay_public_key_path).read()
    ALIPAY_CONFIG = {
        'pay_type': 'ali_pay',
        'app_id': app_id,  # 必填 应用id
        'private_key_path': merchant_private_key_path,  # 必填 应用私钥
        'public_key_path': alipay_public_key_path,  # 必填 支付宝公钥
        'notify_url': notify_url,  # 异步回调地址
        'sign_type': 'RSA2',  # 签名算法 RSA 或者 RSA2
        'debug': True,  # 是否是沙箱模式
    }

    WECHAT_CONFIG = {
        'pay_type': 'wx_pay',  # 必填 区分支付类型
        'app_id': 'ww58ea0a6e86779b7c',  # 必填,应用id
        'mch_key': 'alphamalizhaojunalphamalizhaojun',  # 必填,商户平台密钥
        'mch_id': '1571129241',  # 必填,微信支付分配的商户号
        'app_secret': 'alphamalizhaojunalphamalizhaojun',  # 应用密钥
        'notify_url': notify_url,  # 异步回调地址
        'api_cert_path': wx_apiclient_cert_path,  # API证书
        'api_key_path': wx_apiclient_key_path,  # API证书 key
        'trade_type':  'NATIVE'
    }
    return WECHAT_CONFIG

def alipay2(result):

    return redirect("/alipay/")

# 账户充值（支付宝）视图函数
def alipay(request):
    '''根据当前用户的配置生成url，并跳转'''
    # 我试试请求重定向可以吗，所以这里接收不到post的参数
    money = 25.5;
    WECHAT_CONFIG = get_ali_object()
    # 生成支付的url
    # query_params = alipay.api_alipay_trade_page_pay(
    #     subject="测试订单",
    #     out_trade_no="2017020100",
    #     total_amount=100.25,
    #     return_url="http://192.168.133.1/pay/alipay_result/"
    # )
    # 额外参数，某些支付方式有些选填的参数在PayOrder并没有封装，可以自行传递
    # extra_params = {
    #     'xxx': 'xxx'
    # }                                                                     //按照分来的
    order = PayOrder.Builder().subject('测试订单').product_id("12332").out_trade_no("dkf123").total_fee(1).return_url("http://192.168.133.1/pay/alipay_result/").build()
    pay = Pay(WECHAT_CONFIG)  # 传入对应支付方式配置
    order_res = pay.trade_page_pay(order)  # 传入对应订单和额外参数（要是需要），extra_params可作为第二个参数传入，
    # 支付url
    # print("order_res",order_res)
    # pay_url = "https://openapi.alipaydev.com/gateway.do?{0}".format(order_res)  # 支付宝网关地址（沙箱应用）
    print(order_res)

    # 生成微信支付二维码
    import qrcode

    qr = qrcode.QRCode(
        version=7,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(order_res)
    qr.make(fit=True)
    img = qr.make_image()

    img.save("static/imgs/test.png")
    return render(request, "wxpay.html", {})


from all_pay.pay_error import PayError, PayValidationError, WxPayError


# 微信支付结果通知
def alipay_result2(request):
    data = trans_xml_to_dict(request.body)
    print("data是什么情况：",data)
    # 验证签名
    flag = verify(data)
    print("flag::",flag)
    print("结果",data['return_code'])
    if flag and data['return_code'] == 'SUCCESS':
        print("----微信支付成功----")
        return HttpResponse(trans_dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))
    print("验证失败")
    return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))

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

    alipay = get_ali_object()
    if request.method == "POST":  # POST方法后台回调，只能在外网服务器测试
        # 检测是否支付成功
        # 去请求体中获取所有返回的参数：状态/订单号
        post_dict = request.POST.dict()

        sign = post_dict.pop('sign', None)
        money = post_dict['total_amount']
        status = alipay.verify(post_dict, sign)  # 验签
        if status:
        	# '''
        	# 支付成功后业务逻辑，这里有通知才是真正的完成了支付，return_url可以理解为理论上的成功，这个才是支付宝真的成功发送的请求
        	# '''
            print( "这是我测试用的：：", post_dict['passback_params'])
            return HttpResponse('success')
        else:
        	# '''
        	# 支付失败后业务逻辑
        	# '''
            return HttpResponse('')

    else:   # GET请求 前台回调
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = alipay.verify(params, sign)  # 验签
        if status:
            return HttpResponse('支付成功')
        else:
            return HttpResponse('支付失败')
