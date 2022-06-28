from flask import Flask
from flask_mqtt import Mqtt
from flask_cors import CORS
import secrets
import os
import sys

def GetBackPath(dirname=None):
    back_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
    full_path = os.path.join(back_path, dirname)
    print("path:", full_path)
    return full_path

def create_app():
    app = Flask(__name__, instance_relative_config=True,
                static_folder='..../frontend/dist/static',
                template_folder='..../frontend/dist',
                instance_path=GetBackPath('instance'))
    # TODO 告訴flask應用的名稱
    with app.app_context():
        app.config.from_pyfile('config.py')
        app.config['SECRET_KEY'] = secrets.token_hex(16)
        # app.config['JWT_SECRET_KEY'] = secrets.token_hex(16)
        # app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
        CORS(app, resources={r"/*/*": {"origins": "*"}})
        # TODO 允許前端訪問此後端底下所有的網域，由於採取前後端分離建立一個網站，故會有存取權的問題
        # TODO 若沒有加入此行則前端會無法存取後端建立的網域

        sys.path.append("..")
        from tasks.mqtt.environment_detection import detection
        app.register_blueprint(detection)
        from tasks.control.switch_relay import relay
        app.register_blueprint(relay)
        from tasks.control.take_picture import take
        app.register_blueprint(take)
        from tasks.chart.analysis_data import analysis
        app.register_blueprint(analysis)
        from tasks.table.search_abnormal import search
        app.register_blueprint(search)
        from tasks.user.login import login
        app.register_blueprint(login)
        from tasks.user.register import register
        app.register_blueprint(register)
        from tasks.user.reset import reset
        app.register_blueprint(reset)
    return app
