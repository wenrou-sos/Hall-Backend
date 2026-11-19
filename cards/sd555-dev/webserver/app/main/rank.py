from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify,send_from_directory,current_app as app
from flask_login import login_required, current_user
from . import main,API_SERVER_URL
import datetime
import requests as rq
import json


@main.route('/getrichestrank',methods=['GET'])
def getrichestrank():

    r = rq.get(API_SERVER_URL + 'web/api/getrichestrank/')

    rankdata = r.json()

    rankdata = {"rankInfoList": rankdata}

    return jsonify(rankdata)


@main.route('/rankdata/<path:filename>')
def rankdata(filename):
    try:
        with open('D:\\coding\\jinsongwebserver\\rankdata\\' + filename,encoding='utf-8') as json_file:
            data = json.load(json_file)
        return jsonify(data)
    except:
        return "404",404