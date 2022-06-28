#TODO 從flask套件中引入Flask, jsonify, request, Blueprint的模組
from flask import jsonify,request,Blueprint
import json
import sys
import os
import traceback
#TODO 引入時間的模組
from datetime import datetime
#TODO 引入資料庫連線的模組
from tasks.module.database_connection import DataBase as DB

search = Blueprint('search', __name__, url_prefix='/abnormal')

#TODO 二維列表生成器
def DataList(array_size=None):
    if array_size is None:
        return []
    else:
        return [[] for x in range(array_size)]

#TODO 轉換資料庫dateime的日期格式
conver_date = lambda datetime_format_date: datetime.strftime(datetime_format_date,"%Y/%m/%d %H:%M:%S")

#TODO 搜尋資料庫中異常的環境之數據
def SearchErrorData(data_limit):
    with DB() as db:
        sql_command = "SELECT d_dht11_t,d_dht11_h,d_light,d_soil,d_water_level,d_created_date FROM Sensor_data WHERE d_dht11_t = 0 or d_dht11_h = 0 or d_light = 0 \
                        or d_soil = 0 or d_water_level = 0 ORDER BY d_created_date DESC LIMIT {}".format(data_limit)
        db.execute(sql_command)
        data = db.fetchall()
        #TODO 搜尋日期的資料
        for index,read_data in enumerate(data,0):
          for key,value in read_data.items():
            #TODO 若搜尋到日期的資料
            if key == 'd_created_date':
              #TODO 轉換日期格式
              conver_date_result = conver_date(value)
              #TODO 取代原本的日期格式
              data[index][key] = conver_date_result
    return jsonify(data)

#TODO 返回指定數量的資料
@search.route('/data/table', methods=['GET','POST'])
def read_abnormal_data():
    if request.method == 'POST':
        data_limit = int(request.get_json()['data_limit'])
        if data_limit > 0:
            return SearchErrorData(data_limit)
        else:
            return SearchErrorData(5)
    else:
        return SearchErrorData(5)
