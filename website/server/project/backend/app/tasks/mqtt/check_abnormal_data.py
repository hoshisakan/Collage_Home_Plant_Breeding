import json
import requests
import sys
sys.path.append("...")
import instance.config as Onesignal
import traceback

#TODO 宣告一個字典的全域變數
storage_response = {}
#TODO 宣告一個字串全域變數，儲存警告訊息
send_message = ''
#TODO 宣告一個列表全域變數儲存鍵的名稱
#TODO mode的鍵儲存感測器的控制指令，send的鍵儲存是否允許送出警報，message的鍵儲存異常訊息
#TODO 測試時註解此行
init_key = ['mode','send','message']
#TODO 測試時解開此註解
# init_key = ['mode','send']

#TODO lambda 參數1,參數2:{鍵運算式:值運算式 for 運算式 in 可迭代對象}，生成一組值為空的字典
Initial = lambda add_key:{key:{} for key in add_key}
#TODO 將init_key列表的內容作為鍵，值則為空白
storage_response = Initial(init_key)

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
    print('例外訊息:',errMsg)

#TODO 字典產生器，用於快速生成一組包含鍵值的字典
def DictGenerator(data_key=None,data_value=None):
  #TODO 宣告一個變數，暫存鍵與值
    dict_items = {}
    #TODO 若傳遞過來的鍵與值皆不為None
    if data_key is not None and data_value is not None:
      #TODO 創建一個字典，以參數1的data_key作為鍵,參數2的data_value作為值
      dict_items[data_key] = data_value
    #TODO 若有任一參數為None
    else:
      #TODO 將暫存鍵與值的變數設為None
      dict_items = None
    #TODO 回傳生成的結果
    return dict_items

#TODO 更新指定鍵的值
def UpdateDict(update_key,update_thing):
  global storage_response
  #TODO 若傳遞過來的鍵與值皆不為None
  if update_key is not None and update_thing is not None:
      #TODO 更新值到指定的鍵中
      storage_response[update_key].update(update_thing)
  #TODO 若有任一參數為None，則什麼都不做
  else:
    print('It is None!')

def CombineDict(abnormal_key,abnormal_value):
  #TODO 同時迭代三組List的值
  for read_key,read_value,update_key in zip(abnormal_key,abnormal_value,init_key):
    #TODO 將藉由DictGenerator()函式產生的一組字典型態的資料作為更新字典的值
    UpdateDict(update_key,DictGenerator(read_key,read_value))

#TODO 蒐集異常訊息並儲存
def CollectAlertMessage(alert_message=None):
  global send_message
  if alert_message is not None:
    #TODO 將警告訊息存入全域變數send_message
    send_message += alert_message + '\n'
    #TODO 更新警報訊息(測試時註解此行)
    UpdateDict('message',{'alert':send_message})

#TODO 檢查環境溫度的資料是否符合門檻值，根據檢查結果判斷是否送出警報
def CheckTemperature(temperature=None):
    if temperature is not None:
       abnormal_key = ['no_switch_temp','temperature_alert']
       if temperature > 0 and temperature >= 16 and temperature < 30:
          abnormal_value = [False,False]
       elif temperature > 0 and temperature < 16 or temperature >= 30:
          if temperature < 16:
              abnormal_value = [False,True]
              temp_message = '低溫警報：' + str(temperature) + ' °C'
          else:
              abnormal_value = [False,True]
              temp_message = '高溫警報：' + str(temperature) + ' °C'
          CollectAlertMessage(temp_message)
       CombineDict(abnormal_key, abnormal_value)

#TODO 檢查環境濕度的資料是否符合門檻值，根據檢查結果判斷是否送出警報
def CheckEnvironmentHumidity(env_humidity=None):
  if env_humidity is not None:
    #TODO 宣告一個List作為儲存控制指令與發送警告訊息的鍵
    abnormal_key = ['no_switch_env','temperature_alert']
    #TODO 若濕度適中
    if env_humidity >= 45 and env_humidity <= 65:
      abnormal_value = [False,False]
    #TODO 若濕度過高
    elif env_humidity > 65:
      #TODO 宣告一個List作為儲存控制指令與發送警告訊息的鍵
      abnormal_value = [False,True]
      #TODO 宣告一個變數暫存欲送出的異常訊息
      temp_message = '環境濕度過高：' + str(env_humidity) + ' %RH'
      #TODO 呼叫此函式儲存異常值
      CollectAlertMessage(temp_message)
    #TODO 若濕度過低
    else:
      #TODO 宣告一個List作為儲存控制指令與發送警告訊息的鍵
      abnormal_value = [False,True]
      #TODO 宣告一個變數暫存欲送出的異常訊息
      temp_message = '環境濕度過低：' + str(env_humidity) + ' %RH'
      #TODO 呼叫此函式儲存異常值
      CollectAlertMessage(temp_message)
    #TODO 呼叫此函式，更新控制指令與寄送警報的允許
    CombineDict(abnormal_key, abnormal_value)

def CheckHealthStatus(health_status=None):
  if health_status is not None:
    abnormal_key = ['no_switch_health_status','health_status_alert']
    if health_status < 40:
      abnormal_value = [False,True]
      temp_message = '植物生長不良：' + str(health_status) + ' %'
      CollectAlertMessage(temp_message)
    else:
      abnormal_value = [False,False]
    CombineDict(abnormal_key, abnormal_value)

#TODO 檢查環境亮度的資料是否符合門檻值，根據檢查結果送出開燈或關燈的指令
def WhetherTurnOnLight(brightness=None):
    if brightness is not None:
      #TODO 宣告一個List作為儲存控制指令與發送警告訊息的鍵
      abnormal_key = ['switch_light_state','brightness_alert']
      #TODO 如果環境亮度不足
      if brightness > 0 and brightness >= 51:
        #TODO 宣告一個變數儲存控制指令與發送警告訊息的允許
        #TODO 第一個False表示送出關燈指令，第二個False則表示無須送出警告訊息
        abnormal_value = [False,False]
      #TODO 如果環境亮度足夠
      elif brightness > 0 and brightness < 51:
        #TODO 宣告一個變數暫存欲送出的異常訊息
        temp_message = '日照光線不足：' + str(brightness) + " %"
        #TODO 第一個True表示送出開燈指令，第二個True則表示送出警告訊息的允許
        abnormal_value = [True,True]
        #TODO 呼叫此函式儲存異常值
        CollectAlertMessage(temp_message)
      #TODO 呼叫此函式，更新控制指令與寄送警報的允許
      CombineDict(abnormal_key, abnormal_value)

#TODO 檢查土壤濕度與水位深度的資料是否符合門檻值，根據檢查結果送出澆水或停止澆水的指令
def WhetherTurnOnWatering(water_level=None,soil_moisture=None):
  water_level_abnormal_key = ['switch_motor_state','water_level_alert']
  soil_moisture_abnormal_key = ['switch_motor_state','soil_moisture_alert']

  #TODO 水量充足且土壤濕度不足
  if water_level > 30 and soil_moisture > 1 and soil_moisture <= 30:
    #TODO 宣告一個變數儲存控制指令與發送警告訊息的允許
    #TODO 第一個True表示送出澆水指令，第二個True則表示允許送出警報
    abnormal_value = [True,True]
    #TODO 宣告一個變數暫存欲送出的異常訊息
    temp_message = '土壤水分不足：' + str(soil_moisture) + ' %'
    CollectAlertMessage(temp_message)
  #TODO 水位過低且土壤濕度不足
  elif water_level <= 30 and soil_moisture > 1 and soil_moisture <= 30:
    #TODO 宣告一個變數儲存控制指令與發送警告訊息的允許
    #TODO 第一個False表示送出停止澆水指令，第二個True則表示允許送出警報
    abnormal_value = [False,True]
    #TODO 宣告一個變數暫存欲送出的異常訊息
    temp_message = '水量過低：' + str(water_level) + " %" + '\n土壤水分不足：' + str(soil_moisture) + ' %'
    CollectAlertMessage(temp_message)
  #TODO 水位過低且土壤濕度充足
  elif water_level <= 30 and soil_moisture > 30:
    #TODO 宣告一個變數儲存控制指令與發送警告訊息的允許
    #TODO 第一個False表示送出停止澆水指令，第二個True則表示允許送出警報
    abnormal_value = [False,True]
    #TODO 宣告一個變數暫存欲送出的異常訊息
    temp_message = '水量過低：' + str(water_level) + " %"
    CollectAlertMessage(temp_message)
  #TODO 水量充足且土壤濕度充足
  elif water_level > 30 and soil_moisture > 30:
    #TODO 第一個False表示送出停止澆水指令，第二個False則表示無須送出警報
    abnormal_value = [False,False]
  #TODO 呼叫此函式，更新控制指令與寄送警報的允許
  CombineDict(water_level_abnormal_key, abnormal_value)
  CombineDict(soil_moisture_abnormal_key, abnormal_value)

#TODO 發送警報訊息
def SendAbnormalAlertMessage():
    global send_message
    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization":
              Onesignal.AUCTION_KEY}
    # TODO 表頭需先透過REST API KEY進行身分認證
    # TODO 欲傳送的訊息
    # TODO en是固定鍵不可更改，冒號後面為值(訊息)
    payload = {"app_id": Onesignal.AUCTION_ID,
               "included_segments": ["All"],
               "contents": {"en": send_message}}
    req = requests.post("https://onesignal.com/api/v1/notifications",
                        headers=header, data=json.dumps(payload))
    # TODO data = json.dumps(payload)將python的字典資料型態轉成JSON的資料型態
    response_data = {}
    response_data['request_status_code'] = req.status_code
    response_data['request_reason'] = req.reason
    print(response_data)
    send_message = ""
    # TODO 印出傳送通知是否成功的訊息
    # TODO 失敗 "request_reason": "OK","request_status_code": 200
    # TODO 失敗 "request_reason": "Bad Request","request_status_code": 400

#TODO 蒐集感測器偵測的資料
def CollectSensorData(check_data=None):
   try:
      #TODO 檢查環境溫度的資料是否符合門檻值
      CheckTemperature(check_data['temperature'])
      #TODO 檢查環境溫度的資料是否符合門檻值
      CheckEnvironmentHumidity(check_data['humidity'])
      #TODO 檢查環境亮度的資料是否符合門檻值，根據檢查結果送出開燈或關燈的指令
      WhetherTurnOnLight(check_data['brightness'])
      #TODO 檢查土壤濕度與水位深度的資料是否符合門檻值，根據檢查結果送出澆水或停止澆水的指令
      WhetherTurnOnWatering(check_data['water_level'], check_data['soil'])

      #TODO 迭代字典所有的鍵
      for key in storage_response['send']:
        #TODO 若該字典的指定鍵中有任一為True
        if storage_response['send'][key] == True:
          #TODO 呼叫發送警報訊息的函式
          SendAbnormalAlertMessage()
          #TODO 送出警報訊息後跳出迴圈
          break
      #TODO 返回感測器端的控制指令
      return storage_response['mode']
   except Exception as e:
      CatchError(e)

def CollectGrowingData(health_status=None):
  try:
      #TODO 檢查植物健康度的資料是否符標準
      CheckHealthStatus(health_status)
      #TODO 迭代字典所有的鍵
      for key in storage_response['send']:
        #TODO 若該字典的指定鍵中有任一為True
        if storage_response['send'][key] == True:
          #TODO 呼叫發送警報訊息的函式
          SendAbnormalAlertMessage()
          #TODO 送出警報訊息後跳出迴圈
          break
      # print(storage_response['message'])
      #TODO 返回感測器端的控制指令
      if storage_response['mode'] is not None:
        return storage_response['mode']
  except Exception as e:
      CatchError(e)
