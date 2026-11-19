from app import User
from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify,make_response
from flask_login import login_required, current_user,login_user
from . import main,API_SERVER_URL
import datetime
import requests as rq
import json


@main.route('/LoginByFB', methods=['POST'])
def loginbyfb():
    fbid = request.form.get('userID')
    fbtoken = request.form.get('Token')

    # 記錄連線資訊
    user_region = request.headers.get('X-Client-Geo-Region', None)  # 抓 user region
    user_region_sub = request.headers.get('X-Client-Geo-Region-Sub', None)
    user_city = request.headers.get('X-Client-Geo-City', None)  # 抓 user city
    user_ip = request.headers.get('X-Forwarded-For', None)  # 抓 user ip
    if user_ip is not None:
        user_ip = user_ip.split(',')[0]

    r = rq.get(API_SERVER_URL + 'web/api/loginfb/?fbid={0}&user_region={1}&user_region_sub={2}&user_city={3}&user_ip={4}&fbtoken={5}'.format(fbid,user_region,user_region_sub,user_city,user_ip,fbtoken))
    resultdata = json.loads(r.text)
    resp = make_response(resultdata)

    clientdata = resultdata.get('clientdata')
    if clientdata is not None:
        statuscode = clientdata.get('statuscode')

        if statuscode == 0:
            fbid = clientdata.pop('fbid')
            weblogintoken = clientdata.pop('weblogintoken')
            if weblogintoken is not None:
                resp.set_cookie("weblogintoken", weblogintoken,domain='.jinsong.io')
                resp.set_cookie("userfbid", fbid,domain='.jinsong.io')
                resp.delete_cookie('username', domain='.jinsong.io')
    return resp

@main.route('/LoginByToken',methods=['GET'])
def loginbytoken():
    cookiekeys = request.cookies.keys()
    clientToken = request.cookies.get('clientToken')
    weblogintoken = request.cookies.get('weblogintoken')
    fbid = request.cookies.get('userfbid')
    fbm = request.cookies.get('fbm_253046975639650')
    username = request.cookies.get('username')

    if None not in [clientToken,weblogintoken] and clientToken =='1':
        # 記錄連線資訊
        user_region = request.headers.get('X-Client-Geo-Region', None)  # 抓 user region
        user_region_sub = request.headers.get('X-Client-Geo-Region-Sub', None)
        user_city = request.headers.get('X-Client-Geo-City', None)  # 抓 user city
        user_ip = request.headers.get('X-Forwarded-For', None)  # 抓 user ip
        if user_ip is not None:
            user_ip = user_ip.split(',')[0]

        r = rq.get(
            API_SERVER_URL + 'web/api/loginbytoken/?fbid={0}&user_region={1}&user_region_sub={2}&user_city={3}&user_ip={4}&username={5}&weblogintoken={6}'.format(
                fbid, user_region, user_region_sub, user_city, user_ip,username,weblogintoken))


        resultdata = json.loads(r.text)
        resp = make_response(resultdata)

        clientdata = resultdata.get('clientdata')
        if clientdata is not None:
            weblogintoken = clientdata.pop('weblogintoken')
            if weblogintoken is not None:
                resp.set_cookie("weblstartPurchaseogintoken", weblogintoken,domain='.jinsong.io')



        return resp
    else:
        resultdata = {
            "apiresult": 0,
            "clientdata":{
                "statuscode": 3  # cookie 無 fbtoken , 或是過期, 要重新登入
            }
        }
        return resultdata

@main.route('/LoginByNormal',methods=['POST'])
def loginbynormal():
    username = request.form.get('username')
    password = request.form.get('password')

    # 記錄連線資訊
    user_region = request.headers.get('X-Client-Geo-Region', None)  # 抓 user region
    user_region_sub = request.headers.get('X-Client-Geo-Region-Sub', None)
    user_city = request.headers.get('X-Client-Geo-City', None)  # 抓 user city
    user_ip = request.headers.get('X-Forwarded-For', None)  # 抓 user ip
    if user_ip is not None:
        user_ip = user_ip.split(',')[0]

    r = rq.get(
        API_SERVER_URL + 'web/api/loginusername/?username={0}&user_region={1}&user_region_sub={2}&user_city={3}&user_ip={4}&password={5}'.format(
            username, user_region, user_region_sub, user_city, user_ip,password))
    resultdata = json.loads(r.text)
    resp = make_response(resultdata)

    clientdata = resultdata.get('clientdata')

    if clientdata is not None and clientdata.get('statuscode')==0:
        statuscode = clientdata.get('statuscode')
        username = clientdata.pop('username')
        if statuscode == 0:
            weblogintoken = clientdata.pop('weblogintoken')
            if weblogintoken is not None:
                resp.set_cookie("weblogintoken", weblogintoken,domain='.jinsong.io')
                resp.set_cookie("userfbid", '',expires=0,domain='.jinsong.io')
                resp.set_cookie('username',username,domain='.jinsong.io')

    return resp


@main.route('/logout',methods=['GET'])
def logout():
    fbid = request.cookies.get('userfbid')
    weblogintoken = request.cookies.get('weblogintoken')
    username = request.cookies.get('username')

    r = rq.get(API_SERVER_URL + 'web/api/logout/?fbid={0}&weblogintoken={1}&username={2}'.format(fbid,weblogintoken,username))

    resultdata = json.loads(r.text)
    resp = make_response(resultdata)

    resp.delete_cookie('username',domain='.jinsong.io')
    resp.delete_cookie('userfbid',domain='.jinsong.io')
    resp.delete_cookie('clientToken',domain='.jinsong.io')
    resp.delete_cookie('weblogintoken',domain='.jinsong.io')

    return resp
