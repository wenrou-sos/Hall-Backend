from app import get_config
from flask import render_template, redirect, url_for, flash, request,jsonify
from flask_login import login_required, current_user
from . import main
import datetime
import requests as rq
import json
from user_agents import parse

# 根目錄
@main.route('/', methods=['GET'])
# @login_required
def root():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('index.html', is_mobile = user_agent.is_mobile)
    # else:
    #     alert('desktop')
    #     return render_template('index.html', current_user=current_user)

@main.route('/index.html', methods=['GET'])
# @login_required
def index():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('index.html', is_mobile = user_agent.is_mobile)
    # else:
    #     alert('desktop')
    #     return render_template('index.html', current_user=current_user)



@main.route('/account.html', methods=['GET'])
# @login_required
def account():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('account.html', is_mobile = user_agent.is_mobile)
    # else:
    #     alert('desktop')
    #     return render_template('index.html', current_user=current_user)

@main.route('/customerservice.html', methods=['GET'])
# @login_required
def customerservice():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('customerservice.html', is_mobile = user_agent.is_mobile)
    # else:
    #     alert('desktop')
    #     return render_template('index.html', current_user=current_user)

@main.route('/deposit.html', methods=['GET'])
# @login_required
def deposit():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('deposit.html', is_mobile = user_agent.is_mobile)

@main.route('/introduction.html', methods=['GET'])
# @login_required
def introduction():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('introduction.html', is_mobile = user_agent.is_mobile)

@main.route('/serialnumber.html', methods=['GET'])
# @login_required
def serialnumber():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('serialnumber.html', is_mobile = user_agent.is_mobile)

@main.route('/leaderboard.html', methods=['GET'])
# @login_required
def leaderboard():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('leaderboard.html', is_mobile = user_agent.is_mobile)

@main.route('/teaching.html', methods=['GET'])
# @login_required
def teaching():
    # if request.MOBILE:
    #     alert('mobile')
    uas = request.headers.get('User-Agent')
    user_agent = parse(uas)

    return render_template('teaching.html', is_mobile = user_agent.is_mobile)

