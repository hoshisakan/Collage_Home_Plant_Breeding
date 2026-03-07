# 關鍵程式碼分析：GPIO 控制、例外處理與異步執行

本文件針對專案 **website**、**sensor**、**image_recognition** 中與硬體控制、感測器防呆、以及 OpenCV 與感測器讀取並行執行相關的**關鍵程式碼**進行摘錄與說明。

---

## 一、GPIO 控制：高低電位切換的實作

專案中**唯一直接驅動 GPIO 的程式**為 **sensor** 模組的 **`mqtt_for_sensor.py`**。電位切換透過 **`RPi.GPIO`** 的 **`GPIO.output(pin, value)`** 實作，**HIGH = 關閉繼電器、LOW = 開啟繼電器**（繼電器為低電位觸發）。

### 1.1 腳位與初始電位（模組載入時執行）

**檔案：** `sensor/mqtt_for_sensor.py`

```python
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
motor_pin = 17
light_pin = 18
GPIO.setup(motor_pin, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.HIGH)
```

| 項目 | 說明 |
|------|------|
| `GPIO.BCM` | 使用 BCM 腳位編號（17、18 為 Broadcom 編號） |
| `GPIO.OUT` | 將該腳位設為**輸出**，用於驅動繼電器 |
| `initial=GPIO.HIGH` | 程式啟動時腳位為**高電位**，繼電器不導通（安全預設） |

### 1.2 依 MQTT 指令改寫電位（開燈／關燈）

**檔案：** `sensor/mqtt_for_sensor.py` — `SensorMqtt.on_message()` 內

```python
if command is True:
    self.__light_current_status = GPIO.LOW
    print("開啟自動開燈功能")
    GPIO.output(light_pin, self.__light_current_status)
else:
    self.__light_current_status = GPIO.HIGH
    print("關閉自動開燈功能")
    GPIO.output(light_pin, self.__light_current_status)
```

- **開燈**：`command is True` → 將狀態設為 **`GPIO.LOW`**，再呼叫 **`GPIO.output(light_pin, GPIO.LOW)`**，腳位輸出**低電位**，繼電器導通、燈亮。
- **關燈**：`command is False` → **`GPIO.output(light_pin, GPIO.HIGH)`**，腳位**高電位**，繼電器關閉。

手動開關燈（`switch/light`）的實作相同邏輯：

```python
if command is True:
    self.__light_current_status = GPIO.LOW
    GPIO.output(light_pin, self.__light_current_status)
    print("手動開燈")
    # ...
else:
    self.__light_current_status = GPIO.HIGH
    GPIO.output(light_pin, self.__light_current_status)
    print("手動關燈")
```

### 1.3 馬達（澆水）的時序控制

**檔案：** `sensor/mqtt_for_sensor.py` — `on_message()` 內

```python
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
    GPIO.output(motor_pin, self.__motor_current_status)
```

- **開始澆水**：**`GPIO.output(motor_pin, GPIO.LOW)`** → 馬達繼電器導通；**`time.sleep(5)`** 維持 5 秒；接著 **`GPIO.output(motor_pin, GPIO.HIGH)`** 關閉馬達。
- **停止澆水**：直接 **`GPIO.output(motor_pin, GPIO.HIGH)`**。

### 1.4 小結：高低電位對應關係

| 腳位 | 用途 | HIGH（1） | LOW（0） |
|------|------|-----------|----------|
| GPIO 18 (`light_pin`) | 燈光繼電器 | 關燈 | 開燈 |
| GPIO 17 (`motor_pin`) | 馬達繼電器 | 馬達停止 | 馬達運轉（澆水） |

實作方式就是：**在需要切換時呼叫 `GPIO.output(pin, GPIO.LOW)` 或 `GPIO.output(pin, GPIO.HIGH)`**，無額外硬體抽象層。

---

## 二、例外處理（Exception Handling）：感測器讀不到數值時的防呆

感測器防呆集中在 **sensor** 的 **`CollectSensorData()`**、**`LightData()`**，以及 **`on_message()`** 的 try/except；**image_recognition** 則在 **`on_message()`** 與 **`DataPublisher`** 外層用 try/except 捕獲錯誤。

### 2.1 感測器讀取與有效值檢查（sensor）

**檔案：** `sensor/mqtt_for_sensor.py` — `CollectSensorData()`

```python
def CollectSensorData():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
    light = mcp.read_adc(0)
    soil = mcp.read_adc(1)
    water_level = mcp.read_adc(2)
    date = GetDateTimeCurrent()

    resultCovertList = ConvertPercent(brightness=light, soil=soil, water_level=water_level)
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "brightness": resultCovertList[0],
        "soil": resultCovertList[1],
        "water_level": resultCovertList[2],
        "date": date
    }

    if humidity is None or temperature is None:
        HandleAbnormal(data)
        return None
    elif soil == 0 or light == 0 or water_level == 0:
        HandleAbnormal(data)
        return False
    else:
        convertion_json = json.dumps(data)
        return convertion_json
```

防呆邏輯說明：

| 情況 | 處理方式 |
|------|----------|
| **DHT11 讀取失敗** | `Adafruit_DHT.read_retry()` 在失敗時會回傳 `None`；若 **`humidity is None or temperature is None`**，呼叫 **`HandleAbnormal(data)`**（見下），並 **`return None`**，不發送此筆資料。 |
| **類比感測異常** | MCP3008 讀值 **`soil == 0`、`light == 0`、`water_level == 0`** 視為異常（接線或感測器問題），同樣 **`HandleAbnormal(data)`**，**`return False`**。 |
| **資料有效** | 組好 `data` 並轉成 JSON 回傳，由主迴圈發送到 MQTT。 |

亦即：**先讀取所有感測器，再依「是否為 None / 0」決定是否視為異常並觸發防呆，且異常時不推送該筆資料。**

### 2.2 異常時強制關閉硬體 — HandleAbnormal()

**檔案：** `sensor/mqtt_for_sensor.py`

```python
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
        StorageExecuteMessage(True, error_message)
```

- **亮度異常**（`brightness` 為 None 或 0）：**`GPIO.output(light_pin, True)`**（HIGH），關燈，避免在無法感測環境光時持續開燈。
- **土壤或水位異常**：**`GPIO.output(motor_pin, True)`**（HIGH），關閉馬達，避免在感測異常時繼續澆水。
- 同時將異常內容寫入日誌（**`StorageExecuteMessage(True, ...)`**）。

因此：**感測器讀不到或為 0 時，除了不送資料外，還會主動把燈／馬達關掉並記錄錯誤。**

### 2.3 亮度回報的防呆 — LightData()

**檔案：** `sensor/mqtt_for_sensor.py`

```python
def LightData(light_sta):
    light = mcp.read_adc(0)
    convertResult = ConvertPercent(brightness=light)
    # ...
    if light == 0:
        HandleAbnormal(data)
        return False
    else:
        # 正常則組 JSON 並 return
```

亮度為 0 時同樣觸發 **`HandleAbnormal()`** 並回傳 **`False`**，呼叫端（如 **`LightPublisher()`**）就不會用無效資料發送 MQTT。

### 2.4 主迴圈對回傳值的防呆

**檔案：** `sensor/mqtt_for_sensor.py` — `DataPublisher()` 內

```python
while True:
    message_data = CollectSensorData()

    if message_data is not None and message_data is not False:
        send_result = sensor_pub.Publish(
            pub_topic='env/plant/detection/data',
            pub_message=message_data,
            # ...
        )
        # 成功則寫 access log，失敗則寫 error log
    else:
        message = "Invalid publish data is {}. . .".format(message_data)
        StorageExecuteMessage(True, message)
    time.sleep(5)
```

- **`message_data` 為 `None` 或 `False`**（感測異常）時，**不呼叫 Publish**，只寫入錯誤日誌，避免把無效資料送上 MQTT。
- 每輪固定 **`time.sleep(5)`**，下一輪再重試讀取。

### 2.5 MQTT 回呼的例外處理

**檔案：** `sensor/mqtt_for_sensor.py` — `SensorMqtt.on_message()`

```python
def on_message(self, client, userdata, message):
    try:
        decode_message = str(message.payload.decode("utf-8", "ignore"))
        receive_data = json.loads(decode_message)
        receive_topic = message.topic
        # ... 依 topic 改寫 GPIO、LightPublisher、__send_current_status ...
    except Exception as e:
        CatchError(e)
```

- **`CatchError(e)`** 會取得例外類型、訊息、檔案與行號，並寫入 **error 目錄下的 log 檔**（**`StorageExecuteMessage(True, errMsg)`**）。
- 如此可避免單一錯誤訊息導致整個 MQTT 回呼崩潰，訂閱執行緒可繼續接收下一則訊息。

### 2.6 image_recognition 的例外處理

**檔案：** `image_recognition/mqtt_for_image.py`

- **`on_message()`**：外層 **`try: ... except Exception as e: CatchError(e)`**，避免錯誤的 payload 或 JSON 解析導致訂閱中斷。
- **`DataPublisher()`**：**`while True`** 外層 **`try: ... except Exception as e: CatchError(e)`**，若 **`SaveImage()`** 或 MQTT 發送拋錯，會記錄後繼續下一輪（10 秒後再試），不會直接結束程式。

**website** 後端未直接讀取感測器，感測資料由 **sensor** 經 MQTT 傳至後端，防呆邏輯以 **sensor** 端為主。

---

## 三、效能部分：OpenCV 影像處理與感測器讀取的「異步」執行方式

本專案中 **OpenCV 影像處理** 與 **感測器讀取** 分別位於**不同裝置**（影像在 **image_recognition** Pi，感測器在 **sensor** Pi），兩者本來就是**不同行程**。在**單一程式內部**的「異步」則是以 **多執行緒 (threading)** 達成：**訂閱 MQTT 的迴圈** 與 **定期讀取感測／擷取影像的迴圈** 跑在**不同執行緒**，互不阻塞。

### 3.1 sensor：感測器讀取與 MQTT 訂閱並行

**檔案：** `sensor/mqtt_for_sensor.py`

```python
task_sub = threading.Thread(target=DataSubscriber)
task_pub = threading.Thread(target=DataPublisher)

if __name__ == '__main__':
    try:
        task_sub.start()
        task_pub.start()
        task_sub.join()
        task_pub.join()
    except KeyboardInterrupt:
        ForceStop()
```

- **DataSubscriber()**：建立 MQTT 客戶端並呼叫 **`sensor_sub.Connect(False)`**。在 **`sensor/module/mqtt_base.py`** 中，**`Connect(False)`** 會執行 **`self.__client.loop_forever()`**，該執行緒**阻塞**在 MQTT 迴圈，專門處理訂閱訊息（含 `on_message` 內對 GPIO 的改寫）。
- **DataPublisher()**：建立另一 MQTT 客戶端並呼叫 **`sensor_pub.Connect(True)`**。**`Connect(True)`** 會執行 **`self.__client.loop_start()`**，在**背景執行** MQTT 迴圈，**立即返回**；該執行緒接著進入 **`while True:`**，依序執行 **`CollectSensorData()`**（讀 DHT11、MCP3008）、**Publish**、**`time.sleep(5)`**。

因此：

- **訂閱執行緒**：只做 MQTT 收訊與 GPIO 控制，不負責週期性讀感測器。
- **發佈執行緒**：只做週期性感測器讀取與 MQTT 發送，不負責處理來自網頁的控制指令。

兩者並行，互不阻塞；收到網頁指令時，**訂閱執行緒** 的 **`on_message`** 會馬上改寫 GPIO，無需等感測器讀取週期結束。

### 3.2 image_recognition：OpenCV 影像處理與 MQTT 訂閱並行

**檔案：** `image_recognition/mqtt_for_image.py`

```python
task_sub = threading.Thread(target=DataSubscriber)
task_pub = threading.Thread(target=DataPublisher)

if __name__ == '__main__':
    try:
        task_sub.start()
        task_pub.start()
        task_sub.join()
        task_pub.join()
    except KeyboardInterrupt:
        ForceStop()
```

- **DataSubscriber()**：**`recognition_sub.Connect(False)`** → **`loop_forever()`**，該執行緒**阻塞**在 MQTT 訂閱迴圈，專門處理 **`on_message`**（例如 `manually/take/picture`、`response/monitor/message` 等）。
- **DataPublisher()**：**`recognition_pub.Connect(True)`** → **`loop_start()`**，該執行緒**不阻塞**，進入 **`while True:`**，每次執行 **`SaveImage()`**（內含 **`cv2.VideoCapture(0)`**、**`cap.read()`**、HSV 分析、寫檔）、再 Publish 影像與健康度，最後 **`time.sleep(10)`**。

因此：

- **訂閱執行緒**：只處理 MQTT 訊息（手動拍照、後端回覆等），不執行 OpenCV。
- **發佈執行緒**：只做週期性 **OpenCV 擷取與分析** 以及 MQTT 發送。

當使用者觸發「手動拍照」時，**訂閱執行緒** 的 **`on_message`** 會呼叫 **`ManuallyTakePicture()`**（內含一次 **`SaveImage()`**），與 **發佈執行緒** 的 10 秒週期**彼此獨立**；兩者可同時進行（例如訂閱執行緒正在處理手動拍照時，發佈執行緒仍可依自己的週期擷取），實作上即為 **OpenCV 影像處理與 MQTT 收發的並行執行**。

### 3.3 MQTT 連線模式的差異（mqtt_base.py）

**檔案：** `sensor/module/mqtt_base.py`、`image_recognition/module/mqtt_base.py`（邏輯相同）

```python
def Connect(self, mode=None):
    # ... 連線、設定 on_connect / on_message / on_disconnect ...
    if mode is not None:
      if mode == True:
        self.__client.loop_start()
      else:
        self.__client.loop_forever()
```

| 參數 | 方法 | 行為 |
|------|------|------|
| **Connect(True)** | `loop_start()` | 在背景開一條執行緒跑 MQTT 迴圈，**不阻塞**呼叫者；用於「發佈端」或需在同年執行緒做其他事（如感測迴圈、OpenCV 迴圈）。 |
| **Connect(False)** | `loop_forever()` | 在**目前執行緒**跑 MQTT 迴圈，**阻塞**直到斷線；用於「訂閱端」，該執行緒專職收訊息與回呼。 |

透過 **訂閱用 `Connect(False)`、發佈用 `Connect(True)`**，再搭配 **兩條 Python Thread**，就同時達成：

- 感測器端：**感測器定期讀取** 與 **網頁/MQTT 控制指令處理（含 GPIO）** 並行。
- 影像端：**OpenCV 定期擷取與上傳** 與 **手動拍照等 MQTT 指令處理** 並行。

### 3.4 小結（效能／異步）

| 項目 | 說明 |
|------|------|
| **異步實作方式** | 使用 **`threading.Thread`** 與 MQTT 的 **`loop_forever()` / `loop_start()`** 分工，**非** asyncio。 |
| **sensor** | 一執行緒：訂閱 + GPIO 控制；另一執行緒：每 5 秒讀感測器並發送；兩者並行。 |
| **image_recognition** | 一執行緒：訂閱 + 手動拍照等；另一執行緒：每 10 秒 OpenCV 擷取並發送；兩者並行。 |
| **跨裝置** | OpenCV（影像 Pi）與感測器讀取（感測 Pi）本來就是不同行程，自然並行。 |

---

## 四、彙總表

| 主題 | 關鍵檔案 | 關鍵程式碼／機制 |
|------|----------|------------------|
| **GPIO 高低電位** | `sensor/mqtt_for_sensor.py` | **`GPIO.output(pin, GPIO.HIGH)`** 關閉繼電器、**`GPIO.output(pin, GPIO.LOW)`** 開啟；燈 pin 18、馬達 pin 17；初始皆 **HIGH**。 |
| **感測器防呆** | `sensor/mqtt_for_sensor.py` | **DHT11**：`humidity/temperature is None` → **HandleAbnormal**、不推送；**MCP3008**：`light/soil/water_level == 0` → **HandleAbnormal**、不推送；**HandleAbnormal** 內依異常項目 **關燈／關馬達** 並寫 log。 |
| **主迴圈防呆** | `sensor/mqtt_for_sensor.py` | **`if message_data is not None and message_data is not False`** 才 Publish；否則只寫 error log。 |
| **MQTT 回呼防呆** | `sensor` / `image_recognition` | **`on_message`** 外層 **try / except → CatchError**，錯誤寫 log，不讓單一訊息錯誤中斷訂閱。 |
| **異步／並行** | `sensor`、`image_recognition` | **兩條 Thread**：訂閱端 **Connect(False)** → **loop_forever**；發佈端 **Connect(True)** → **loop_start** + **while True**（感測器讀取或 **SaveImage()**）+ **sleep**。 |

以上即為專案中與 **GPIO 控制**、**感測器例外處理** 以及 **OpenCV 與感測器讀取的異步執行** 相關的關鍵程式碼與行為彙整。
