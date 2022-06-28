import traceback
import ssl
import threading
import os
import json
import sys
import paho.mqtt.client as mqtt
sys.path.append("...")
import instance.config as cf

class MqttClient(object):
  def __init__(self, id='Unknown'):
    #TODO Mqtt客戶端的連接IP address或domain name
    self.__host = cf.MQTT_BROKER_URL
    #TODO Mqtt客戶端的連接埠
    self.__port = cf.MQTT_BROKER_PORT
     #TODO Mqtt客戶端的ID名稱
    self.__id = id
    #TODO 初始化Mqtt客戶端，創建一個Mqtt的物件
    self.__client = mqtt.Client(client_id=self.__id, clean_session=True)
    #TODO 初始化欲訂閱的主題，以接收感測器與影像辨識傳送過來的資料
    # self.__subscribe_topics = [('change/response',1)]
    self.__subscribe_topics = None
    #TODO 呼叫連接的私有方法
    self.__start_connect()

  def __start_connect(self):
    #TODO 使用帳號與密碼連接上Mqtt的代理伺服器
    self.__client.username_pw_set(cf.MQTT_USERNAME, cf.MQTT_PASSWORD)
    #TODO Mqtt客戶端啟用安全性連線，確保資料的安全性
    self.__client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                          tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    #TODO 禁用對等驗證，無須提供證書
    self.__client.tls_insecure_set(True)
    #TODO 開始與代理伺服器的連線
    self.__client.connect(self.__host, self.__port, 60)
    #TODO 初始化欲訂閱的主題
    self.__client.on_connect = self.__on_connect
    #TODO 接收訂閱主題的訊息
    self.__client.on_message = self.__on_message
    #TODO 中斷先前的連線
    # self.__client.on_disconnect = self.__on_disconnect
    #TODO 開始連接
    self.__client.loop_start()

  def HandleError(self,exp_object=None):
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
        os._exit(0)

  def __on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      print("client is connected.\nstatus code:{}".format(str(rc)))
      self.__client.subscribe(self.__subscribe_topics)
      print(self.__subscribe_topics)
    else:
      print("connection failed")

  #TODO 處理訂閱主題接收到的資料
  def __on_message(self, client, userdata, message):
    try:
        decode_message = str(message.payload.decode("utf-8", "ignore"))
        receive_data = json.loads(decode_message)
        print(receive_data)
    except Exception as e:
      self.HandleError(e)

  # def __on_disconnect(self, client, userdata, rc):
  #   if rc != 0:
  #     print('disconnect from mqtt client. . .')

  #TODO 返回mqtt物件
  def __enter__(self):
    return self.__client

  #TODO 執行完後自動關閉連線
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.__client.loop_stop()
    self.__client.disconnect()
    print('關閉連線. . .')
