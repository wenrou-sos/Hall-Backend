from flask import Flask
from flask_login import LoginManager,UserMixin
from conf.config import config
import logging

import os
import env_setting

import pg_general

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'main.root'


class User(UserMixin):
    pass



def get_basedir():
    return os.path.abspath(os.path.dirname(__file__))


def get_config():
    return config[os.getenv('FLASK_CONFIG') or 'default']


def create_app(config_name):
    app = Flask(__name__,static_folder='../assets')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app


