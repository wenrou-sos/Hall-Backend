from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify,make_response
from flask_login import login_required, current_user,login_user
from . import main,API_SERVER_URL
import datetime
import requests as rq
import json
import xml.dom.minidom
from pyDes import *
import base64
import hashlib
import requests
from xml.etree import cElementTree as ElementTree
import pg_general
import env_setting
import xmltodict
import time
from ecpay_invoice.ecpay_main import *


if env_setting.PRODUCTION_MODE == False:
    ECPAY_LOVE_CODE_CHECK_URL = 'https://einvoice-stage.ecpay.com.tw/Query/CheckLoveCode'
    ECPAY_BARCODE_CHECK_URL = 'https://einvoice-stage.ecpay.com.tw/Query/CheckMobileBarCode'
    MERCHANTID = '2000132'
    HASHKEY = 'ejCk326UnaZWKisg'
    HASHIV = 'q9jcZX8Ib9LM8wYk'

else:
    ECPAY_LOVE_CODE_CHECK_URL = 'https://einvoice.ecpay.com.tw/Query/CheckLoveCode'
    ECPAY_BARCODE_CHECK_URL = 'https://einvoice.ecpay.com.tw/Query/CheckMobileBarCode'
    MERCHANTID = '3187789'
    HASHKEY = 'o6D75PIvuYMbSCE6'
    HASHIV = 'R0vvRIja0A0CmlvG'




@main.route('/ecpay/CheckLoveCode', methods=['POST'])
def checklovecode():
    CheckCode = request.form.get('LoveCode')

    ecpay_invoice = EcpayInvoice()
    ecpay_invoice.MerchantID = MERCHANTID
    ecpay_invoice.HashKey = HASHKEY
    ecpay_invoice.HashIV = HASHIV


    # 寫入基本介接參數
    ecpay_invoice.Invoice_Method = 'CHECK_LOVE_CODE'
    ecpay_invoice.Invoice_Url = ECPAY_LOVE_CODE_CHECK_URL

    # 3.寫入發票相關資訊
    ecpay_invoice.Send['LoveCode'] = CheckCode

    # 4. 送出
    aReturn_Info = ecpay_invoice.Check_Out()

    # print('return:' + aReturn_Info.get('IsExist'))
    if aReturn_Info.get('IsExist') == 'Y':
        return make_response('Y')
    else:
        return make_response('N')


@main.route('/ecpay/CheckMobileBarCode', methods=['POST'])
def ecpay_checkbarcode():
    CheckCode = request.form.get('BarCode')

    ecpay_invoice = EcpayInvoice()
    ecpay_invoice.MerchantID = MERCHANTID
    ecpay_invoice.HashKey = HASHKEY
    ecpay_invoice.HashIV = HASHIV
    # 寫入基本介接參數
    ecpay_invoice.Invoice_Method = 'CHECK_MOBILE_BARCODE'
    ecpay_invoice.Invoice_Url = ECPAY_BARCODE_CHECK_URL

    # 3.寫入發票相關資訊
    ecpay_invoice.Send['BarCode'] = CheckCode

    # 4. 送出
    aReturn_Info = ecpay_invoice.Check_Out()

    if aReturn_Info.get('IsExist') == 'Y':
        return make_response('Y')
    else:
        return make_response('N')

@main.route('/ecpay/startPurchase', methods=['POST'])
def ecpay_startPurchase():

    resultdata = {}

    ecpaydata = request.form

    memberid = ecpaydata.get('memberid')
    token = ecpaydata.get('token')
    amount = ecpaydata.get('Amount')

    # 先看memberid的log，比對玩家是否不是機器人帳號
    check_member = pg_general.is_robot_or_not("ecpay_startPurchase", memberid)
    # 確認memberid，若是機器人自動帳號，則退回玩家顯示儲值失敗
    if check_member["statuscode"] != 0:
        return make_response(check_member)

    if None in [memberid,token,amount] or token != '1':
        resultdata['code'] = "99"
        resultdata['msg'] = '未登入, 請先登入再進行購買, 謝謝您'

    else:

        r = rq.get(
            API_SERVER_URL + 'web/api/ecpay_credit_start_purchase/',params=ecpaydata)
        resultdata =json.loads(r.text)

    resp = make_response(resultdata)

    return resp


@main.route('/ecpay/serverorderresult', methods=['POST'])
def ecpay_server_order_result():
    try:
        result = False
        resultdata = '1'


        resp = make_response('1')
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            "ecpay_server_order_result Exception:{},requestform:{}".format(e, request.form))
    resp = make_response(resultdata)
    return resp
@main.route('/ecpay/clientorderresult', methods=['POST'])
def ecpay_client_orderresult():
    try:

        resultdata = ''
        params = request.form
        r = rq.get(
            API_SERVER_URL + 'web/api/ecpay_credit_order_result/', params=params)

        resultdata = json.loads(r.text)

        status_code = resultdata.get('status_code')
        showstr = resultdata.get('showstr')
        if status_code == 0:
            strmsg = 'alert("{0}");'.format(showstr)
        else:
            strmsg = 'alert("儲值失敗,請重新儲值");'

        if env_setting.LOCAL_SERVER == True:
            returnurl = "https://dev.jinsong.io"
        elif env_setting.PRODUCTION_MODE == False:
            returnurl = "https://inner.jinsong.io"
        else:
            returnurl = "https://jinsong.io"

        resultdata = '<html><head><title>Close</title>' \
                     '<script>' \
                     'function show() {' + '{0}'.format(strmsg)

        resultdata +=' window.location.href ="{0}"'.format(returnurl) + '}'

        resultdata +='</script>' \
                     '</head><body onload="show();">' \
                     '</body></html>'

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "ecpay_client_orderresult Exception:{},requestform:{}".format(e,request.form))


    resp = make_response(resultdata)

    return resp
