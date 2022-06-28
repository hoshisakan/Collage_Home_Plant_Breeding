#TODO 從flask套件中引入Flask, jsonify, request, Blueprint的模組
import glob
from xmlrpc.client import boolean
from flask import jsonify, request, Blueprint
#TODO 引入json模組
import json
import threading
import sys
import os
import traceback
import base64
#TODO 引入時間的模組
import time
from datetime import datetime,timedelta
#TODO 引入異常檢測的模組
import tasks.mqtt.check_abnormal_data as CAD
#TODO 引入資料庫連線的模組
from tasks.module.database_connection import DataBase as DB
#TODO 引入取得檔案路徑的模組
from tasks.mqtt.file import GetFileWorkingPath as GP

#TODO 初始化與定義藍圖
detection = Blueprint('detection', __name__, url_prefix='/env')

#TODO 轉換資料庫dateime的日期格式
conver_date = lambda datetime_format_date: datetime.strftime(datetime_format_date,"%Y年%m月%d日 %H時%M分%S秒")

#TODO 從資料庫中先抓取偵測資料後，再以JSON的資料格式將資料進行回傳
@detection.route('/data', methods=['GET'])
def read_env_data():
    #TODO 連接資料庫
    with DB() as db:
        #TODO 從Sensor_data取出最新的一筆資料(先以ORDERY BY進行倒排，再以LIMIT限制資料筆數)
        sql_command = "SELECT * FROM Sensor_data ORDER BY d_created_date DESC LIMIT 1"
        #TODO 執行SQL指令
        db.execute(sql_command)
        #TODO 讀取資料並將其儲存至data的變數中
        data = db.fetchall()
        #TODO 儲存轉換後的資料
        storage_data = {}

        for read_data in data[0]:
            #TODO 如果讀取到的資料的鍵是d_date，則會執行以下程式
            if read_data == 'd_created_date':
                #TODO 轉換資料庫dateime的日期格式
                conver_date_result = conver_date(data[0][read_data])
                #TODO 將轉換後日期儲存至storage_data的變數中，字典的鍵為read_data讀取到的鍵
                storage_data[read_data] = conver_date_result
            #TODO 反之，直接將資料儲存至storage_data的變數中
            else:
                storage_data[read_data] = data[0][read_data]
    return jsonify(storage_data)

#TODO 先從資料庫抓取健康度數值與辨識日期的資料後，再以JSON的資料格式將資料進行回傳
@detection.route('/plant/health/data', methods=['GET'])
def read_plant_health():
    #TODO 連接資料庫
    with DB() as db:
        # TODO 從Sensor_data取出最新的一筆資料(先以ORDERY BY進行倒排，再以LIMIT限制資料筆數)
        sql_command = "SELECT health_status,data_created_date FROM Growing_data ORDER BY data_created_date DESC LIMIT 1"
        #TODO 執行SQL指令
        db.execute(sql_command)
        #TODO 讀取資料並將其儲存至data的變數中
        data = db.fetchall()
        #TODO 儲存轉換後的資料
        storage_plant_health_data = {}

        for read_data in data[0]:
          #TODO 如果讀取到的資料的鍵是data_created_date，則會執行以下程式
          if read_data == 'data_created_date':
            #TODO 轉換資料庫dateime的日期格式
            conver_date_result = conver_date(data[0][read_data])
            #TODO 將轉換後日期儲存至storage_plant_health_data的變數中，字典的鍵為read_data讀取到的鍵
            storage_plant_health_data[read_data] = conver_date_result
          #TODO 反之，直接將資料儲存至storage_plant_health_data的變數中
          else:
            storage_plant_health_data[read_data] = data[0][read_data]
    return jsonify(storage_plant_health_data)

#TODO 取得最新創建的檔案名稱
def get_image_name(image_path=None):
    if image_path is not None:
        #TODO 列出圖像路徑的所有檔案
        image_files_list = os.listdir(image_path)
        #TODO 將檔案依據最近訪問的時間進行排序
        image_files_list.sort(
            key=lambda filename: os.path.getctime(os.path.join(image_path,filename)))
        #TODO 從該列表中取出倒數第一的檔案名稱，也就是最新的檔案名稱，將其與路徑結合後回傳
        latest_filename = os.path.join(image_path, image_files_list[-1])
        print(f'filename: {latest_filename}')
        return latest_filename
    return None

def obtain_newest_dirname(img_path):
    files = os.listdir(img_path)
    # paths = [os.path.join(path, basename) for basename in files]
    # return max(paths, key=os.path.getctime)
    latest_dirname = sorted(files, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
    # return os.path.join(img_path, latest_dirname[-1])
    return os.path.join(img_path, latest_dirname[-2])

def obtain_newest_filename(latest_img_path):
    # folder = r'{}'.format(latest_img_path)
    # file_type = r'\*type'
    # print(f'search target: {folder}')
    # files = glob.glob(folder + file_type)
    # dir_files = os.listdir(latest_img_path)
    # if len(dir_files) > 0:
    #     max_file = max(files, key=os.path.getctime)
    #     print(max_file)
    # print(f'files count: {len(files)}')
    # print(f'dir_files: {dir_files}')
    return os.listdir(latest_img_path)[-1]

check_path_exists = lambda check_path: os.path.exists(check_path)

#TODO 取得圖像或圖像的最近訪問日期
def get_image_stream(img_save_dir=None,mode=None):
    #TODO 取得圖片路徑，將指定的圖片目錄與當前路徑結合
    image_path = GP.GetFullPath(dirname='static/{}'.format(img_save_dir),mode=False)
    print(f'image path: {image_path}')
    if check_path_exists(image_path):
        latest_img_dirname = obtain_newest_dirname(image_path)
        print(f'latest_img_dirname: {latest_img_dirname}')
        print(f'check path exists: {check_path_exists( latest_img_dirname)}')
        # latest_img_filename = obtain_newest_filename(latest_img_dirname)
        # print(f'latest_img_filename: {latest_img_filename}')
        # full_img_path = os.path.join(latest_img_dirname, latest_img_filename)
        if img_save_dir == 'img':
            latest_img_filename = '2020-06-12-14_59_24_image.png'
        elif img_save_dir == 'plant_anatomy':
            latest_img_filename = '2020-06-12-09_49_10_anatomy.png'
        full_img_path = os.path.join(latest_img_dirname, latest_img_filename)
        print(f"full_img_path: {full_img_path}")
        
        if check_path_exists(full_img_path):
                #TODO 則True是返回圖片
                if mode is True:
                    image_stream = ''
                    #TODO 獲取圖片
                    with open(full_img_path, 'rb') as image:
                        #TODO 讀取圖片以bytes的資料格式返回
                        image_content = image.read()
                        #TODO 再將bytes轉換成base64的資料格式
                        image_stream = base64.b64encode(image_content)
                    return image_stream
                #TODO False是返回檔案最近訪問的日期
                else:
                    #TODO 取得檔案的最近訪問日期
                    get_file_created_time = lambda path: os.path.getctime(path)
                    #TODO 暫存最新檔案的最近訪問日期
                    time_stamp = get_file_created_time(full_img_path)
                    #TODO 轉換時間格式
                    conver_date_result = datetime.fromtimestamp(time_stamp).strftime("%Y年%m月%d日 %H時%M分%S秒")
                    #TODO 回傳轉換後的日期
                    return conver_date_result
    return False

#TODO 指定今日存放圖片的目錄
get_target_directory = lambda dirname: os.path.join(dirname,datetime.strftime(datetime.now(),"%Y-%m-%d"))

#TODO 指定昨天存放圖片的目錄
get_other_directory = lambda dirname=None,days=1:os.path.join(dirname,datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%d'))

#TODO 透端該路由返回轉換過後的圖片
@detection.route('/data/image', methods=['POST'])
def read_local_image():
    # result = {}
    if request.method == 'POST':
        mode = bool(request.get_json()['mode'])
        print(f'mode: {mode}')
        if isinstance(mode, bool):
            #TODO True是返回圖片流，False是返回檔案最近訪問的日期
            response_data = get_image_stream('img',mode)
            # result['img_stream'] = response_data
            # print(result)
            return response_data



#TODO 透端該路由返回轉換過後的圖片
@detection.route('/data/image/anatomy/plant', methods=['POST'])
def read_local_anatomy_plant_image():
    # result = {}
    if request.method == 'POST':
        mode = bool(request.get_json()['mode'])
        print(f'mode: {mode}')
        if isinstance(mode, bool):
            #TODO True是返回圖片流，False是返回檔案最近訪問的日期
            response_data = get_image_stream('plant_anatomy',mode)
            # result['img_stream'] = response_data
            # print(result)
            return response_data
