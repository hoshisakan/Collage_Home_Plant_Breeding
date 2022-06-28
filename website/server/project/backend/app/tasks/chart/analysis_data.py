from flask import jsonify, request, Blueprint
import json
import threading
import sys
import os
import traceback
import requests
from tasks.module.database_connection import DataBase as DB

analysis = Blueprint('analysis', __name__, url_prefix='/chart')

#TODO 用於生成二維陣列
def DataList(array_size=None):
    if array_size is None:
        return []
    else:
        return [[] for x in range(array_size)]

#TODO 取小時與分鐘，將秒捨棄
#TODO 12:56:02(從右邊數來第一個冒號作為分割點)
def split_seconds(data_datatime=None):
    if data_datatime is not None:
        get_current_datetime = str(data_datatime)
        rsplit_string = get_current_datetime.rsplit(":", 1)
        # TODO 從右邊開始計算，以第一個冒號為分隔的界線，將其進行分割
        # TODO 取出日期與時間中的時跟分，秒則捨棄
        return rsplit_string[0]
        # TODO rsplit_string[1]即是被捨棄的秒
    return None

#TODO 取得所有的資料
def get_all_chart_data(**kwargs):
  with DB() as db:
    #TODO 資料儲存索引
    index = 0
    #TODO 取得前N筆最新的感測器偵測之資料
    sql_command = "SELECT * FROM Sensor_data ORDER BY d_created_date DESC LIMIT \
                        {}".format(kwargs['data_limit'])
    #TODO 執行SQL指令
    db.execute(sql_command)
    #TODO 將從資料庫取得的資料暫存至temp_env_data
    temp_env_data = db.fetchall()
    #TODO 取得前N筆最新的植物生長之資料
    sql_command = "SELECT * FROM Growing_data ORDER BY data_created_date DESC LIMIT \
                        {}".format(kwargs['data_limit'])
    #TODO 執行SQL指令
    db.execute(sql_command)
    #TODO 將從資料庫取得的資料暫存至temp_env_data
    temp_health_data = db.fetchall()
    #TODO 依據指定的數量生成一個二維的列表，用以儲存環境偵測與植物生長之資料
    temp_chart_data = DataList(kwargs['data_limit'])

    #TODO 同時迭代兩個列表的資料，並將其儲存至二維列表中
    for sensor,growing in zip(temp_env_data,temp_health_data):
      sensorDectectionDate = split_seconds(str(sensor['d_created_date']))
      # growingDectectionDate = split_seconds(str(growing['data_created_date']))
      #TODO 將資料附加至當前索引列表的末端
      temp_chart_data[index].append(sensorDectectionDate)
      temp_chart_data[index].append(int(sensor['d_light']))
      temp_chart_data[index].append(int(sensor['d_soil']))
      temp_chart_data[index].append(int(sensor['d_water_level']))
      temp_chart_data[index].append(int(growing['health_status']))
      # if sensorDectectionDate == growingDectectionDate:
      #   temp_chart_data[index].append(int(growing['health_status']))
      # else:
      #   temp_chart_data[index].append(0)
      index += 1
    #TODO 插入資料至二維列表的開頭
    temp_chart_data.insert(0, kwargs['chart_options'])
    #TODO 轉換至JSON格式後回傳資料
    return jsonify(temp_chart_data)

# TODO 讀取感測器偵測與植物生長之資料，取其前N筆最新的資料並以JSON格式返回前台供圖表使用
@analysis.route('/data/average', methods=['POST'])
def read_env_average_data():
    chart_options = ['偵測時間', '環境亮度', '土壤濕度', '剩餘水量','植物健康狀態']
    if request.method == 'POST':
        data_limit = int(request.get_json()['data_limit'])

        if data_limit > 0:
            return get_all_chart_data(
                chart_options=chart_options,
                data_limit=data_limit)
        return get_all_chart_data(
            chart_options=chart_options,
            data_limit=10)
