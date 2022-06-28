from flask import Flask
from flask_cors import CORS
import os
import sys

def GetBackPath(dirname=None):
    back_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
    full_path = os.path.join(back_path, dirname)
    print("path:", full_path)
    return full_path

def create_mqtt_app():
    mqtt_app = Flask(__name__, instance_relative_config=True,
                static_folder='..../frontend/dist/static',
                template_folder='..../frontend/dist',
                instance_path=GetBackPath('instance'))
    # TODO 告訴flask應用的名稱
    with mqtt_app.app_context():
        mqtt_app.config.from_pyfile('config.py')
        CORS(mqtt_app, resources={r"/*/*": {"origins": "*"}})
        # TODO 允許前端訪問此後端底下所有的網域，由於採取前後端分離建立一個網站，故會有存取權的問題
        # TODO 若沒有加入此行則前端會無法存取後端建立的網域

        sys.path.append("..")
        from tasks.mqtt.mqtt_loop_connection import collect
        mqtt_app.register_blueprint(collect)
    return mqtt_app
