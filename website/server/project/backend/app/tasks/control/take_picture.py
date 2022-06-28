from flask import jsonify, request, Blueprint
import json
import traceback
from datetime import datetime
from tasks.control.mqtt_single_connection import MqttClient

take = Blueprint('take', __name__, url_prefix='/manually')

@take.route('/take/picture', methods=['GET'])
def manually_take_picture():
  mode = True
  response = {
     'manually_take_picture': mode,
  }
  command = {'manually_take_picture': mode}
  data = json.dumps(command)
  with MqttClient('take_picture') as client:
    client.publish('manually/take/picture',data,2,False)
  print('拍照否?',command)
  return jsonify(response)
