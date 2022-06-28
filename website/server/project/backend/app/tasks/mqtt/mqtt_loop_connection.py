#TODO 引入mqtt的模組
import paho.mqtt.client as mqtt
import sys
#TODO 引入異常檢測的模組
from flask import Blueprint
#TODO 引入異常檢測的模組
import tasks.mqtt.check_abnormal_data as CAD
#TODO 引入時間的模組
from tasks.module.date import DateTime as DE
from datetime import datetime as dt
#TODO 引入資料庫連線的模組
from tasks.module.database_connection import DataBase as DB
#TODO 引入取得檔案路徑的模組
from tasks.mqtt.file import GetFileWorkingPath as GP
#TODO 返回前兩層目錄
sys.path.append("...")
#TODO 引入配置檔的內
import instance.config as cf
import traceback
import ssl
import threading
import os
import json

collect = Blueprint('collect', __name__, url_prefix='/mqtt')

webMqtt = None
#TODO 資料儲存計數
count = 0
#TODO 圖像儲存計數
save_image_count = 0
#TODO 資料更新計數
update_count_ = 0
#TODO 健康度資料更新計數
update_count = 0
#TODO 健康度資料儲存計數
save_health_data_count = 0
save_switch_mode_data_count = 0

class HandleData():
    #TODO 例外處理
    def __HandleError(self,exp_object=None):
        error_class = exp_object.__class__.__name__
        # TODO 例外類型
        detail = exp_object.args[0]
        # TODO 引發例外原因
        cl, exc, tb = sys.exc_info()
        lastCallStack = traceback.extract_tb(tb)[-1]
        fileName = lastCallStack[0]
        lineNumber = lastCallStack[1]
        funcName = lastCallStack[2]
        errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(
            fileName, lineNumber, funcName, error_class, detail)
        print('例外訊息：{}'.format(errMsg))

    #TODO 寫入數據到資料庫中
    @staticmethod
    def insertion_data(save_data=None):
        global count
        with DB() as db:
            sql_command = "INSERT INTO Sensor_data(d_dht11_t,d_dht11_h,d_light,d_soil,d_water_level,d_created_date) \
                        VALUES(%s,%s,%s,%s,%s,'%s')" % (save_data['temperature'], save_data['humidity'], save_data['brightness'],
                                                        save_data['soil'], save_data['water_level'], save_data['date'])
            db.execute(sql_command)
            print(DE.GetDateTime(), "成功儲存第", count + 1, "筆資料")
            count += 1

    # TODO 更新數據到資料庫中
    @staticmethod
    def update_data(data_id, latest_data):
        global update_count
        with DB() as db:
            sql_command = "UPDATE Sensor_data SET d_dht11_t = %s,d_dht11_h = %s,d_light = %s,d_soil = %s,d_water_level = %s,d_created_date = '%s' WHERE d_id = %s" % (
                latest_data['temperature'], latest_data['humidity'], latest_data['brightness'],latest_data['soil'], latest_data['water_level'],latest_data['date'],data_id)
            exc_code = db.execute(sql_command)
            print(DE.GetDateTime(), "成功更新第", update_count + 1, "筆資料")
            update_count += 1
        return exc_code

    @staticmethod
    def split_seconds(data_datatime=None):
        if data_datatime is not None:
          get_current_datetime = str(data_datatime)
          rsplit_string = get_current_datetime.rsplit(":", 1)
          #TODO 從右邊開始計算，以第一個冒號為分隔的界線，將其進行分割
          #TODO 取出日期與時間中的時跟分，秒則捨棄
          return rsplit_string[0]
          #TODO rsplit_string[1]即是被捨棄的秒
        return None

    # TODO 比對儲存感測器的資料表與接收數據的日期時間，若相同則不會儲存資料；反之，將資料儲存到資料庫中
    @classmethod
    def check_data_repeatability_modify(cls, check_data=None):
        with DB() as db:
            sql_command = "SELECT d_id,d_created_date FROM Sensor_data ORDER BY d_created_date"
            # TODO 從Sensor_data取出最新的一筆資料(先以ORDERY BY進行倒排，再以LIMIT限制資料筆數)
            db.execute(sql_command)
            data = db.fetchall()

            for read in data:
                # TODO 類方法可以藉由cls去調用自身類別的方法(包括私有方法)
                # TODO 將資料庫與接收數據的日期和時間藉由以下函式將時分秒轉換成時分進行比對
                if cls.split_seconds(read['d_created_date']) == cls.split_seconds(check_data['date']):
                    cls.update_data(read['d_id'], check_data)
                    return True
            return False

    # TODO 更新數據到資料庫中
    @staticmethod
    def update_data_for_health(data_id, latest_data):
        global update_count_
        print('測試:',latest_data)
        with DB() as db:
            sql_command = "UPDATE Growing_data SET health_status = %s,data_created_date = '%s' WHERE data_id = %s" % (
                int(latest_data['health_status']),latest_data['created_date'],data_id)
            exc_code = db.execute(sql_command)
            print(DE.GetDateTime(), "成功更新第", update_count_ + 1, "筆資料")
            update_count_ += 1
        return exc_code

    # TODO 比對健康度的資料表與接收數據的日期時間，若相同則不會儲存資料；反之，將資料儲存到資料庫中
    @classmethod
    def check_data_repeatability_for_health(cls, check_data=None):
        with DB() as db:
            sql_command = "SELECT data_id,data_created_date FROM Growing_data ORDER BY data_created_date"
            # TODO 從Growing_data取出最新的一筆資料(先以ORDERY BY進行倒排，再以LIMIT限制資料筆數)
            db.execute(sql_command)
            data = db.fetchall()

            for read in data:
                # TODO 類方法可以藉由cls去調用自身類別的方法(包括私有方法)
                # TODO 將資料庫與接收數據的日期和時間藉由以下函式將時分秒轉換成時分進行比對
                if cls.split_seconds(read['data_created_date']) == cls.split_seconds(check_data['created_date']):
                    print(True)
                    cls.update_data_for_health(read['data_id'], check_data)
                    return True
            print(False)
            return False

    #TODO 將接收到的圖像儲存至指定的目錄下，若成功儲存，則將訊息透過MQTT的管道回傳至負責監控的樹莓派中
    #TODO 反之，則回傳失敗的訊息至負責監控的樹莓派中
    @staticmethod
    def save_image(save_path=None,rec_image=None,rec_topic=None):
        global save_image_count
        temp_msg = ""
        send_msg = {}
        dict_keys = ['monitor','anatomy']
        #TODO 以二進制方式寫入檔案
        with open(save_path, 'wb') as handle:
            handle.write(rec_image)
            #TODO 若原圖或辯識圖像儲存成功
            if os.path.isfile(save_path):
                save_image_count += 1
                print("第{}張圖像儲存成功!".format(str(save_image_count)))
                #TODO 賦予暫存回覆訊息的變數為Yes
                temp_msg = 'Yes'
                #TODO 若是原圖儲存成功
                if rec_topic == 'response/monitor/message':
                    #TODO 取dict_keys索引0作為回覆訊息的鍵
                    send_msg[dict_keys[0]] = temp_msg
                #TODO 若是辨識圖像儲存成功
                else:
                    #TODO 取dict_keys索引1作為回覆訊息的鍵
                    send_msg[dict_keys[1]] = temp_msg
            else:
                print("圖像儲存失敗. . .")
                #TODO 賦予暫存回覆訊息的變數為No
                temp_msg = "No"
                #TODO 若是原圖儲存失敗
                if rec_topic == 'response/monitor/message':
                    #TODO 取dict_keys索引0作為回覆訊息的鍵
                    send_msg[dict_keys[0]] = temp_msg
                #TODO 若是辨識圖像儲存失敗
                else:
                    #TODO 取dict_keys索引1作為回覆訊息的鍵
                    send_msg[dict_keys[1]] = temp_msg
        #TODO 返回訊息
        return send_msg

    #TODO 儲存健康度與辨識的時間
    @classmethod
    def insertion_health_status_data(cls,receive_data=None):
       try:
            global save_health_data_count
            with DB() as db:
                sql_command = "INSERT INTO Growing_data(health_status,data_created_date) \
                                VALUES(%s,'%s')" % (int(receive_data['health_status']),receive_data['created_date'])
                db.execute(sql_command)
                print(DE.GetDateTime(), "成功儲存第", save_health_data_count + 1, "筆資料")
                save_health_data_count += 1
       except Exception as e:
            cls.__HandleError(e)

    @classmethod
    def insertion_relay_control_mode(cls,receive_data=None):
       try:
            global save_switch_mode_data_count
            print(receive_data)
            with DB() as db:
                sql_command = "INSERT INTO Relay_Control(auto_control_status,manually_light_control,manually_motor_control,switch_mode_date) \
                                VALUES(%s,%s,%s,'%s')" % (receive_data['auto_control'],receive_data['manually_light'],receive_data['manually_motor'],receive_data['swtich_date'])
                db.execute(sql_command)
                print(DE.GetDateTime(), "成功儲存第", save_switch_mode_data_count + 1, "筆資料")
                save_switch_mode_data_count += 1
       except Exception as e:
            cls.__HandleError(e)

    @staticmethod
    def read_realy_status():
        with DB() as db:
            sql_command = "SELECT auto_control_status FROM Relay_Control ORDER BY switch_mode_date DESC LIMIT 1"
            db.execute(sql_command)
            data = db.fetchall()
            auto_relay_status = data[0]['auto_control_status']
        return bool(auto_relay_status)

#TODO 此類別用於執行MQTT客戶端連線
class WebClient():
    #TODO 初始化Mqtt客戶端連線的資料
    def __init__(self,client_id='Unknown', subscribe_topics=None):
        #TODO Mqtt客戶端的連接IP address或domain name
        self.__host = cf.MQTT_BROKER_URL
        #TODO Mqtt客戶端的連接埠
        self.__port = cf.MQTT_BROKER_PORT
        #TODO Mqtt客戶端的ID名稱
        self.__client_id = client_id
        #TODO 初始化Mqtt客戶端，創建一個Mqtt的物件
        self.__client = mqtt.Client(client_id=self.__client_id, clean_session=True)
        #TODO 儲存客戶端訂閱的多個主題
        self.__subscribe_topics = subscribe_topics
        #TODO 初始化欲訂閱的主題，以接收感測器與影像辨識傳送過來的資料
        self.__client.on_connect = self.__on_connect
        #TODO 處理訂閱主題接收到的資料
        self.__client.on_message = self.__on_message

    #TODO 斷開與Mqtt代理伺服器的連線
    def __disconnect(self):
        self.__client.disconnect()
        self.__client.loop_stop()

    #TODO 開始與Mqtt代理伺服器的連接
    def start_connect(self):
        #TODO 使用帳號與密碼連接上Mqtt的代理伺服器
        self.__client.username_pw_set(cf.MQTT_USERNAME, cf.MQTT_PASSWORD)
        # self.__disconnect()
        #TODO 開始與代理伺服器的連線
        self.__client.connect(self.__host, self.__port, 60)
        #TODO Mqtt客戶端啟用安全性連線，確保資料的安全性
        self.__client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                              tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        #TODO 禁用對等驗證，無須提供證書
        self.__client.tls_insecure_set(True)

    #TODO 初始化欲訂閱的主題，以接收感測器與影像辨識傳送過來的資料
    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("client is connected.\nstatus code:{}".format(str(rc)))
            if self.__subscribe_topics is not None:
              #TODO 若不為空則訂閱指定的主題
              self.__client.subscribe(self.__subscribe_topics)
              print(self.__subscribe_topics)
            else:
              print('尚未指定訂閱的主題. . .')
        else:
            print("connection failed")

    #TODO 處理訂閱主題接收到的資料
    def __on_message(self, client, userdata, message):
        try:
            #TODO 設置變數暫存MQTT客戶端接收到的主題
            receive_topic = message.topic
            if receive_topic == 'env/plant/detection/data':
                decode_message = str(message.payload.decode("utf-8", "ignore"))
                receive_data = json.loads(decode_message)
                # TODO 如果接收的數據不為空，則執行以下程式
                if receive_data:
                    print('接收感測器數據:', receive_data)
                    check_result = HandleData.check_data_repeatability_modify(receive_data)
                    if check_result == False:
                        HandleData.insertion_data(receive_data)
                    # TODO 檢測數據是否異常，若異常則推送警報給有訂閱此網站的使用者
                    command = CAD.CollectSensorData(receive_data)
                    print('控制指令:{}'.format(command))
                    read_realy_auto_mode = HandleData.read_realy_status()
                    if read_realy_auto_mode is True:
                        self.publish_data(topic='operation/command',payload=command,qos=2,retain=False)
                    else:
                        print('現在是手動模式. . .')
                else:
                    print('無法接收到資料. . .')
            #TODO 接收影像辨識的樹莓派傳送過來的原圖
            elif receive_topic == 'immediate/monitor/image':
                #TODO 取得圖片流，資料格式為bytes
                monitor_image = message.payload
                #TODO 指定儲存路徑static + 年-月-日
                get_target_directory = lambda dirname: os.path.join(dirname,dt.strftime(dt.now(),"%Y-%m-%d"))
                #TODO 設置變數storage_dirname暫存指定的儲存路徑
                storage_dirname = get_target_directory('static/img')
                #TODO 回覆主題，若有收到圖片且儲存成功會透過此主題傳送訊息給執行影像辨識的樹莓派
                response_topic = 'response/monitor/message'
                #TODO 區隔原圖與辨識圖像的檔案，在每個檔案的結尾.png前加上image的名稱
                filename = 'image'
                #TODO 執行儲存圖片的程式
                save_result = self.__HandleImage(bytes_image=monitor_image,filename=filename,storage_dirname=storage_dirname,rec_topic=response_topic)
                #TODO 若成功儲存圖片，返回的結果是True，則在log檔印出以下訊息
                if save_result:
                    print('Image saved successfully!')
            #TODO 接收影像辨識的樹莓派傳送過來的辨識圖像
            elif receive_topic == 'immediate/anatomy/image':
                #TODO 取得圖片流，資料格式為bytes
                monitor_image = message.payload
                #TODO 指定儲存路徑static + 年-月-日
                get_target_directory = lambda dirname: os.path.join(dirname,dt.strftime(dt.now(),"%Y-%m-%d"))
                #TODO 設置變數storage_dirname暫存指定的儲存路徑
                storage_dirname = get_target_directory('static/plant_anatomy')
                response_topic = 'response/anatomy/message'
                #TODO 區隔原圖與辨識圖像的檔案，在每個檔案的結尾.png前加上anatomy的名稱
                filename = 'anatomy'
                #TODO 執行儲存圖片的程式
                save_result = self.__HandleImage(bytes_image=monitor_image,filename=filename,
                                                storage_dirname=storage_dirname,rec_topic=response_topic)
                #TODO 若成功儲存圖片，返回的結果是True，則在log檔印出以下訊息
                if save_result:
                    print('Image saved successfully!')
            #TODO 接收影像辨識的樹莓派傳送過來的植物健康度與辨識偵測的日期
            # elif receive_topic == 'immediate/plant/health':
            #     #TODO 接收植物辨識後計算的健康度與其創建日期
            #     decode_message = str(message.payload.decode("utf-8", "ignore"))
            #     #TODO JSON資料還原，由JSON至dict
            #     receive_data = json.loads(decode_message)
            #     check_result = HandleData.check_data_repeatability_for_health(receive_data['created_date'])
            #     print(receive_data)
            #     HandleData.insertion_health_status_data(receive_data)
            #     # if check_result is False:
            #     #     #TODO 儲存植物健康度與其創建日期到資料庫
            #     #     HandleData.insertion_health_status_data(receive_data)
            #     command = CAD.CollectGrowingData(receive_data['health_status'])
            #     print('control command:',command)
                        #TODO 接收影像辨識的樹莓派傳送過來的植物健康度與辨識偵測的日期
            elif receive_topic == 'immediate/plant/health':
                #TODO 接收植物辨識後計算的健康度與其創建日期
                decode_message = str(message.payload.decode("utf-8", "ignore"))
                #TODO JSON資料還原，由JSON至dict
                receive_data = json.loads(decode_message)
                print(receive_data)
                check_result = HandleData.check_data_repeatability_for_health(receive_data)
                print(check_result)
                if check_result == False:
                    #TODO 儲存植物健康度與其創建日期到資料庫
                    HandleData.insertion_health_status_data(receive_data)
                command = CAD.CollectGrowingData(receive_data['health_status'])
                print('control command:',command)
            elif receive_topic == 'realy/current/mode':
               decode_message = str(message.payload.decode("utf-8", "ignore"))
               receive_data = json.loads(decode_message)
               HandleData.insertion_relay_control_mode(receive_data)
            else:
                print("未知的主題. . . ")
        except FileExistsError as fer:
            self.__HandleError(fer)
        except Exception as e:
            self.__HandleError(e)

    #TODO 儲存圖片至本地
    def __HandleImage(self,**kwargs):
        #TODO 若是任一參數為None則返回False
        if kwargs['bytes_image'] is None or kwargs['storage_dirname'] is None or kwargs['rec_topic'] is None:
            return False
        #TODO 將指定路徑與當前路徑結合，當作儲存圖片的路徑
        check_storage_directory = GP.GetFullPath(dirname=kwargs['storage_dirname'],mode=False)
        #TODO 檢查該儲存路徑是否存在和其是否為一個目錄
        if not os.path.exists(check_storage_directory) and not os.path.isdir(check_storage_directory):
            #TODO 不存在則創建一個目錄
            os.makedirs(check_storage_directory)
        #TODO 將檔案名稱與目錄名稱，以及附檔名結合，構成一個完整的圖片儲存路徑
        write_image_path = GP.GetFullPath(filename='{}_{}.png'.format(DE.GetDateTime(),kwargs['filename']),dirname='{}'.format(kwargs['storage_dirname']),mode=True)
        #TODO 若圖片存在則不會儲存
        if os.path.isfile(write_image_path):
          raise FileExistsError("檔案已經存在. . .")
        #TODO 則會儲存圖片
        else:
          #TODO 將bytes圖片流經由HandleData類別的save_image函式進行轉換儲存成二進制的圖片
          msg = HandleData.save_image(write_image_path,kwargs['bytes_image'],kwargs['rec_topic'])
          #TODO 儲存成功則透過Mqtt的主題發送回覆給影像辨識的樹莓派
          self.publish_data(topic=kwargs['rec_topic'],payload=msg,qos=2,retain=False)
          return True

    #TODO 例外處理
    def __HandleError(self,exp_object=None):
        error_class = exp_object.__class__.__name__
        # TODO 例外類型
        detail = exp_object.args[0]
        # TODO 引發例外原因
        cl, exc, tb = sys.exc_info()
        lastCallStack = traceback.extract_tb(tb)[-1]
        fileName = lastCallStack[0]
        lineNumber = lastCallStack[1]
        funcName = lastCallStack[2]
        errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(
            fileName, lineNumber, funcName, error_class, detail)
        print(errMsg)

    #TODO 維持Mqtt客戶端永久的連線
    def start_loop(self, timeout=None):
        #TODO 啟動線程讓mqtt客戶端以非阻塞方式連接
        thread = threading.Thread(target=self.__loop, args=(timeout,))
        thread.start()

    def __loop(self, timeout=None):
        if not timeout:
            #TODO 以非阻塞方式連接
            self.__client.loop_forever()
        else:
            self.__client.loop(timeout)

    #TODO 以指定的主題推送資料
    def publish_data(self, **kwargs):
        if kwargs['topic'] is None and kwargs['payload'] is None:
            return False
        if type(kwargs['payload']) == dict:
            print('推送主題:{}'.format(kwargs['topic']))
            print('推送訊息:{}'.format(kwargs['payload']))
            control_command = json.dumps(kwargs['payload'])
            #TODO 以指定的主題推送資料
            self.__client.publish(kwargs['topic'], control_command, kwargs['qos'], kwargs['retain'])
            print("'Publish successful!'")
        return True

if __name__ != '__main__':
    #TODO 客戶端的連接ID
    client_id = 'webMqtt'
    #TODO 客戶端欲訂閱主題
    subscribe_topics = [('immediate/monitor/image',2),
                        ('env/plant/detection/data',2),
                        ('immediate/anatomy/image',2),
                        ('immediate/plant/health',2),
                        ('realy/current/mode',2)]
    #TODO 初始化類別生成一個物件
    webMqtt = WebClient(client_id, subscribe_topics)
    #TODO 以物件呼叫其函式進行連線
    webMqtt.start_connect()
    #TODO 維持永久的連線，直到客戶端自行斷開連線
    webMqtt.start_loop()
