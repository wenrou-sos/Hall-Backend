from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify,send_from_directory,current_app as app,make_response
from flask_login import login_required, current_user
from . import main,API_SERVER_URL
import datetime
import requests as rq
import json




@main.route('/addComment',methods=['POST'])
def addComment():
    conent = request.form.get('CommentContent')
    typeid = request.form.get('CommentTypeId')
    memberid = request.form.get('memberid')
    params = {
        "content": conent,
        "typeid": typeid,
        "memberid": memberid
    }
    r = rq.get(
        API_SERVER_URL + 'web/api/add_comment/', params=params)

    resultdata = json.loads(r.text)


    resp = make_response(resultdata)

    return resp
