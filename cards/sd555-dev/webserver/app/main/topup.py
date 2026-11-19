from app import User
from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify,make_response
from flask_login import login_required, current_user,login_user
from . import main,API_SERVER_URL
import datetime
import requests as rq
import json
import webbrowser
import pg_general
import env_setting

# MyCard儲值方式
# 3-1 智冠驗證廠商通行證
@main.route('/mycard/gashpoints', methods=['GET'])
def mycard_gashpoints_webserver():
    # 取得前端的值
    CustomerId = request.args.get("CustomerId", "")  # 智冠的CustomerId = 金爽的memberid
    SandBoxMode = request.args.get("SandBoxMode", "false")  # 是否為測試環境：不是布林值，是小寫字串
    FacReturnURL = request.args.get("FacReturnURL", "")  # 交易結果回傳網址
    Amount = request.args.get("Amount", "")  # 金額

    # 先看memberid的log，比對玩家是否不是機器人帳號
    check_member = pg_general.is_robot_or_not("mycard_gashpoints", CustomerId)    # 智冠的CustomerId = 金爽的memberid
    # 確認memberid，若是機器人自動帳號，則退回玩家顯示儲值失敗
    if check_member["statuscode"] != 0:
        return make_response(check_member)

    # 取得回傳結果
    r = rq.get(API_SERVER_URL + 'mycard/gashpoints/?CustomerId={0}&SandBoxMode={1}&FacReturnURL={2}&Amount={3}'.format(CustomerId, SandBoxMode, FacReturnURL, Amount))
    # 整理成JsonLoad
    resp = json.loads(r.text)
    # 再轉成JsonDumps
    return make_response(resp)

# 3-2-4 確認交易並回傳交易結果給廠商 → 接收回傳交易結果
@main.route('/mcresult', methods=['POST'])
def mycard_mcresult_webserver():
    # 取得智冠回傳的3.4.2參數
    ReturnCode = request.form.get("ReturnCode", "")    # 回傳結果代碼
    ReturnMsg = request.form.get("ReturnMsg", "")    # 訊息描述
    PayResult = request.form.get("PayResult", "")    # 交易結果代碼
    FacTradeSeq = request.form.get("FacTradeSeq", "")    # 廠商交易序號
    PaymentType = request.form.get("PaymentType", "")    # 付費方式
    Amount = request.form.get("Amount", "")    # 金額
    Currency = request.form.get("Currency", "")    # 幣別
    MyCardTradeNo = request.form.get("MyCardTradeNo", "")    # 卡片號碼，或會員扣點交易序號，端看PaymentType而定
    # PaymentType = INGAME時，傳MyCard卡片號碼
    # PaymentType = COSTPOINT時，傳會員扣點交易序號，格式為MMS開頭+數字
    # 其餘PaymentType為Billing小額付款交易，傳Billing交易序號

    MyCardType = request.form.get("MyCardType", "")    # 通路代碼，PaymentType = INGAME時才有值
    PromoCode = request.form.get("PromoCode", "")    # 活動代碼
    Hash = request.form.get("Hash", "")    # 驗證碼

    # 開始3-2-4
    r = rq.get(API_SERVER_URL + 'mycard/mcresult/?ReturnCode={0}&ReturnMsg={1}&PayResult={2}&FacTradeSeq={3}&PaymentType={4}&Amount={5}&Currency={6}&MyCardTradeNo={7}&MyCardType={8}&PromoCode={9}&Hash={10}'.format(ReturnCode, ReturnMsg, PayResult, FacTradeSeq, PaymentType, Amount, Currency, MyCardTradeNo, MyCardType, PromoCode, Hash))
    # json.loads
    resp3_2 = json.loads(r.text)

    # 判斷3-2-4的參數有沒有新增到資料庫
    if resp3_2["status_code"] != 200:
        if env_setting.PRODUCTION_MODE == False:
            return redirect("https://inner.jinsong.io/deposit.html?message=a02zx02")
        else:
            return redirect("https://jinsong.io/deposit.html?message=a02zx02")

    # 開始3-3
    resp3_3 = mycard_checkMyCardTradeResult_webserver(FacTradeSeq)

    # 判斷3-3的"status_code"
    if resp3_3["status_code"] != 200:
        if env_setting.PRODUCTION_MODE == False:
            return redirect("https://inner.jinsong.io/deposit.html?message=a02zx02")
        else:
            return redirect("https://jinsong.io/deposit.html?message=a02zx02")

    # 開始3-4
    AuthCode = resp3_3["AuthCode"]
    SandBoxMode = resp3_3["SandBoxMode"]
    Amount = resp3_3["Amount"]
    CustomerId = resp3_3["CustomerId"]
    TradeSeq = resp3_3["TradeSeq"]
    MyCardTradeNo = resp3_3["MyCardTradeNo"]
    FacTradeSeq = resp3_3["FacTradeSeq"]
    Currency = resp3_3["Currency"]
    PaymentType = resp3_3["PaymentType"]
    resp3_4 = mycard_mycardReturnInvoiceResult_webserver(AuthCode, SandBoxMode, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType)

    # 錯誤回傳
    if resp3_4["status_code"] != 200:
        if env_setting.PRODUCTION_MODE == False:
            return redirect("https://inner.jinsong.io/deposit.html?message=a02zx02")
        else:
            return redirect("https://jinsong.io/deposit.html?message=a02zx02")
    # 正確回傳
    else:
        if env_setting.PRODUCTION_MODE == False:
            return redirect("https://inner.jinsong.io/deposit.html?message=w09se29")
        else:
            return redirect("https://jinsong.io/deposit.html?message=w09se29")

# 3-3 驗證MyCard交易結果
def mycard_checkMyCardTradeResult_webserver(FacTradeSeq):
    # 取得回傳結果
    r = rq.get(API_SERVER_URL + 'mycard/checkMyCardTradeResult/?FacTradeSeq={0}'.format(FacTradeSeq))
    # 整理成JsonLoad
    resp3_3 = json.loads(r.text)
    return resp3_3

# 3-4 確認MyCard交易，並進行請款
def mycard_mycardReturnInvoiceResult_webserver(AuthCode, SandBoxMode, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType):
    # 取得回傳結果
    r = rq.get(API_SERVER_URL + 'mycard/mycardReturnInvoiceResult/?AuthCode={0}&SandBoxMode={1}&Amount={2}&CustomerId={3}&TradeSeq={4}&MyCardTradeNo={5}&FacTradeSeq={6}&Currency={7}&PaymentType={8}'.format(AuthCode, SandBoxMode, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType))
    # 整理成JsonLoad
    resp3_4 = json.loads(r.text)
    return resp3_4

# 3-6 補儲值
@main.route('/mcredeposit', methods=['POST'])
def mycard_mcredeposit_webserver():
    pg_general.writelog(pg_general.PG_LogerLevel.info, 'call 3-6 api success')
    Data_3_6 = request.form.get("DATA")   # 取得智冠form的dict
    # eval str to dict
    Data_3_6 = eval(Data_3_6)
    # 處理參數
    ReturnCode = Data_3_6.get("ReturnCode", "")     # 查詢結果代碼
    ReturnMsg = Data_3_6.get("ReturnMsg", "")     # 訊息描述
    FacServiceId = Data_3_6.get("FacServiceId", "")    # 廠商服務代碼
    FacTradeSeq = Data_3_6.get("FacTradeSeq", "")   # 廠商交易序號(list可能是多筆)

    # 正確訊息回傳用的list
    fetch_all_3_6 = []
    # 如果智冠沒有給相關序號與代碼
    if ReturnCode == "" or ReturnMsg == "" or FacServiceId == "" or FacTradeSeq == "":
        r = {"return_msg": "3-6相關參數沒有給", "status_code": -1}
        # 參數不完整的訊息回傳給智冠
        return make_response(r)

    # 交易序號可能有多筆，一筆一筆處理
    for i in FacTradeSeq:
        # 3-6將智冠通知的補儲值訊息儲存至資料庫
        r = rq.get(API_SERVER_URL + 'mycard/mcredeposit/?ReturnCode={0}&ReturnMsg={1}&FacServiceId={2}&FacTradeSeq={3}'.format(ReturnCode, ReturnMsg, FacServiceId, i))
        # 還原成Json Object
        resp3_6 = json.loads(r.text)

        # 判斷3-6的參數有沒有新增到資料庫
        if resp3_6["status_code"] != 200:
            return make_response(resp3_6)

        # 開始3-3
        resp3_3 = mycard_checkMyCardTradeResult_webserver(i)

        # 判斷3-3的"status_code"
        if resp3_3["status_code"] != 200:
            return make_response(resp3_3)

        # 開始3-4
        AuthCode = resp3_3["AuthCode"]
        SandBoxMode = resp3_3["SandBoxMode"]
        Amount = resp3_3["Amount"]
        CustomerId = resp3_3["CustomerId"]
        TradeSeq = resp3_3["TradeSeq"]
        MyCardTradeNo = resp3_3["MyCardTradeNo"]
        FacTradeSeq = resp3_3["FacTradeSeq"]
        Currency = resp3_3["Currency"]
        PaymentType = resp3_3["PaymentType"]
        resp3_4 = mycard_mycardReturnInvoiceResult_webserver(AuthCode, SandBoxMode, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType)

        # 判斷3-4的"status_code"
        if resp3_4["status_code"] != 200:
            return make_response(resp3_4)
        else:
            # 正確儲值，記得可能還有下一筆
            fetch_all_3_6.append(resp3_4)

    # 最後回傳
    return make_response(fetch_all_3_6)

# 3-7 交易成功資料的差異比對，供智冠MyCard查詢
@main.route('/mcresultcheck', methods=['POST'])
def mycard_mcresultcheck_webserver():
    # 用卡片號碼或會員扣點碼查詢
    MyCardTradeNo = request.form.get("MyCardTradeNo", "")
    # 用起始時間至結束時間查詢
    StartDateTime = request.form.get("StartDateTime", "")
    EndDateTime = request.form.get("EndDateTime", "")

    # 如果智冠給的是MyCardTradeNo：單筆查詢
    if MyCardTradeNo != "":
        r = rq.get(API_SERVER_URL + 'mycard/mcresultcheck/single/?MyCardTradeNo={0}'.format(MyCardTradeNo))
        resp = json.loads(r.text)
        # 成功回傳給智冠
        return make_response(resp)

    # 如果智冠給的是StartDateTime與EndDateTime：多筆查詢
    elif StartDateTime != "" and EndDateTime != "":
        r = rq.get(API_SERVER_URL + 'mycard/mcresultcheck/multi/?StartDateTime={0}&EndDateTime={1}'.format(StartDateTime, EndDateTime))
        resp = json.loads(r.text)
        # 成功回傳給智冠：只需要回傳resp["returnMsg"]的<BR>頁面
        return make_response(resp)

    # 2種比對方法都沒有給，無法查詢
    else:
        r = {"return_msg": "3-7相關參數沒有給", "status_code": -1}
        # 失敗訊息回傳
        return make_response(r)

@main.route('/gash/wallet/base64', methods=['GET'])
def gash_wallet():
    memberid = request.args.get('memberid')
    amount = request.args.get('amount')
    itemid = request.args.get('itemid')

    # 先看memberid的log，比對玩家是否不是機器人帳號
    check_member = pg_general.is_robot_or_not("gash_wallet", memberid)
    # 確認memberid，若是機器人自動帳號，則退回玩家顯示儲值失敗
    if check_member["statuscode"] != 0:
        return make_response(check_member)

    if None not in [memberid, amount, itemid]:
        r = rq.get(API_SERVER_URL + 'web/api/get_gash_wallet_base64/?memberid={0}&amount={1}&itemid={2}'.format(memberid,amount,itemid))

        resultdata = json.loads(r.text)
    else:
        resultdata = {
            "status_code": 1
        }

    resp = make_response(resultdata)
    return resp

@main.route('/gash/point/base64', methods=['GET'])
def gash_point():
    memberid = request.args.get('memberid')
    amount = request.args.get('amount')
    itemid = request.args.get('itemid')

    # 先看memberid的log，比對玩家是否不是機器人帳號
    check_member = pg_general.is_robot_or_not("gash_point", memberid)
    # 確認memberid，若是機器人自動帳號，則退回玩家顯示儲值失敗
    if check_member["statuscode"] != 0:
        return make_response(check_member)

    if None not in [memberid,amount,itemid]:
        r = rq.get(API_SERVER_URL + 'web/api/get_gash_point_base64/?memberid={0}&amount={1}&itemid={2}'.format(memberid,amount,itemid))

        resultdata = json.loads(r.text)
    else:
        resultdata = {
            "status_code" : 1
        }

    resp = make_response(resultdata)
    return resp

@main.route('/getgashwalletitem', methods=['GET'])
def getgashwalletitem():
    r = rq.get(API_SERVER_URL + 'web/api/getgashwalletitem/')

    resultdata = json.loads(r.text)

    resp = make_response(resultdata)
    return resp

@main.route('/getgashpointitem', methods=['GET'])
def getgashpointitem():
    r = rq.get(API_SERVER_URL + 'web/api/getgashpointitem/')

    resultdata = json.loads(r.text)

    resp = make_response(resultdata)
    return resp

