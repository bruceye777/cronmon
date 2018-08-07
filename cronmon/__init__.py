import logging
import os
from logging.config import fileConfig
from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from cronmon.conf.config import config


login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'auth.login'
login_manager.login_message = u""
fileConfig('cronmon/conf/log.conf')
mail = Mail()
moment = Moment()
scheduler = APScheduler()


def get_logger(name):
    """日志对象初始化"""
    return logging.getLogger(name)


def get_config():
    """获取业务配置"""
    return config[os.getenv('FLASK_CONFIG') or 'default']


def create_app(config_name):
    """app初始化，配置读取以及蓝点注册"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    mail.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    from .api.api_1_0 import api_1_0 as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app
