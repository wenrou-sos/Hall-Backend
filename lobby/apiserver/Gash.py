import xml.dom.minidom
from pyDes import *
import base64
import hashlib
import requests
import random
from xml.etree.ElementTree import fromstring, ElementTree
import xmltodict
import env_setting
import pg_general
import dicttoxml

if env_setting.PRODUCTION_MODE == False:        # debug mode
    GASH_PASSWORD = 'dgjDmyhj97z='
    GASH_KEY = 'UfaySwgEvC5Vw8yM8i+AOkQ7NQL1sESp'
    GASH_IV = 'Z7ZB8jy5BxU='
    GASH_MID ='M1000831'
    GASH_CID = 'C008310001275'

    GASH_ORDER_URL = 'https://stage-api.eg.gashplus.com/CP_Module/order.aspx'
    GASH_SETTLE_URL = 'https://stage-api.eg.gashplus.com/CP_Module/settle.asmx?wsdl'
    GASH_CHECKORDER_URL = 'https://stage-api.eg.gashplus.com/CP_Module/checkorder.asmx?wsdl'
else:                                           # production mode
    GASH_PASSWORD = 'a9ngXSX9o=y'
    GASH_KEY = 'nsHYPo8NTRa9ngXSXHNOQWjR5X9L8tSB'
    GASH_IV = 'nrxJIVEtS0o='
    GASH_MID = 'M1000751'
    GASH_CID = 'C007510001380'

    GASH_ORDER_URL = 'https://api.eg.gashplus.com/CP_Module/order.aspx'
    GASH_SETTLE_URL = 'https://api.eg.gashplus.com/CP_Module/settle.asmx?wsdl'
    GASH_CHECKORDER_URL = 'https://api.eg.gashplus.com/CP_Module/checkorder.asmx?wsdl'


if env_setting.LOCAL_SERVER == True:
    GASH_WALLET_RETURN_URL = 'https://dev.jinsong.io/gash/wallet/ret'
    GASH_POINT_RETURN_URL = 'https://dev.jinsong.io/gash/point/ret'
elif env_setting.PRODUCTION_MODE == False:
    GASH_WALLET_RETURN_URL = 'https://inner.jinsong.io/gash/wallet/ret'
    GASH_POINT_RETURN_URL = 'https://inner.jinsong.io/gash/point/ret'
elif env_setting.PRODUCTION_MODE == True:
    GASH_WALLET_RETURN_URL = 'https://jinsong.io/gash/wallet/ret'
    GASH_POINT_RETURN_URL = 'https://jinsong.io/gash/point/ret'


GASH_WALLET_PAID = "COPGAM09"           # GASH 錢包代碼
GASH_POINT_PAID = "COPGAM05"            # GASH 點數代碼



def decode_b64xml(b64str):
    result = None
    try:
        decodestr = base64.b64decode(b64str).decode('utf-8')
        result = xmltodict.parse(decodestr)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "decode_b64xml Exception:{}".format(e))
    return result


def GetERQC(strAry):  # strAry = CID + COID + CUID + strAmount(12,2)
    PASSWORD = GASH_PASSWORD        # Issued by GASH+
    key = GASH_KEY                  # Issued by GASH+
    iv = GASH_IV                    # Issued by GASH+
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

def Make_Wallet_SendOder(memberid,transid,amount):
    MSG_TYPE = "0100"
    PCODE = "300000"
    CID =  GASH_CID
    COID = str(transid)
    CUID = "TWD"
    PAID = GASH_WALLET_PAID
    AMOUNT = amount
    ERQC = ""
    ORDER_TYPE = "M"
    RETURN_URL = GASH_WALLET_RETURN_URL
    POST_URL = GASH_ORDER_URL

    PRODUCT_ID = ""
    USER_ACCTID = str(memberid)


    strAmount = "%014d" % (AMOUNT * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)

    ERQC = GetERQC(strAry)

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
    nodeUSER_ACCTID = doc.createElement('USER_ACCTID')

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
    appendNodeAndText(nodeTRANS, nodeUSER_ACCTID,USER_ACCTID)

    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    # end of build xml string
    FormData = base64.b64encode(bytes(xmlStr, "utf-8"))
    strFormData = FormData.decode("utf-8")
    doc.unlink()
    return strFormData

def Make_Wallet_Settle(memberid,transid,amount):
    MSG_TYPE = "0500"
    PCODE = "300000"
    CID = GASH_CID
    COID = str(transid)
    CUID = "TWD"
    AMOUNT = amount
    PAID = GASH_WALLET_PAID

    strAmount = "%014d" % (amount * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)
    ERQC = GetERQC(strAry)

    doc = xml.dom.minidom.Document()
    nodeTRANS = doc.createElement("TRANS")

    nodeMSG_TYPE = doc.createElement("MSG_TYPE")
    nodePCODE = doc.createElement("PCODE")
    nodeERQC = doc.createElement("ERQC")
    nodeCID = doc.createElement("CID")
    nodeCOID = doc.createElement("COID")
    nodeCUID = doc.createElement("CUID")
    nodeAMOUNT = doc.createElement("AMOUNT")
    nodePAID = doc.createElement("PAID")

    appendNodeAndText(nodeTRANS, nodeMSG_TYPE, MSG_TYPE)
    appendNodeAndText(nodeTRANS, nodePCODE, PCODE)
    appendNodeAndText(nodeTRANS, nodeERQC, str(ERQC))
    appendNodeAndText(nodeTRANS, nodeCID, CID)
    appendNodeAndText(nodeTRANS, nodeCOID, COID)
    appendNodeAndText(nodeTRANS, nodeCUID, CUID)
    appendNodeAndText(nodeTRANS, nodeAMOUNT, str(AMOUNT))
    appendNodeAndText(nodeTRANS, nodePAID, PAID)
    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    Data = base64.b64encode(bytes(xmlStr, "utf-8"))
    strData = Data.decode("utf-8")
    doc.unlink()

    return strData


def Make_Wallet_Check(memberid,transid,amount):
    MSG_TYPE = "0100"
    PCODE = "200000"
    CID = GASH_CID
    COID = str(transid)
    CUID = "TWD"
    AMOUNT = amount


    strAmount = "%014d" % (amount * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)
    ERQC = GetERQC(strAry)


    doc = xml.dom.minidom.Document()
    nodeTRANS = doc.createElement("TRANS")

    nodeMSG_TYPE = doc.createElement("MSG_TYPE")
    nodePCODE = doc.createElement("PCODE")
    nodeERQC = doc.createElement("ERQC")
    nodeCID = doc.createElement("CID")
    nodeCOID = doc.createElement("COID")
    nodeCUID = doc.createElement("CUID")
    nodeAMOUNT = doc.createElement("AMOUNT")


    appendNodeAndText(nodeTRANS, nodeMSG_TYPE, MSG_TYPE)
    appendNodeAndText(nodeTRANS, nodePCODE, PCODE)
    appendNodeAndText(nodeTRANS, nodeERQC, str(ERQC))
    appendNodeAndText(nodeTRANS, nodeCID, CID)
    appendNodeAndText(nodeTRANS, nodeCOID, COID)
    appendNodeAndText(nodeTRANS, nodeCUID, CUID)
    appendNodeAndText(nodeTRANS, nodeAMOUNT, str(AMOUNT))

    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    Data = base64.b64encode(bytes(xmlStr, "utf-8"))
    strData = Data.decode("utf-8")
    doc.unlink()



    return strData

def Make_Point_SendOder(memberid,transid,amount):
    MSG_TYPE = "0100"
    PCODE = "300000"
    CID =  GASH_CID
    COID = str(transid)
    CUID = "TWD"
    PAID = GASH_POINT_PAID
    AMOUNT = amount
    ERQC = ""
    ORDER_TYPE = "M"
    RETURN_URL = GASH_POINT_RETURN_URL
    POST_URL = GASH_ORDER_URL

    PRODUCT_ID = ""
    USER_ACCTID = str(memberid)


    strAmount = "%014d" % (AMOUNT * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)

    ERQC = GetERQC(strAry)

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
    nodeUSER_ACCTID = doc.createElement('USER_ACCTID')

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
    appendNodeAndText(nodeTRANS, nodeUSER_ACCTID,USER_ACCTID)

    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    # end of build xml string
    FormData = base64.b64encode(bytes(xmlStr, "utf-8"))
    strFormData = FormData.decode("utf-8")
    doc.unlink()
    return strFormData


def Make_Point_Settle(memberid, transid, amount):
    MSG_TYPE = "0500"
    PCODE = "300000"
    CID = GASH_CID
    COID = str(transid)
    CUID = "TWD"
    AMOUNT = amount
    PAID = GASH_POINT_PAID

    strAmount = "%014d" % (amount * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)
    ERQC = GetERQC(strAry)

    doc = xml.dom.minidom.Document()
    nodeTRANS = doc.createElement("TRANS")

    nodeMSG_TYPE = doc.createElement("MSG_TYPE")
    nodePCODE = doc.createElement("PCODE")
    nodeERQC = doc.createElement("ERQC")
    nodeCID = doc.createElement("CID")
    nodeCOID = doc.createElement("COID")
    nodeCUID = doc.createElement("CUID")
    nodeAMOUNT = doc.createElement("AMOUNT")
    nodePAID = doc.createElement("PAID")

    appendNodeAndText(nodeTRANS, nodeMSG_TYPE, MSG_TYPE)
    appendNodeAndText(nodeTRANS, nodePCODE, PCODE)
    appendNodeAndText(nodeTRANS, nodeERQC, str(ERQC))
    appendNodeAndText(nodeTRANS, nodeCID, CID)
    appendNodeAndText(nodeTRANS, nodeCOID, COID)
    appendNodeAndText(nodeTRANS, nodeCUID, CUID)
    appendNodeAndText(nodeTRANS, nodeAMOUNT, str(AMOUNT))
    appendNodeAndText(nodeTRANS, nodePAID, PAID)
    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    Data = base64.b64encode(bytes(xmlStr, "utf-8"))
    strData = Data.decode("utf-8")
    doc.unlink()

    return strData

def Make_Point_Check(memberid,transid,amount):
    MSG_TYPE = "0100"
    PCODE = "200000"
    CID = GASH_CID
    COID = str(transid)
    CUID = "TWD"
    AMOUNT = amount


    strAmount = "%014d" % (amount * 100)
    strAry = "%s%s%s%s" % (CID, COID, CUID, strAmount)
    ERQC = GetERQC(strAry)


    doc = xml.dom.minidom.Document()
    nodeTRANS = doc.createElement("TRANS")

    nodeMSG_TYPE = doc.createElement("MSG_TYPE")
    nodePCODE = doc.createElement("PCODE")
    nodeERQC = doc.createElement("ERQC")
    nodeCID = doc.createElement("CID")
    nodeCOID = doc.createElement("COID")
    nodeCUID = doc.createElement("CUID")
    nodeAMOUNT = doc.createElement("AMOUNT")


    appendNodeAndText(nodeTRANS, nodeMSG_TYPE, MSG_TYPE)
    appendNodeAndText(nodeTRANS, nodePCODE, PCODE)
    appendNodeAndText(nodeTRANS, nodeERQC, str(ERQC))
    appendNodeAndText(nodeTRANS, nodeCID, CID)
    appendNodeAndText(nodeTRANS, nodeCOID, COID)
    appendNodeAndText(nodeTRANS, nodeCUID, CUID)
    appendNodeAndText(nodeTRANS, nodeAMOUNT, str(AMOUNT))

    doc.appendChild(nodeTRANS)
    xmlStr = doc.toprettyxml()
    Data = base64.b64encode(bytes(xmlStr, "utf-8"))
    strData = Data.decode("utf-8")
    doc.unlink()



    return strData


if __name__ == '__main__':
    Make_Wallet_SendOder(2404,47,150)
    Make_Wallet_Settle(2404,47,150)


    # SendOder()
    # decode_b64xml('PFRSQU5TPjxNU0dfVFlQRT4wMTEwPC9NU0dfVFlQRT48UENPREU+MzAwMDAwPC9QQ09ERT48Q0lEPkMwMDgzMTAwMDEyNzU8L0NJRD48Q09JRD40MDwvQ09JRD48UlJOPkdQMjAwMTE1UzAwMDAwMjE8L1JSTj48Q1VJRD5UV0Q8L0NVSUQ+PFBBSUQ+Q09QR0FNMDk8L1BBSUQ+PEFNT1VOVD4xNTA8L0FNT1VOVD48RVJQQz5sbUsxODdsYm00cXhzRWRURGFzWnhVSmU5RUk9PC9FUlBDPjxPUkRFUl9UWVBFPjwvT1JERVJfVFlQRT48UEFZX1NUQVRVUz5TPC9QQVlfU1RBVFVTPjxQQVlfUkNPREU+MDAwMDwvUEFZX1JDT0RFPjxSQ09ERT4wMDAwPC9SQ09ERT48RVJQX0lEPlBJTkhBTEw8L0VSUF9JRD48TUlEPk0xMDAwODMxPC9NSUQ+PEJJRD48L0JJRD48TUVNTz48L01FTU8+PFBST0RVQ1RfTkFNRT5HQVNIUE9JTlTph5HmtYHmnI3li5k8L1BST0RVQ1RfTkFNRT48UFJPRFVDVF9JRD5QSU5IQUxMPC9QUk9EVUNUX0lEPjxVU0VSX0FDQ1RJRD4yNDA0PC9VU0VSX0FDQ1RJRD48VVNFUl9HUk9VUElEPjwvVVNFUl9HUk9VUElEPjxVU0VSX0lQPjExNC4zMy43MS40PC9VU0VSX0lQPjxFWFRFTlNJT04+PC9FWFRFTlNJT04+PEdQU19JTkZPPjwvR1BTX0lORk8+PFNZU1RJTUU+MjAyMC0wMS0xNSAxMTowMToxNDwvU1lTVElNRT48VFhUSU1FPjIwMjAwMTE1MTEwMTA3PC9UWFRJTUU+PC9UUkFOUz4=')
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






