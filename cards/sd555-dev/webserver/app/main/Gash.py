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

GASH_PASSWORD = 'dgjDmyhj97z='
GASH_KEY = 'UfaySwgEvC5Vw8yM8i+AOkQ7NQL1sESp'
GASH_IV = 'Z7ZB8jy5BxU='



if env_setting.PRODUCTION_MODE == False:
    GASH_RETURN_URL = 'https://dev.jinsong.io'
    GASH_ORDER_URL = 'https://stage-api.eg.gashplus.com/CP_Module/order.aspx'
    GASH_SETTLE_URL = 'https://stage-api.eg.gashplus.com/CP_Module/settle.asmx'
    GASH_CHECKORDER_URL = 'https://stage-api.eg.gashplus.com/CP_Module/checkorder.asmx'
else:
    GASH_RETURN_URL = 'https://jinsong.io'
    GASH_ORDER_URL = 'https://api.eg.gashplus.com/CP_Module/order.aspx'
    GASH_SETTLE_URL = 'https://api.eg.gashplus.com/CP_Module/settle.asmx'
    GASH_CHECKORDER_URL = 'https://api.eg.gashplus.com/CP_Module/checkorder.asmx'


def decode_b64xml(b64str):
    result = None
    try:
        decodestr = base64.b64decode(b64str).decode('utf-8')
        result = xmltodict.parse(decodestr)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "decode_b64xml Exception:{}".format(e))
    return result


@main.route('/gash/wallet/ret', methods=['POST','GET'])
def gps_wallet_result():
    resultb64 = request.form.get('data')

    params = {"data": resultb64}
    r = rq.get(
        API_SERVER_URL + 'web/api/ret_gash_wallet_base64/',params=params)

    resultdata = json.loads(r.text)

    status_code = resultdata.get('status_code')
    showstr = resultdata.get('showstr')
    if status_code == 0:
        strmsg = 'alert("{0}");'.format(showstr)
    else:
        strmsg = 'alert("儲值失敗,請重新儲值");'

    resultdata='<html><head><title>Close</title>' \
               '<script>' \
                'function show() {' + '{0}'.format(strmsg) + \
               'window.close();}' \
               '</script>' \
               '</head><body onload="show();">' \
               '</body></html>'
    resp = make_response(resultdata)

    return resp

@main.route('/gash/point/ret', methods=['POST','GET'])
def gps_point_result():
    resultb64 = request.form.get('data')

    params = {"data": resultb64}
    r = rq.get(
        API_SERVER_URL + 'web/api/ret_gash_point_base64/',params=params)


    resultdata = json.loads(r.text)

    status_code = resultdata.get('status_code')
    showstr = resultdata.get('showstr')
    if status_code == 0:
        strmsg = 'alert("{0}");'.format(showstr)
    else:
        strmsg = 'alert("儲值失敗,請重新儲值");'

    resultdata='<html><head><title>Close</title>' \
               '<script>' \
                'function show() {' + '{0}'.format(strmsg) + \
               'window.close();}' \
               '</script>' \
               '</head><body onload="show();">' \
               '</body></html>'
    resp = make_response(resultdata)

    return resp





def GetERQC(strAry):  # strAry = CID + COID + CUID + strAmount(12,2)
    PASSWORD = GASH_PASSWORD # Issued by GASH+
    key =  GASH_KEY # Issued by GASH+
    iv =  GASH_IV # Issued by GASH+
    ERQC_DATA = strAry + PASSWORD

    tripleDesKey = base64.b64decode(key)
    tripleDesIv = base64.b64decode(iv)
    tripleDesEncoder = triple_des(tripleDesKey, CBC, tripleDesIv, pad=None, padmode=PAD_PKCS5)
    tripleDesOutput = tripleDesEncoder.encrypt(ERQC_DATA)
    tripleDesOutputBase64 = base64.b64encode(tripleDesOutput)

    SHA1 = hashlib.sha1()
    SHA1.update(tripleDesOutputBase64)
    result = base64.b64encode(SHA1.digest()).decode('utf-8')
    return result


def appendNodeAndText(parentNode, node, text):
    doc = xml.dom.minidom.Document()
    textNode = doc.createTextNode(text)
    node.appendChild(textNode)
    parentNode.appendChild(node)

def SendOder():
    MSG_TYPE = "0100"
    PCODE = "300000"
    CID =  "C008310001275"
    COID =  "test-0001"
    CUID = "TWD"
    PAID = "COPGAM09"
    AMOUNT = 100
    ERQC = ""
    ORDER_TYPE = "M"
    RETURN_URL = GASH_RETURN_URL + "/gps/result"
    POST_URL = GASH_ORDER_URL
    # POST_URL = "https://api.eg.gashplus.com/CP_Module/order.aspx"
    PRODUCT_ID = ""
    USER_ACCTID = ""


    strAmount = "%014d" % (AMOUNT * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)

    ERQC = GetERQC(strAry)

    # build xml string
    doc = xml.dom.minidom.Document()
    nodeTRANS = doc.createElement("TRANS")

    nodeMSG_TYPE = doc.createElement("MSG_TYPE")
    nodePCODE = doc.createElement("PCODE")
    nodeERQC = doc.createElement("ERQC")
    nodeCID = doc.createElement("CID")
    nodeCOID = doc.createElement("COID")
    nodeCUID = doc.createElement("CUID")
    nodePAID = doc.createElement("PAID")
    nodeAMOUNT = doc.createElement("AMOUNT")
    nodeRETURN_URL = doc.createElement("RETURN_URL")
    nodeORDER_TYPE = doc.createElement("ORDER_TYPE")

    appendNodeAndText(nodeTRANS, nodeMSG_TYPE, MSG_TYPE)
    appendNodeAndText(nodeTRANS, nodePCODE, PCODE)
    appendNodeAndText(nodeTRANS, nodeERQC, str(ERQC))
    appendNodeAndText(nodeTRANS, nodeCID, CID)
    appendNodeAndText(nodeTRANS, nodeCOID, COID)
    appendNodeAndText(nodeTRANS, nodeCUID, CUID)
    appendNodeAndText(nodeTRANS, nodePAID, PAID)
    appendNodeAndText(nodeTRANS, nodeAMOUNT, str(AMOUNT))
    appendNodeAndText(nodeTRANS, nodeRETURN_URL, RETURN_URL)
    appendNodeAndText(nodeTRANS, nodeORDER_TYPE, ORDER_TYPE)

    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    # end of build xml string

    FormData = base64.b64encode(bytes(xmlStr, "utf-8"))
    strFormData = FormData.decode("utf-8")





def DecodeOrder():

    returnstr = 'PFRSQU5TPjxNU0dfVFlQRT4wMTEwPC9NU0dfVFlQRT48UENPREU+MzAwMDAwPC9QQ09ERT48Q0lEPkMwMDgzMTAwMDEyNzU8L0NJRD48Q09JRD4xMjMxMjMxOTIzMjwvQ09JRD48UlJOPkdQMjAwMTE0UzAwMDAwMjY8L1JSTj48Q1VJRD5UV0Q8L0NVSUQ+PFBBSUQ+Q09QR0FNMDk8L1BBSUQ+PEFNT1VOVD4xMDA8L0FNT1VOVD48RVJQQz41cTByS2E0OGpHRkhWbFQwNVIzemdSWkgvbWM9PC9FUlBDPjxPUkRFUl9UWVBFPjwvT1JERVJfVFlQRT48UEFZX1NUQVRVUz5TPC9QQVlfU1RBVFVTPjxQQVlfUkNPREU+MDAwMDwvUEFZX1JDT0RFPjxSQ09ERT4wMDAwPC9SQ09ERT48RVJQX0lEPlBJTkhBTEw8L0VSUF9JRD48TUlEPk0xMDAwODMxPC9NSUQ+PEJJRD48L0JJRD48TUVNTz48L01FTU8+PFBST0RVQ1RfTkFNRT5HQVNIUE9JTlTph5HmtYHmnI3li5k8L1BST0RVQ1RfTkFNRT48UFJPRFVDVF9JRD5QSU5IQUxMPC9QUk9EVUNUX0lEPjxVU0VSX0FDQ1RJRD50ZXN0MTIzPC9VU0VSX0FDQ1RJRD48VVNFUl9HUk9VUElEPjwvVVNFUl9HUk9VUElEPjxVU0VSX0lQPjExNC4zMy43MS40PC9VU0VSX0lQPjxFWFRFTlNJT04+PC9FWFRFTlNJT04+PEdQU19JTkZPPjwvR1BTX0lORk8+PFNZU1RJTUU+MjAyMC0wMS0xNCAxMTowNDo1MjwvU1lTVElNRT48VFhUSU1FPjIwMjAwMTE0MTEwNDMxPC9UWFRJTUU+PC9UUkFOUz4='

    base64str = '<TRANS><MSG_TYPE>0110</MSG_TYPE><PCODE>300000</PCODE><CID>C008310001275</CID><COID>12312319232</COID><RRN>GP200114S0000026</RRN><CUID>TWD</CUID><PAID>COPGAM09</PAID><AMOUNT>100</AMOUNT><ERPC>5q0rKa48jGFHVlT05R3zgRZH/mc=</ERPC><ORDER_TYPE></ORDER_TYPE><PAY_STATUS>S</PAY_STATUS><PAY_RCODE>0000</PAY_RCODE><RCODE>0000</RCODE><ERP_ID>PINHALL</ERP_ID><MID>M1000831</MID><BID></BID><MEMO></MEMO><PRODUCT_NAME>GASHPOINT金流服務</PRODUCT_NAME><PRODUCT_ID>PINHALL</PRODUCT_ID><USER_ACCTID>test123</USER_ACCTID><USER_GROUPID></USER_GROUPID><USER_IP>114.33.71.4</USER_IP><EXTENSION></EXTENSION><GPS_INFO></GPS_INFO><SYSTIME>2020-01-14 11:04:52</SYSTIME><TXTIME>20200114110431</TXTIME></TRANS>'



if __name__ == '__main__':
    # SendOder()
    DecodeOrder()
# form submit with this strFormData
# example
# <!DOCTYPE html>
# <html>
# <head>
#  <title></title>
# </head>
# <body>
# <form id="form1" name="form1" method="post" action='<%= $POST_URL %>'>
# <div>
#	<input id="data" name="data" type="hidden" value='<%= $strFormData %>' />
# </div>
# <input type="submit" Value="SUBMIT"/><br/>
# </form>
# </body>
# </html>






