from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify
from flask_login import login_required, current_user
from . import main, API_SERVER_URL
import datetime
import requests as rq
import json
import pg_general

@main.route('/GetServerStatus',methods=['GET'])
def GetServerStatus():
    r = rq.get(API_SERVER_URL + 'web/api/getserverstatus/')
    status = r.json()

    return status


@main.route('/serialinput', methods=['GET'])
def serialinput():
    memberid = request.args.get('memberid')
    serial = request.args.get('serial')
    webtoken = request.cookies.get('clientToken')
    weblogintoken = request.cookies.get('weblogintoken')

    # 先看memberid的log，比對玩家是否不是機器人帳號
    check_member = pg_general.is_robot_or_not("serialinput", memberid)
    pg_general.writelog(pg_general.PG_LogerLevel.error,
                        'utility.py/serialinput:serialinput memberid:{0},webtoken:{1} , serial:{2} , weblogintoken:{3}, check_member:{4}'.format(
                            memberid, webtoken, serial, weblogintoken,check_member))

    # 確認memberid，若是機器人自動帳號，則退回玩家顯示儲值失敗
    if check_member["statuscode"] != 0:
        return check_member

    if None not in [memberid,serial,webtoken] and webtoken =='1':
        r = rq.get(API_SERVER_URL + 'web/api/serialinput/?memberid={}&serial={}&logintoken={}'.format(memberid,serial,weblogintoken))
        resultdata = r.json()
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'None not in [memberid,serial,webtoken] and webtoken resultdata:serialinput resultdata:{0}'.format(resultdata))

    else:
        resultdata = {
            "status_code": 1,
            "msg": "序號輸入錯誤, 請重新輸入 !!"
        }
        pg_general.writelog(pg_general.PG_LogerLevel.error,'else resultdata:serialinput resultdata:{0}'.format(resultdata))


    return resultdata



@main.route('/healthycheck',methods=['GET'])
def healthycheck():
    return 'check'


@main.route('/setting/<path:filename>')
def setting(filename):

    try:

        if filename.split('.')[1]=='json':
            with open('D:\\coding\\jinsongwebserver\\setting\\' + filename,encoding='utf-8') as json_file:
                data = json.load(json_file)
            return jsonify(data)
        elif filename.split('.')[1]=='html':
            with open('D:\\coding\\jinsongwebserver\\setting\\' + filename, encoding='utf-8') as html_file:
                data = html_file.read()
            return data
    except Exception as e:

        return "404",404