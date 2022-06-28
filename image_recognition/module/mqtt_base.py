import traceback
import ssl
import os
import json
import sys
import paho.mqtt.client as mqtt
import module.config as cf

#TODO MQTT父類別，讓繼承的子類別進行功能修改
class MqttBase(object):
  #TODO 類別初始化方法
  def __init__(self,client_id=None,subscribe_topics=None):
    #TODO 宣告一個私有屬性host，儲存MQTT代理伺服器的IP
    self.__host = cf.broker_address
    #TODO 宣告一個私有屬性port，儲存MQTT代理伺服器的SSL連接埠
    self.__port = cf.connect_port
    #TODO 宣告一個私有屬性id，儲存客戶端ID
    self.__id = client_id
    #TODO 宣告一個私有屬性client，儲存初始化後的mqtt物件
    self.__client = mqtt.Client(client_id=self.__id, clean_session=True)
    #TODO 宣告一個私有屬性subscribe_topics，儲存欲訂閱的主題
    self.__subscribe_topics = subscribe_topics

  #TODO MQTT代理者連線
  def Connect(self,mode=None):
    #TODO 設置Mqtt的使用者名稱與密碼
    self.__client.username_pw_set(cf.username, cf.password)
    #TODO 設置以TLS方式連結的參數
    self.__client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                          tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    self.__client.tls_insecure_set(True)
    #TODO 連線Mqtt代理伺服器
    self.__client.connect(self.__host, self.__port, 60)
    #TODO 呼叫回調函式印出連線狀態資訊，以及以初始化的客戶端訂閱主題
    self.__client.on_connect = self.__on_connect
    #TODO 呼叫回調函式處理訂閱主題收到的資料
    self.__client.on_message = self.on_message
    self.__client.on_disconnect = self.__on_disconnect
    if mode is not None:
      if mode == True:
        self.__client.loop_start()
      else:
        #TODO 以非阻塞方式連接Mqtt代理者
        self.__client.loop_forever()

  def Disconnect(self):
    self.__client.loop_stop()
    self.__client.disconnect()

  #TODO 印出詳細的例外訊息
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

  #TODO 印出連線狀態的資訊
  def __on_connect(self, client, userdata, flags, rc):
    #TODO 倘若狀態為0，表示有連上代理伺服器，則會訂閱指定主題與顯示連線狀態
    if rc == 0:
      print("client is connected.\nstatus code:{}".format(str(rc)))
      if self.__subscribe_topics is not None:
        self.__client.subscribe(self.__subscribe_topics)
        print(self.__subscribe_topics)
      else:
        print('subscribe topic None')
    #TODO 反之，印出連線失敗的訊息
    else:
      print("connection failed")

  #TODO 接收客戶訂閱主題的內容
  def on_message(self, client, userdata, message):
    try:
      decode_message = str(message.payload.decode("utf-8", "ignore"))
      receive_data = json.loads(decode_message)
      receive_topic = message.topic
      print('訂閱主題:{}\n接收數據:{}'.format(receive_topic,receive_data))
    except Exception as e:
      self.HandleError(e)

  def __on_disconnect(self, client, userdata, rc):
    if rc != 0:
      print('disconnect from mqtt client. . .')

  #TODO 推送資料至指定的主題
  def Publish(self, **kwargs):
   #TODO 倘若主題與訊息皆不為None則會將數據推送至指定的主題，並傳回True
   if kwargs['pub_topic'] is not None and kwargs['pub_message'] is not None:
       self.__client.publish(kwargs['pub_topic'],kwargs['pub_message'],kwargs['pub_qos'],kwargs['pub_retain'])
       print("推送成功!")
       return True
   #TODO 反之，則傳回False
   else:
    print("推送失敗!")
    return False
