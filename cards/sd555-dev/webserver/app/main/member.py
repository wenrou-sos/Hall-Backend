from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify
from flask_login import login_required, current_user
from . import main
import datetime
import requests as rq
import json
from app import login_manager


cfg = get_config()

@login_manager.user_loader
def load_user(user_id):
    print("user_loader " + user_id)
    return "0"

@main.route('/getmemberinfo',methods=['GET'])
def getmemberinfo():

    return "0"













