# Collage_Home_Plant_Breeding

CentOS-Docker-Nginx-SSL-uWSGI-Vue.js-Flask-MySQL-Mosquitto-OpenCV

透過 [Docker](https://www.docker.com/) 建立 [Vue.js
](https://vuejs.org/) + [Flask](https://flask.palletsprojects.com/en/2.0.x/) + [Nginx](https://nginx.org/en/) + [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) + [MySQL](https://www.mysql.com/) + [Mosquitto](https://mosquitto.org/) 製作居家植物養殖的網站

## 簡述
* 使用兩塊 Raspberry pi 分別連接感測器與羅技 C270 網路攝影機，蒐集植物生長環境數據與透過影像辨識技術剖析植物生長圖像計算其健康度，以及拍攝植物生長情況，並將其數據與圖像透過 MQTT topic 傳遞至 MQTT broker。

* 使用 Flask 建置後端伺服器，連接 MQTT broker，接收兩塊 Raspberry pi 傳遞的植物生長環境數據，以及植物生長圖像與健康度數值。

## Docker 開發環境建置

### docker-compose.yml 配置

```cmd
version: "3.7"
services:
  vue:
    build: ./conf/vue.js
    container_name: web_frontend_vue.js
    volumes:
      - ./server/project/frontend:/server/project/frontend/
    ports:
      - 8082:8080
      - 8081:8086
    tty: true
    privileged: true
    restart: always

  flask:
    build: ./conf/flask-uwsgi
    container_name: web_backend_flask
    command: ["bash", "./run_web.sh"]
    volumes:
      - temporary:/server/temporary
      - ./server:/server
      - ./server/project:/server/project
      - ./server/run_web.sh:/server/run_web.sh
      - ./server/vassal:/server/vassal
      - ./logs/uwsgi/temp:/var/log/uwsgi
    networks:
      - common
    ports:
      - 5000:5000
      - 5001:5001
    depends_on:
      - mysql
      - mosquitto
    restart: always

  nginx:
    build: ./conf/nginx
    container_name: web_nginx
    ports:
      - 80:80
      - 443:443
    volumes:
      - temporary:/server/temporary
      - ./server:/server
      - ./conf/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./conf/nginx/conf.d:/etc/nginx/conf.d/
      - ./conf/nginx/dhparam:/etc/nginx/dhparam
      - ./server/project/frontend/certs/ssl/:/etc/nginx/ssl
      - ./server/project/frontend/certs/data/:/usr/share/nginx/html/letsencrypt/
      - ./logs/nginx/message:/var/log/nginx
    tty: true
    depends_on:
      - flask
      - mysql
    networks:
      - common
    restart: always

  mysql:
    image: mysql:5.7
    container_name: web_mysql
    ports:
      - 3306:3306
    volumes:
      - ./data/db/mysql/:/var/lib/mysql/
      - ./conf/mysql/my.cnf:/etc/mysql/my.cnf
    environment:
      - MYSQL_ROOT_USER=${MYSQL_ROOT_USER:-root}
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-967832134}
      - MYSQL_USER=${MYSQL_USER:-hoshisakan}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD:-967832}
      - MYSQL_DATABASE=${MYSQL_DATABASE:-Default}
    restart: always

  web_phpMyAdmin:
    image: phpmyadmin/phpmyadmin:latest
    container_name: web_phpMyAdmin
    ports:
      - 8081:80
    environment:
      - PMA_HOST=${MYSQL_HOST:-mysql}
    depends_on:
      - mysql
    restart: always

  mosquitto:
    build: ./conf/mosquitto
    container_name: web_mosquitto
    ports:
      - 1883:1883
      - 8883:8883
      - 9001:9001
      - 9002:9002
    environment:
      - MOSQUITTO_USERNAME=${MOSQUITTO_USERNAME}
      - MOSQUITTO_PASSWORD=${MOSQUITTO_PASSWORD}
      - MOSQUITTO_LOGFILENAME=${MOSQUITTO_LOGFILENAME}
    volumes:
      - ./conf/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - ./logs/mosquitto/:/mosquitto/log
      - ./conf/mosquitto/docker-entrypoint.sh:/docker-entrypoint.sh
      - ./conf/mosquitto/passwordfile:/mosquitto/passwordfile
      - ./server/project/frontend/certs/ssl/:/var/lib/mosquitto
    networks:
      - common
    restart: always

volumes:
  temporary:

networks:
  common:
    external: true

```

### .env 檔案配置

> 註: 此步驟一定要做，否則當創建 MySQL 與 phpMyAdmin，以及 mosquitto 容器，且沒有給預設值時，會造成其創建失敗

```cmd
#MYSQL
MYSQL_ROOT_USER=your MySQL normal administrator password
MYSQL_ROOT_PASSWORD=your MySQL administrator password
MYSQL_USER=your MySQL normal user password
MYSQL_PASSWORD=your MySQL normal user password
MYSQL_DATABASE=your MySQL database name
MYSQL_HOST=mysql
##對應到docker-compose.yml中mysql的服務名稱
MAX_LIMIT=2000
##資料上限
#MOSQUITTO
MOSQUITTO_USERNAME=your mqtt broker username
MOSQUITTO_PASSWORD=your mqtt broker password
MOSQUITTO_LOGFILENAME=/mosquitto/log/05_10_mosquitto.log

```

### Docker 查看容器運行情況

```cmd
docker-compose ps
```
![alt](https://imgur.com/XybHd4C.png)
![alt](https://imgur.com/K9V236D.png)


## MySQL && phpMyAdmin

### phpMyAdmin 查看 MySQL 資料庫的資料表

![alt](https://imgur.com/gM4Zaur.png)
![alt](https://imgur.com/mJtgMtj.png)

## Eclipse Mosquitto && Raspberry Pi

* 建立與 Mosquitto Server 的連線

```cmd
  def Connect(self,mode=None):
    self.__client.username_pw_set(cf.username, cf.password)
    self.__client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                          tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    self.__client.tls_insecure_set(True)
    self.__client.connect(self.__host, self.__port, 60)
    self.__client.on_connect = self.__on_connect
    self.__client.on_message = self.on_message
    self.__client.on_disconnect = self.__on_disconnect
    if mode is not None:
      if mode == True:
        self.__client.loop_start()
      else:
        self.__client.loop_forever()
```
* 斷開與 Mosquitto Server 的連線

```cmd
def Disconnect(self):
    self.__client.loop_stop()
    self.__client.disconnect()
```

* 推送訊息透過主題

```cmd
def Publish(self, **kwargs):
   if kwargs['pub_topic'] is not None and kwargs['pub_message'] is not None:
       self.__client.publish(kwargs['pub_topic'],kwargs['pub_message'],kwargs['pub_qos'],kwargs['pub_retain'])
       print("推送成功!")
       return True
   else:
    print("推送失敗!")
    return False
```

* 接收訊息透過主題

```cmd
def on_message(self, client, userdata, message):
    try:
      decode_message = str(message.payload.decode("utf-8", "ignore"))
      receive_data = json.loads(decode_message)
      receive_topic = message.topic
      print('訂閱主題:{}\n接收數據:{}'.format(receive_topic,receive_data))
    except Exception as e:
      self.HandleError(e)
```

## Flask 後端 Web Server

### 儲存資料至 MySQL 資料庫的資料表中

* 建構一個指標，獲取對資料庫操作的權限

```cmd
class DataBase():
    def __init__(self, *args):
        self.connection = pymysql.connect(
            host=MySQL.MYSQL_HOST,
            user=MySQL.MYSQL_USER,
            database=MySQL.MYSQL_DB,
            password=MySQL.MYSQL_PASSWORD,
            port=MySQL.MYSQL_PORT,
            cursorclass=DictCursor
        )
        self.connection.autocommit(True)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()
```

* 執行 SQL Insert Command

```cmd
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
```

* 執行 SQL Update Command

```cmd
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
```

* 檢測環境數值是否異常，異常則發送推播

```cmd
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
```

* 接收 Raspberry pi 透過 MQTT 發送的圖片，以二進制方式寫入將其儲存至伺服器端

```cmd
@staticmethod
def save_image(save_path=None,rec_image=None,rec_topic=None):
    global save_image_count
    temp_msg = ""
    send_msg = {}
    dict_keys = ['monitor','anatomy']
    with open(save_path, 'wb') as handle:
        handle.write(rec_image)
        if os.path.isfile(save_path):
            save_image_count += 1
            print("第{}張圖像儲存成功!".format(str(save_image_count)))
            temp_msg = 'Yes'
            if rec_topic == 'response/monitor/message':
                send_msg[dict_keys[0]] = temp_msg
            else:
                send_msg[dict_keys[1]] = temp_msg
        else:
            print("圖像儲存失敗. . .")
            temp_msg = "No"
            if rec_topic == 'response/monitor/message':
                send_msg[dict_keys[0]] = temp_msg
            else:
                send_msg[dict_keys[1]] = temp_msg
    return send_msg
```

## 推播服務 OneSingnal

### 操作流程

> OneSingnal 服務設定，需貼上網站的 URL才能夠使用此服務

![alt](https://imgur.com/a1d7tHl.png)
![alt](https://imgur.com/eG7jLQo.png)

> Vue.Js 的專案底下其 index.html 也要加上其 SDK 的引用

```cmd
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
```

> 此外，Vue.JS 還需要加上初始化 OneSignal 服務的設定

```cmd
 methods: {
    // 初始化OneSignal的通知
    InitOnce () {
      if (this.alert_enable !== true) {
        var OneSignal = window.OneSignal || []
        OneSignal.push(function () {
          OneSignal.init({
            appId: 'cc5f345e-09f7-4b47-8f56-1f5509e417ba',
            autoResubscribe: true,
            notifyButton: {
              enable: true
            }
            // allowLocalhostAsSecureOrigin: true
          })
          OneSignal.showNativePrompt()
          OneSignal.showSlidedownPrompt()
        })
      }
      this.alert_enable = true
    }
  },
```

### 測試推播服務

![alt](https://imgur.com/sfZGMOe.png)

# 運行結果

### 監控植物生長的環境狀態與其生長情況

![alt](https://imgur.com/ImcU5fU.png)

### 透過羅技 c270 的鏡頭捕捉植物的生長狀態

![alt](https://imgur.com/3mGQR6v.png)

### 網頁手機版介面

![alt](https://imgur.com/Fk7eW4Z.jpg)

### 硬體展示

![alt](https://imgur.com/y9Ptxwc.jpg)