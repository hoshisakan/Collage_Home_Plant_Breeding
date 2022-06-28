from flask import jsonify, request, Blueprint
import json
import traceback
from datetime import datetime
from tasks.control.mqtt_single_connection import MqttClient
from tasks.module.database_connection import DataBase as DB

relay = Blueprint('relay', __name__, url_prefix='/relay')

@relay.route('/manually/open/light', methods=['POST'])
def change_light():
    if request.method == 'POST':
        mode = request.get_json()['mode']
        response = {
            'manually_light_status': False,
            'manually_motor_status': mode,
            'auto_control_status': False
        }
        command = {'light_status': mode}
        data = json.dumps(command)
        with MqttClient('open_light') as client:
            client.publish('switch/light',data,2,False)
        return jsonify(response)

@relay.route('/manually/open/watering', methods=['POST'])
def change_watering():
    if request.method == 'POST':
        mode = request.get_json()['mode']
        response = {
            'manually_light_status': mode,
            'manually_motor_status': False,
            'auto_control_status': False
        }
        command = {'watering_status': mode}
        data = json.dumps(command)
        with MqttClient('open_watering') as client:
            client.publish('switch/watering',data,2,False)
        return jsonify(response)

@relay.route('/auto/control/switch', methods=['POST'])
def switch_auto_control():
    if request.method == 'POST':
        mode = request.get_json()['mode']
        response = {
            'manually_light_status': False,
            'manually_motor_status': False,
            'auto_control_status': mode
        }
        command = {'auto_control_switch': mode}
        data = json.dumps(command)
        with MqttClient('auto_control_switch') as client:
            client.publish('switch/auto/control',data,2,False)
        return jsonify(response)

conver_date = lambda datetime_format_date: datetime.strftime(datetime_format_date,"%Y年%m月%d日 %H時%M分%S秒")

def get_relay_status():
    with DB() as db:
        sql_command = "SELECT *	FROM Relay_Control ORDER BY switch_mode_date DESC LIMIT 1"
        db.execute(sql_command)
        data = db.fetchall()
        storage_relay_status = {}

        for read_data in data[0]:
            if read_data != 'exc_id' and read_data != 'switch_mode_date':
                storage_relay_status[read_data] = bool(data[0][read_data])
            elif read_data != 'exc_id' and read_data == 'switch_mode_date':
                conver_date_result = conver_date(data[0][read_data])
                storage_relay_status[read_data] = conver_date_result
    return storage_relay_status

@relay.route('/read/control/mode',methods=['GET'])
def update_relay_status():
    return jsonify(get_relay_status())

@relay.route('/test', methods=['GET'])
def read_realy_status():
     with DB() as db:
       sql_command = "SELECT auto_control_status FROM Relay_Control ORDER BY switch_mode_date DESC LIMIT 1"
       db.execute(sql_command)
       data = db.fetchall()
       auto_relay_status = data[0]['auto_control_status']
       collect = {}
       collect['auto_control_status'] = bool(auto_relay_status)
     return jsonify(collect)
