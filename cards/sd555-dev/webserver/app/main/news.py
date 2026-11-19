from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify
from flask_login import login_required, current_user
from . import main
import datetime
import requests as rq
import json

# get news status
@main.route('/nocache/index/news_status.json',methods=['GET'])
def GetNewsJson():

    returnlist = [{"Count":"12","LastUpdate":"2019-06-20T10:14:46Z","Name":"活動","Type":"14"},{"Count":"104","LastUpdate":"2019-06-20T10:14:46Z","Name":"營運","Type":"15"},{"Count":"12","LastUpdate":"2019-06-20T10:14:46Z","Name":"客服","Type":"16"},{"Count":"128","LastUpdate":"2019-06-20T10:14:46Z","Name":"All","Type":"-1"}]
    return jsonify(returnlist)

# get news list
@main.route('/cache/index/news_list.json',methods=['GET'])
def GetNewsList():
    returnlist = [{"Id": "123","Name": "Name1","Title": "title1","CreateTime": "2019-01-01 00:00:00"}]
    return jsonify(returnlist)
