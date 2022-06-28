import ssl
import os
import cv2
import numpy as np
import time
import json
import sys
import datetime as dt
import traceback
import threading
sys.path.append("..")
from module.mqtt_base import MqttBase
from module.file import GetFileWorkingPath as GP

recognition_sub = None
recognition_pub = None
manually_take_picture_pub = None
manually_take_picture_count = 0
open_light_pub = None
data_pub_count = 0
orignal_image_path = None
anatomy_image_path = None
sensor_light_status = None
env_birghtness = 0

check_whether_exist = lambda path: os.path.exists(path)

check_file_whether_exist = lambda path: os.path.isfile(path)

class SurveillanceImageMqtt(MqttBase):
  def __init__(self, client_id=None, subscribe_topics=None):
    #TODO 子類別調用父類別的初始化方法
    super().__init__(client_id, subscribe_topics)
    #TODO 子類別另外定義屬於自身的私有屬性

  #TODO 覆寫父類別的on_message，添加其他的內容至此函式
  def on_message(self, client, userdata, message):
    try:
      global sensor_light_status
      # TODO 將json資料格式進行轉換成python的字典資料型態
      receive_message_topic = message.topic
      receive_data = str(message.payload.decode("utf-8", "ignore"))
      receive_response_message = json.loads(receive_data)

      if receive_message_topic == 'response/anatomy/message' or receive_message_topic == 'response/monitor/message':
        for key,value in receive_response_message.items():
          if key == 'monitor' and value == 'Yes':
            print('是否收到監控圖像?{}'.format(value))
            os.remove(orignal_image_path)
            if not check_whether_exist(orignal_image_path) and not check_file_whether_exist(orignal_image_path):
              print('本地保存的原始圖片已經移除')
          elif key == 'anatomy' and value == 'Yes':
            print('是否收到辯識圖像?{}'.format(value))
            os.remove(anatomy_image_path)
            if not check_whether_exist(anatomy_image_path) and not check_file_whether_exist(anatomy_image_path):
              print('本地保存的辯識圖片已經移除')
      elif receive_message_topic == 'manually/take/picture':
        for mode,allow in receive_response_message.items():
          if mode == 'manually_take_picture' and allow is True:
            ManuallyTakePicture()
          else:
            print('do nothing')
      elif receive_message_topic == 'receive/sensor/light/status':
        sensor_light_status = receive_response_message.get('status', 'Empty')
        env_brightness = receive_response_message.get('brightness')
        temp_msg = '目前燈光狀態:{} 光敏數值:{}'.format(sensor_light_status,env_brightness)
        print(temp_msg)
        StorageExecuteMessage(False,temp_msg)
      else:
        pass
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

#TODO 強制停止
def ForceStop(abnormal=None):
    global recognition_sub,recognition_pub
    # global recognition_sub
    #TODO 中斷與MQTT代理人的連結
    recognition_sub.Disconnect()
    recognition_pub.Disconnect()
    if abnormal is not None:
        print('異常數據:{}'.format(abnormal))
    else:
        print('強制退出程式. . .')
    os._exit(0)

#TODO 印出詳細的錯誤訊息
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
    print(errMsg)
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

def DataSubscriber():
    global recognition_sub
    try:
        #TODO 客戶ID
        client_id = 'host_b_test'
        #TODO 訂閱主題
        subscribe_topics = [('response/monitor/message',2),('response/anatomy/message',2),
                            ('receive/sensor/light/status',2),('manually/take/picture',2)]
        #TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
        recognition_sub = SurveillanceImageMqtt(client_id, subscribe_topics)
        #TODO 開始連線，訂閱以上的主題
        recognition_sub.Connect(False)
    except Exception as e:
        CatchError(e)

#TODO 取得當前的時間
GetDateTimeCurrent = lambda:dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def SendModePublisher(send_data=None):
  if send_data is not None:
    global open_light_pub
    try:
      # TODO 客戶ID
      client_id = 'sensor_relay_mode_switch'
      # TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
      subscribe_topics = None
      # TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
      send_mode_pub = SurveillanceImageMqtt(client_id, subscribe_topics)
      # TODO 開始連線推送資料
      send_mode_pub.Connect(True)

      print('轉換前:{}'.format(send_data))
      convertion_json = json.dumps(send_data)

      send_result = send_mode_pub.Publish(
        pub_topic='switch/light',
        pub_message=convertion_json,
        pub_qos=2,
        pub_retain=False
      )
      if send_result is True:
        print('成功推送開燈指令!')
      send_mode_pub.Disconnect()
    except Exception as e:
      CatchError(e)

def get_image_name(image_path=None):
    if image_path is not None:
      image_files_list = os.listdir(image_path)
      image_files_list.sort(
            key=lambda fn: os.path.getctime(image_path + "/" + fn))
      latest_filename = os.path.join(image_path, image_files_list[-1])
      return latest_filename
    return None

def SaveImage():
    global orignal_image_path,anatomy_image_path
    health_number = None

    cap = cv2.VideoCapture(0)

    if cap.isOpened():
        camera_opened=1
        print('success opened the camera')
    else :
        camera_opened=0
        print("fail opened the camera")

    while(camera_opened):
        ret,frame = cap.read()
        frame2 = frame.copy()
        result_brown = frame.copy()
        result_green = frame.copy()
    
   
        hsv_g = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2HSV)   #將image color_BGR 轉化為HSV
        hsv_b = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2HSV)
    
        lower_g = np.array([30,90,90])   #設定目標顏色上下限
        upper_g = np.array([40,245,245])   #g=green
        #25 100 50
        #75 255 255
    
        lower_b = np.array([10, 50, 50])  
        upper_b = np.array([20, 245, 245])  #b=brown
        #10 0 0
        #20 235 235
        
        #15 80 80
        #27 235 235
    
        mask_g = cv2.inRange(hsv_g, lower_g, upper_g)   #開始分割綠色
        mask_g = cv2.GaussianBlur(mask_g, (5, 5), 0)
        mask_g = cv2.blur(mask_g, (5, 5))
        canny_mask_g = cv2.Canny(mask_g,30,100)
        #cv2.imshow('canny_mask_g',canny_mask_g)
    
    
        mask_b = cv2.inRange(hsv_b, lower_b, upper_b)
        #cv2.imshow('canny_mask_b',mask_b)
        
        mask_b = cv2.GaussianBlur(mask_b, (7, 7), 0)
        mask_b = cv2.blur(mask_b, (5, 5))
        #cv2.imshow('mask_b',mask_b)
        canny_mask_b = cv2.Canny(mask_b,100,200)
    
        #cv2.imshow('canny_mask_b',canny_mask_b)
    
        contours_g, hierarchy = cv2.findContours(mask_g,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        contours_b, hierarchy = cv2.findContours(mask_b,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    
        if len(contours_b)>0:
        #取得輪廓特徵面積
            center_b=max(contours_b,key=cv2.contourArea)
            # 取得圓的中心點與半徑
            ((x,y),radius)=cv2.minEnclosingCircle((center_b))
    
            #取得輪廓特徵面積矩陣
            M=cv2.moments(center_b)

            if M["m00"] != 0:
                #尋找特徵點的重心X跟Y，特過矩陣 M['m10']/M['m00']取得X，M['m01']/M['m00']取得Y
                center = (int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"]))
            
                area2 = cv2.contourArea(center_b)
                #print('brown:',area2)
            
                if radius >5:

                    #在圖像frame上畫圓，第一個參數圖像，第二個參數中心點，第三個參數圓的半徑，第四個參數圓的顏色，第5個參數線條寬度
                    #cv2.circle(frame,(int(x),int(y)),int(radius),(0,255,255),2)
                    #cv2.circle(frame,center,5,(0,0,255),-1)
                
                    cv2.drawContours(result_brown,contours_b,-1,(0,0,255),3)
                    x,y,w,h = cv2.boundingRect(center_b)
    
    
        if len(contours_g) > 0:
        #取得輪廓特徵面積
            center_g=max(contours_g,key=cv2.contourArea)
            # 取得圓的中心點與半徑
            ((x,y),radius)=cv2.minEnclosingCircle((center_g))
    
            #取得輪廓特徵面積矩陣
            M=cv2.moments(center_g)

            if M["m00"] != 0:
            #尋找特徵點的重心X跟Y，特過矩陣 M['m10']/M['m00']取得X，M['m01']/M['m00']取得Y
                center = (int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"]))
            
                area = cv2.contourArea(center_g) + area2
                #print('green:',area)
            
                if radius >5:

                    #在圖像frame上畫圓，第一個參數圖像，第二個參數中心點，第三個參數圓的半徑，第四個參數圓的顏色，第5個參數線條寬度
                    cv2.circle(frame2,(int(x),int(y)),int(radius),(0,255,255),2)
                    cv2.circle(frame2,center,5,(0,0,255),-1)
                    cv2.drawContours(result_green,contours_g,-1,(0,0,255),3)
                    x,y,w,h = cv2.boundingRect(center_g)
                
                    crop = frame[y:y+h,x:x+w]
                
                
                    hsv_b = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                    crop_mask = cv2.inRange(hsv_b, lower_b, upper_b)
                
                    contours2, hierarchy2 = cv2.findContours(crop_mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
                    #cv2.imshow('crop_green', crop_mask)
                    if len(contours2) > 0:
                        c2=max(contours2,key=cv2.contourArea)
                        area2 += cv2.contourArea(c2)
                    
                        hsv_crop = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    
                        mask_crop = cv2.inRange(hsv_crop, lower_g, upper_g)   #開始分割綠色
                        mask_crop = cv2.GaussianBlur(mask_crop, (7, 7), 0)
                        mask_crop = cv2.blur(mask_crop, (7, 7))
                        canny_crop = cv2.Canny(mask_crop,30,100)
                    
                    
                        contours3, hierarchy3 = cv2.findContours(canny_crop,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
                        #cv2.drawContours(result_green,contours3,-1,(0,0,255),3)
                        #cv2.drawContours(crop,contours2,-1,(0,0,255),3)
                        #cv2.imshow('mask_crop', canny_crop)
                        #print('brown:',area2)
                        #cv2.imshow('result2', crop)
                    #cv2.putText(frame2,'Hello',center,cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),6)
                    #else:
                        #area2=0
                
                    if area!=0 and area2!=0:
                        health_number = int(100-((area2/area)*100))
                        print('green:',area,'  brown:',area2,'  health_number:',int(100-((area2/area)*100)),'%')
                    #else:
                        #print('no data')
        #cv2.drawContours(frame2,contours,-1,(0,0,255),3)
        #cv2.putText(frame2,'Hello',(cx,cy),cv2.FONT_HERSHEY_COMPLEX,6,(0,0,255),6)
            else:
                print('green:0')
            
        #cv2.imshow('video', frame)
        #cv2.imshow('result', frame2)
        #cv2.imshow('result2', crop)
        #print('brown:',area2)
        #print('green:',area)
        #health_number = int(100-((area2/area)*100))
        
        #print(len(contours))
    
    
        k = cv2.waitKey(1) & 0xFF
        
        orignal_image_path = GP.GetFullPath(filename='{}.jpeg'.format(GetDateTimeCurrent()),
                                            dirname='img',mode=True)
        anatomy_image_path = GP.GetFullPath(filename='{}.jpeg'.format(GetDateTimeCurrent()),
                                            dirname='anatomy',mode=True)
        cv2.imwrite(orignal_image_path,frame)
        cv2.imwrite(anatomy_image_path,result_brown)
        #cv2.imwrite(anatomy_image_path,frame2)
        exc_mode = {'light_status': False}
        break

    cap.release()
    cv2.destroyAllWindows()

    if check_whether_exist(orignal_image_path) and check_whether_exist(anatomy_image_path):
      return True,health_number
    else:
      return False,None

def Conversion(dirname=None):
  if dirname is not None:
    image_path = GP.GetFullPath(dirname=dirname,mode=False)
    image_name = get_image_name(image_path)
    image_full_path = os.path.join(image_path,image_name)
    if check_file_whether_exist(image_full_path):
      #TODO 讀取檔案內容並將其以bytes的資料格式返回
      #TODO 模式「b」即是binary mode，未加則是以str的形式將資料返回
      with open(file='{}'.format(image_full_path),mode='rb') as image:
        image_content = image.read()
        conversion_bytes = bytes(image_content)
      return conversion_bytes
    else:
      return None
  else:
    return False

def DataPublisher():
    global recognition_pub,data_pub_count
    try:
        #TODO 客戶ID
        client_id = 'host_a_test'
        #TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
        subscribe_topics = None
        #TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
        recognition_pub = SurveillanceImageMqtt(client_id, subscribe_topics)
        #TODO 開始連線推送資料
        recognition_pub.Connect(True)

        #TODO 確認連線後會開始傳送數據至指定主題
        while True:
          image_save_result,health_status = SaveImage()
          print('健康度:',health_status)
          if image_save_result == True and health_status is not None:
            send_data = {}
            send_result = None
            storage_dirname = ['img','anatomy',None]
            publish_topics = ['immediate/monitor/image','immediate/anatomy/image','immediate/plant/health']
            send_data['health_status'] = health_status
            send_data['created_date'] = GetDateTimeCurrent()

            for dirname,topic in zip(storage_dirname,publish_topics):
              if topic == 'immediate/monitor/image' or topic == 'immediate/anatomy/image':
                immediate_monitor_image = Conversion(dirname)
                send_result = recognition_pub.Publish(
                  pub_topic=topic,
                  pub_message=immediate_monitor_image,
                  pub_qos=2,
                  pub_retain=False
                )
              else:
                convertion_json = json.dumps(send_data)
                send_result = recognition_pub.Publish(
                  pub_topic=topic,
                  pub_message=convertion_json,
                  pub_qos=2,
                  pub_retain=False
                )
                print(send_result)
                #TODO 若傳輸成功則會接收到True
            
            if send_result == True:
              data_pub_count += 1
              message = "{} 傳送成功第 {} 筆資料".format(str(GetDateTimeCurrent()), str(data_pub_count))
              print(message)
              StorageExecuteMessage(False,message)
            else:
              message = 'Publish data failed. . .'
              StorageExecuteMessage(True,message)
          else:
            message = 'Image save field. . .'
            StorageExecuteMessage(True,message)
          #TODO 一分鐘傳一次數據
          time.sleep(10)
    except Exception as e:
      CatchError(e)

def ManuallyTakePicture():
    global manually_take_picture_pub,manually_take_picture_count
    try:
        #TODO 客戶ID
        client_id = 'manually_take_picture'
        #TODO 訂閱主題(由於推送與訂閱主題是分開的，因此這裡設定成None，這個函式僅負責推送資料)
        subscribe_topics = None
        #TODO 初始化SensorMqtt物件，傳遞客戶ID與訂閱主題
        manually_take_picture_pub = SurveillanceImageMqtt(client_id, subscribe_topics)
        #TODO 開始連線推送資料
        manually_take_picture_pub.Connect(True)

        #TODO 確認連線後會開始傳送數據至指定主題
        image_save_result,health_status = SaveImage()
        print('健康度:',health_status)
        if image_save_result == True and health_status is not None:
          send_data = {}
          send_result = None
          storage_dirname = ['img','anatomy',None]
          publish_topics = ['immediate/monitor/image','immediate/anatomy/image','immediate/plant/health']
          send_data['health_status'] = health_status
          send_data['created_date'] = GetDateTimeCurrent()

          for dirname,topic in zip(storage_dirname,publish_topics):
            if topic == 'immediate/monitor/image' or topic == 'immediate/anatomy/image':
              immediate_monitor_image = Conversion(dirname)
              send_result = manually_take_picture_pub.Publish(
                pub_topic=topic,
                pub_message=immediate_monitor_image,
                pub_qos=2,
                pub_retain=False
              )
            else:
              convertion_json = json.dumps(send_data)
              send_result = manually_take_picture_pub.Publish(
                pub_topic=topic,
                pub_message=convertion_json,
                pub_qos=2,
                pub_retain=False
              )
              print(send_result)
          #TODO 若傳輸成功則會接收到True
          if send_result == True:
            manually_take_picture_count += 1
            message = "{} 傳送成功第 {} 筆資料".format(str(GetDateTimeCurrent()), str(manually_take_picture_count))
            print(message)
            StorageExecuteMessage(False,message)
          else:
            message = 'Publish data failed. . .'
            StorageExecuteMessage(True,message)
        else:
          message = 'Image save field. . .'
          StorageExecuteMessage(True,message)
        manually_take_picture_pub.Disconnect()
        print('中斷連線. . .')
    except Exception as e:
      CatchError(e)

#TODO 初始化MQTT訂閱主題的子線程
task_sub = threading.Thread(target=DataSubscriber)
#TODO 初始化MQTT推送資料的子線程
task_pub = threading.Thread(target=DataPublisher)

#TODO 若此程式是直接執行，而非以模組方式被執行時，則會執行以下程式
if __name__ == '__main__':
    try:
        task_sub.start()
        #TODO 執行MQTT訂閱主題的子線程
        task_pub.start()
        #TODO 執行MQTT推送資料的子線程
        task_sub.join()
        task_pub.join()
    except KeyboardInterrupt:
        ForceStop()
