import RPi.GPIO as GPIO
import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO
import traceback
import threading
import datetime as dt
import ssl
import os
import json
import sys
import time
sys.path.append("..")
from module.mqtt_base import MqttBase

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
motor_pin = 17
light_pin = 18
GPIO.setup(motor_pin, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.HIGH)
sensor_sub = None
sensor_pub = None
send_mode_pub = None
data_pub_count = 0
auto_control_light = True
open_auto_control = True
open_manually_light_control = False
open_manually_motor_control = False

# TODO 取得當前的時間
GetDateTimeCurrent = lambda:dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# TODO MQTT客戶端連線的類別繼承自MqttBase的父類別
class SensorMqtt(MqttBase):
    def __init__(self, client_id=None, subscribe_topics=None):
        # TODO 子類別調用父類別的初始化方法
        super().__init__(client_id, subscribe_topics)
        # TODO 子類別另外定義屬於自身的私有屬性
        self.__light_current_status = True
        self.__motor_current_status = True

    def __send_current_status(self,*args):
        dict_keys = ['auto_control','manually_light','manually_motor','swtich_date']
        current_mode = {}

        for index,key in enumerate(dict_keys,0):
            current_mode[key] = args[index]
        CurrentModePublisher(current_mode,'realy/current/mode')

    # TODO 覆寫父類別的on_message，添加其他的內容至此函式
    def on_message(self, client, userdata, message):
        try:
            global auto_control_light,open_auto_control,open_manually_light_control,open_manually_motor_control
            # global auto_control_light
            # open_auto_control = True
            # open_manually_light_control = False
            # open_manually_motor_control = False
            switch_mode_time = GetDateTimeCurrent()

            # TODO 訂閱主題之訊息
            decode_message = str(message.payload.decode("utf-8", "ignore"))
            # TODO 將json資料格式進行轉換成python的字典資料型態
            receive_data = json.loads(decode_message)
            # TODO 訂閱主題之名稱
            receive_topic = message.topic
            print('message received:{}'.format(str(receive_topic)))

            # TODO 接收後端伺服器傳來的控制指令
            if receive_topic == 'operation/command' and open_auto_control is True:
                open_manually_light_control = False
                open_manually_motor_control = False
                for key,command in receive_data.items():
                    if key == 'switch_light_state' and auto_control_light is True:
                        if command is True:
                            self.__light_current_status = GPIO.LOW
                            print("開啟自動開燈功能")
                            GPIO.output(light_pin, self.__light_current_status)
                        else:
                            self.__light_current_status = GPIO.HIGH
                            print("關閉自動開燈功能")
                            GPIO.output(light_pin, self.__light_current_status)
                        LightPublisher(self.__light_current_status)
                    else:
                        if command is True:
                            self.__motor_current_status = GPIO.LOW
                            print("啟動自動澆水功能")
                            GPIO.output(motor_pin, self.__motor_current_status)
                            time.sleep(5)
                            self.__motor_current_status = GPIO.HIGH
                            print("關閉自動澆水功能")
                            GPIO.output(motor_pin, self.__motor_current_status)
                        else:
                            self.__motor_current_status = GPIO.HIGH
                            print("關閉自動澆水功能")
                            GPIO.output(motor_pin, self.__motor_current_status)
                self.__send_current_status(
                        open_auto_control,
                        open_manually_light_control,
                        open_manually_motor_control,
                        switch_mode_time)
            # TODO 接收手動開燈與手動澆水的指令
            elif receive_topic == 'switch/light' or receive_topic == 'switch/watering':
                open_auto_control = False
                for target,command in receive_data.items():
                    if target == 'light_status':
                        if command is True:
                            self.__light_current_status = GPIO.LOW
                            GPIO.output(light_pin, self.__light_current_status)
                            print("手動開燈")
                            open_manually_light_control = True
                            open_manually_motor_control = not self.__motor_current_status
                        else:
                            self.__light_current_status = GPIO.HIGH
                            GPIO.output(light_pin, self.__light_current_status)
                            print("手動關燈")
                            open_manually_light_control = False
                            open_manually_motor_control = not self.__motor_current_status
                        LightPublisher(self.__light_current_status)
                    else:
                        if command is True:
                            self.__motor_current_status = GPIO.LOW
                            print("手動開始澆水")
                            GPIO.output(motor_pin, self.__motor_current_status)
                            time.sleep(5)
                            self.__motor_current_status = GPIO.HIGH
                            print("關閉自動澆水")
                            GPIO.output(motor_pin, self.__motor_current_status)
                        else:
                            self.__motor_current_status = GPIO.HIGH
                            print("手動停止澆水")
                            GPIO.output(motor_pin, self.__motor_current_status)
                        open_manually_light_control = False
                        open_manually_motor_control = False
                    self.__send_current_status(
                        open_auto_control,
                        open_manually_light_control,
                        open_manually_motor_control,
                        switch_mode_time)
            elif receive_topic == 'switch/auto/control':
                for mode,status in receive_data.items():
                    if status is True:
                        open_auto_control = True
                        open_manually_light_control = not self.__light_current_status
                        open_manually_motor_control = False
                        print('切換至自動控制')
                    else:
                        open_auto_control = False
                        open_manually_light_control = False
                        open_manually_motor_control = False
                        print('關閉自動控制')
                self.__send_current_status(
                        open_auto_control,
                        open_manually_light_control,
                        open_manually_motor_control,
                        switch_mode_time)
            else:
                print('Unknown topic:{}'.format(receive_topic))
        except Exception as e:
            CatchError(e)

class WriteException():
    def __init__(self, **kwargs):
        self.__storage_filename = kwargs['storage_filename']
        self.__storage_dirname = kwargs['storage_dirname']
        self.__path_exc_mode = kwargs['path_exc_mode']

    def __getFileName(self,filename=None):
        return dt.datetime.now().strftime("%Y_%m_%d_{}".format(filename))

    def __getFullPath(self,**kwargs):
       def working_directory(): return os.getcwd()
       if kwargs['mode'] is True:
         return os.path.join(kwargs['path'],kwargs['filename'])
       else:
         return os.path.join(working_directory(), kwargs['dirname'])

    def __checkPath(self,file_path=None):
        if file_path is not None:
            while not os.path.exists(file_path):
                os.makedirs(file_path)
            return file_path
        else:
            return None

    def __getWritePath(self):
      full_path = self.__checkPath(self.__getFullPath(mode=self.__path_exc_mode, dirname=self.__storage_dirname))
      file_name = self.__getFileName(self.__storage_filename)
      full_write_path = self.__getFullPath(path=full_path,filename=file_name,mode=True)
      return full_write_path

    def writeLogFile(self,**kwargs):
      if kwargs['exc_mode'] is not None and \
                   kwargs['storage_message'] is not None:
         with open(self.__getWritePath(), kwargs['exc_mode'], encoding='utf-8') as file:
           file.seek(0)
           data = file.read(100)
           if len(data) > 0:
             file.write('\n')
           file.write(kwargs['storage_message'])

# TODO 強制停止
def ForceStop():
    # global sensor_sub, sensor_pub
    global sensor_sub, sensor_pub

    # TODO 將燈光與馬達的狀態切至True即是關閉
    GPIO.output(light_pin, True)
    GPIO.output(motor_pin, True)
    # TODO 中斷與MQTT代理人的連結
    sensor_sub.Disconnect()
    sensor_pub.Disconnect()
    os._exit(0)

def HandleAbnormal(abnormal=None):
    if abnormal is not None:
        abnormal_message = {}
        temp_message = ''

        for key, value in abnormal.items():
            if value is None or value == 0:
                temp_message = value
                abnormal_message[key] = temp_message
                if key == 'brightness':
                  GPIO.output(light_pin, True)
                elif key == 'soil' or key == 'water_level':
                  GPIO.output(motor_pin, True)
        abnormal_message['date'] = abnormal['date']
        error_message = '異常訊息:\n{}'.format(abnormal_message)
        StorageExecuteMessage(True,error_message)

# TODO 印出詳細的錯誤訊息
def CatchError(exp_object=None):
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
    # print('例外訊息:',errMsg)
    StorageExecuteMessage(True,errMsg)

def StorageExecuteMessage(exc_mode=None,msg=None):
  temp_dirname = None
  temp_filename = None

  if exc_mode is True:
    temp_dirname = 'error'
    temp_filename = 'error.txt'
  else:
    temp_dirname = 'access'
    temp_filename = 'access.txt'

  WE = WriteException(
      storage_dirname=temp_dirname,
      path_exc_mode=False,
      storage_filename=temp_filename)
  WE.writeLogFile(
      exc_mode='a+',
      storage_message=msg)

def CurrentModePublisher(send_data=None,send_topic=None):
  if send_data is not None and send_topic is not None:
    global send_mode_pub
    try:
      # TODO 客戶ID
      client_id = 'sensor_relay_mode_switch'
      # TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
      subscribe_topics = None
      # TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
      send_mode_pub = SensorMqtt(client_id, subscribe_topics)
      # TODO 開始連線推送資料
      send_mode_pub.Connect(True)

    #   print('轉換前:{}'.format(send_data))
      convertion_json = json.dumps(send_data)

      send_result = send_mode_pub.Publish(
        pub_topic=send_topic,
        pub_message=convertion_json,
        pub_qos=2,
        pub_retain=False
      )
      if send_result is True:
        # print('成功推送當前控制模式!')
        pass
      send_mode_pub.Disconnect()
    except Exception as e:
      CatchError(e)

def DataSubscriber():
    global sensor_sub
    try:
        # TODO 客戶ID
        client_id = 'sensor_data_client_demo_sub'
        # TODO 訂閱主題
        subscribe_topics = [('switch/light', 2),('switch/watering', 2),
                            ('operation/command', 2),('switch/auto/control', 2)]
        # TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
        sensor_sub = SensorMqtt(client_id, subscribe_topics)
        # TODO 開始連線，訂閱以上的主題
        sensor_sub.Connect(False)
    except Exception as e:
        CatchError(e)

def LightData(light_sta):
    light = mcp.read_adc(0)
    convertResult = ConvertPercent(brightness=light)
    light_status = not light_sta

    data = {
        "brightness": convertResult,
        "status": light_status
    }
    if light == 0:
        HandleAbnormal(data)
        return False
    else:
        # TODO 轉換至Json格式以供資料推送
        print("數據:\n{}".format(str(data)))
        convertion_json = json.dumps(data)
        return convertion_json

def LightPublisher(light_sta):
    # TODO 客戶ID
    light_pub=None
    client_id = 'light_light_sta'
    # TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
    subscribe_topics = None
    # TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
    light_pub = SensorMqtt(client_id, subscribe_topics)
    # TODO 開始連線推送資料
    light_pub.Connect(True)

    message_data = LightData(light_sta)

            # TODO 判斷是否接收到轉換後的JSON數據
    if message_data is not False:
                # TODO 推送資料至指定主題
        send_result = light_pub.Publish(
        pub_topic='receive/sensor/light/status',
        pub_message=message_data,
        pub_qos=2,
        pub_retain=False
    )
                # TODO 若傳輸成功則會接收到True
    if send_result is True:
        print("{} 傳送成功".format(
        str(GetDateTimeCurrent())))
    light_pub.Disconnect()

def ConvertPercent(**kwargs):
    sensorUpper = 1023
    sensorLower = 0
    tempList = []

    for key, value in kwargs.items():
        tempSensorValue = abs(value - sensorUpper)
        percentage = int(float((tempSensorValue - sensorLower) * 100) / (sensorUpper - sensorLower))
        tempList.append(percentage)
    return tempList

def CollectSensorData():
    # TODO 接收環境的溫溼度的值
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
    # TODO 接收環境亮度的值
    light = mcp.read_adc(0)
    # TODO 接收土壤濕度的值
    soil = mcp.read_adc(1)
    # TODO 接收水位深度的值
    water_level = mcp.read_adc(2)
    # TODO 接收當前的時間
    date = GetDateTimeCurrent()

    resultCovertList = ConvertPercent(
        brightness=light,
        soil=soil,
        water_level=water_level
    )
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "brightness": resultCovertList[0],
        "soil": resultCovertList[1],
        "water_level": resultCovertList[2],
        "date": date
    }

    print('轉換結果:{}'.format(data))

    if humidity is None or temperature is None:
        HandleAbnormal(data)
        return None
    elif soil == 0 or light == 0 or water_level == 0:
        HandleAbnormal(data)
        return False
    else:
        # TODO 轉換至Json格式以供資料推送
        print("感測器數據:\n{}".format(str(data)))
        convertion_json = json.dumps(data)
        return convertion_json

def DataPublisher():
    global sensor_pub, data_pub_count
    try:
        # TODO 客戶ID
        client_id = 'sensor_data_client_demo_pub'
        # TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
        subscribe_topics = None
        # TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
        sensor_pub = SensorMqtt(client_id, subscribe_topics)
        # TODO 開始連線推送資料
        sensor_pub.Connect(True)

        # TODO 確認連線後會開始傳送數據至指定主題
        while True:
            # TODO 獲取感測器轉換後的JSON資料
            message_data = CollectSensorData()

            # TODO 判斷是否接收到轉換後的JSON數據
            if message_data is not None and message_data is not False:
                # TODO 推送資料至指定主題
                send_result = sensor_pub.Publish(
                    pub_topic='env/plant/detection/data',
                    pub_message=message_data,
                    pub_qos=2,
                    pub_retain=False
                )
                # TODO 若傳輸成功則會接收到True
                if send_result is True:
                    data_pub_count += 1
                    print("{} 傳送成功第 {} 筆資料".format(
                        str(GetDateTimeCurrent()), str(data_pub_count)))
                    message = "偵測數據:{}\n{} 傳送成功第 {} 筆資料".format(str(message_data),str(GetDateTimeCurrent()), str(data_pub_count))
                    StorageExecuteMessage(False,message)
                else:
                    message = "Invalid publish data is {}. . .\nPublish data failed. . .".format(message_data)
                    StorageExecuteMessage(True,message)
            else:
                message = "Invalid publish data is {}. . .".format(message_data)
                StorageExecuteMessage(True,message)
            # TODO 每5秒傳一次值
            time.sleep(5)
    except Exception as e:
        CatchError(e)

# TODO 初始化MQTT訂閱主題的子線程
task_sub = threading.Thread(target=DataSubscriber)
# TODO 初始化MQTT推送資料的子線程
task_pub = threading.Thread(target=DataPublisher)

# TODO 若此程式是直接執行，而非以模組方式被執行時，則會執行以下程式
if __name__ == '__main__':
    try:
        task_sub.start()
        # TODO 執行MQTT訂閱主題的子線程
        task_pub.start()
        # TODO 執行MQTT推送資料的子線程
        task_sub.join()
        task_pub.join()
    except KeyboardInterrupt:
        ForceStop()
