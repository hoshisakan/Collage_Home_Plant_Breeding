# 軟硬體控制邏輯 — 程式與功能對照 (Code Function Mapping)

本文件依 **image_recognition**、**sensor**、**website** 三模組之原始碼整理，供硬體主管快速對照：**主要 Python 檔案與硬體組件之對應**、**初始化與異常處理邏輯**、**併發設計**，以及**長時間運作穩定性**之實作要點。全文以繁體中文撰寫，聚焦工程邏輯與可追溯之程式位置。

---

## 一、模組化功能對照表

### 1.1 sensor 模組（感測器端 Raspberry Pi）

| 主要 Python 檔案 | 負責的硬體組件 | 核心功能 |
|------------------|----------------|----------|
| **mqtt_for_sensor.py** | **GPIO 輸出**：BCM 17（馬達繼電器）、BCM 18（燈光繼電器）<br/>**GPIO 輸入／感測**：BCM 4（DHT11 溫溼度）<br/>**SPI**：MCP3008 ADC（CH0 亮度、CH1 土壤、CH2 水位） | 訂閱 MQTT 控制主題（switch/light、switch/watering、operation/command、switch/auto/control），依指令改寫 GPIO 驅動繼電器；定時讀取 DHT11 與 MCP3008，經 MQTT 上報；感測值異常時呼叫 HandleAbnormal 關閉繼電器並寫 log |
| **module/mqtt_base.py** | 無直接硬體 | MQTT 連線、訂閱／發佈、TLS 設定之基底類別 |
| **module/config.py** | 無直接硬體 | Broker 位址、埠、帳密等連線參數 |

**硬體對應摘要**：**Relay** 由 GPIO 17、18 透過 **GPIO.output(pin, HIGH/LOW)** 控制；**Sensors** 為 DHT11（單線）與 MCP3008（SPI），讀取結果用於上報與異常判定。

### 1.2 image_recognition 模組（影像端 Raspberry Pi）

| 主要 Python 檔案 | 負責的硬體組件 | 核心功能 |
|------------------|----------------|----------|
| **mqtt_for_image.py** | **攝影機**（OpenCV `VideoCapture(0)`）<br/>不操作 RPi.GPIO | 定時或收到手動拍照指令時擷取影像、HSV 分析計算健康度，發佈原圖／辨識圖／健康度至 MQTT；訂閱 response、手動拍照、燈狀態等主題；雙執行緒分離「訂閱」與「擷取＋發佈」 |
| **module/mqtt_base.py** | 無直接硬體 | MQTT 連線與發佈之基底類別 |
| **module/config.py** | 無直接硬體 | Broker 連線參數 |

**硬體對應摘要**：本模組**僅操作攝影機**，無 GPIO 或 Relay；若需開燈拍照，可經 MQTT 發送 `switch/light` 至感測器端，由 sensor 模組驅動繼電器。

### 1.3 website 模組（後端伺服器）

| 主要 Python 檔案 | 負責的硬體組件 | 核心功能 |
|------------------|----------------|----------|
| **app/web/main.py** | 無直接硬體 | Flask 主站應用建立、Blueprint 註冊（環境、繼電器、手動拍照、圖表、異常、使用者） |
| **app/data/mainMqtt.py** | 無直接硬體 | MQTT 專用 Flask 應用、載入時啟動 WebClient（訂閱感測／影像主題） |
| **app/tasks/control/switch_relay.py** | 間接：經 MQTT 控制感測器 Pi 之 Relay | REST API：手動開關燈、手動澆水、切換自動模式；以 MqttClient 發佈 switch/light、switch/watering、switch/auto/control |
| **app/tasks/control/take_picture.py** | 間接：經 MQTT 觸發影像 Pi 之攝影機 | REST API：手動拍照；發佈 manually/take/picture |
| **app/tasks/control/mqtt_single_connection.py** | 無直接硬體 | 單次連線用之 MQTT 客戶端（Context Manager），供 relay、take_picture 發佈 |
| **app/tasks/mqtt/mqtt_loop_connection.py** | 無直接硬體 | WebClient：訂閱感測資料、影像、健康度、繼電器模式；收訊後寫 DB、門檻判斷、發送 operation/command（自動模式時） |
| **app/tasks/mqtt/check_abnormal_data.py** | 無直接硬體 | 感測器／健康度門檻判斷、產生開關燈／馬達指令、OneSignal 警報 |

**硬體對應摘要**：後端**不直接驅動 GPIO 或感測器**，僅透過 **MQTT** 下達控制指令或觸發拍照；實際 **Relay** 與 **Sensors** 由 **sensor** 模組在裝置端執行。

---

## 二、核心邏輯解析

### 2.1 初始化流程：程式啟動時如何對應硬體狀態

#### sensor 模組（唯一直接操作 GPIO／感測器的模組）

初始化在**模組載入時**執行（無額外 `main()` 前段），順序如下：

| 步驟 | 程式位置 | 行為說明 |
|------|----------|----------|
| 1 | `mqtt_for_sensor.py` 約第 17–18 行 | **GPIO.setmode(GPIO.BCM)**、**GPIO.setwarnings(False)**：設定 BCM 腳位編號，避免重複設定警告 |
| 2 | 約第 19–21 行 | **SPI / MCP3008**：`SPI_PORT=0`, `SPI_DEVICE=0`，建立 **Adafruit_MCP3008.MCP3008** 實例，用於後續 read_adc(0/1/2) |
| 3 | 約第 22–24 行 | **繼電器腳位**：`motor_pin=17`、`light_pin=18`；**GPIO.setup(..., GPIO.OUT, initial=GPIO.HIGH)**：輸出模式，**預設 HIGH（繼電器不導通）**，確保上電或啟動時燈與馬達皆為關閉 |
| 4 | 約第 25–33 行 | 全域變數（計數、自動／手動模式旗標）初始化 |
| 5 | `__main__` | 建立 **task_sub**（DataSubscriber）、**task_pub**（DataPublisher）兩條執行緒並 start；**未**在啟動時主動讀取感測器做「硬體存在與否」檢測，異常判定改在**週期性 CollectSensorData()** 與 **LightData()** 中處理 |

**設計要點**：以 **initial=GPIO.HIGH** 作為安全預設，與後續 **HandleAbnormal**、**ForceStop** 的「關閉繼電器」語意一致；DHT11 無模組頂層初始化，在 **CollectSensorData()** 內以 **Adafruit_DHT.read_retry(DHT11, 4)** 指定 GPIO 4 讀取。

#### image_recognition 模組

- **無 GPIO 或 Relay 初始化**。
- 攝影機在 **SaveImage()** 內以 **cv2.VideoCapture(0)** 按次開啟、擷取後 release，不在模組載入時佔用。
- 執行緒在 **__main__** 啟動：**task_sub**（DataSubscriber）、**task_pub**（DataPublisher）。

#### website 模組

- 無硬體介面；**create_app()** 載入設定與 Blueprint；MQTT 應用在 **create_mqtt_app()** 載入時建立 WebClient 並以 **threading.Thread** 啟動 **loop_forever()**。

---

### 2.2 異常處理 (Edge Case)：感測器讀值為 0 或 Null 時，立即關閉繼電器

以下段落為**感測器讀值異常時，立即關閉繼電器**之核心邏輯，便於硬體主管對照程式位置。

#### （1）觸發條件：何時視為異常

**檔案：** `sensor/mqtt_for_sensor.py`

- **CollectSensorData()** 內（約第 399–405 行）：
  - **DHT11**：`humidity is None or temperature is None` → 視為讀取失敗。
  - **MCP3008**：`soil == 0 or light == 0 or water_level == 0` → 視為接線或感測異常（ADC 0 通常表示通道異常）。
- **LightData()** 內（約第 323–325 行）：**light == 0**（亮度通道異常）時同樣觸發異常處理。

#### （2）立即關閉繼電器之程式碼段落：HandleAbnormal

**檔案：** `sensor/mqtt_for_sensor.py`，約第 **219–234** 行。

```python
def HandleAbnormal(abnormal=None):
    if abnormal is not None:
        abnormal_message = {}
        for key, value in abnormal.items():
            if value is None or value == 0:
                temp_message = value
                abnormal_message[key] = temp_message
                if key == 'brightness':
                  GPIO.output(light_pin, True)   # 亮度異常 → 立即關燈（HIGH = 繼電器關閉）
                elif key == 'soil' or key == 'water_level':
                  GPIO.output(motor_pin, True)   # 土壤／水位異常 → 立即關馬達
        abnormal_message['date'] = abnormal['date']
        error_message = '異常訊息:\n{}'.format(abnormal_message)
        StorageExecuteMessage(True, error_message)  # 寫入 error log，可追溯
```

**對應關係**：

- **brightness** 為 **None** 或 **0**：無法可靠判斷環境光 → **GPIO.output(light_pin, True)**，關閉燈光繼電器。
- **soil** 或 **water_level** 為 **None** 或 **0**：無法可靠判斷土壤或水位 → **GPIO.output(motor_pin, True)**，關閉馬達繼電器。
- 所有異常皆寫入 **error** 目錄 log，不丟棄紀錄。

#### （3）主迴圈不推送無效資料（避免錯誤資料驅動後端決策）

**檔案：** `sensor/mqtt_for_sensor.py`，**DataPublisher()** 內約第 424–450 行。

當 **CollectSensorData()** 因上述條件回傳 **None** 或 **False** 時：

- **不呼叫 Publish**，該筆資料不送往後端。
- 僅執行 **StorageExecuteMessage(True, message)** 寫入 error log。
- 下一輪 **time.sleep(5)** 後再次讀取，形成重試。

#### （4）程式結束時強制關閉繼電器：ForceStop

**檔案：** `sensor/mqtt_for_sensor.py`，約第 **206–217** 行。

```python
def ForceStop():
    global sensor_sub, sensor_pub
    GPIO.output(light_pin, True)
    GPIO.output(motor_pin, True)
    sensor_sub.Disconnect()
    sensor_pub.Disconnect()
    os._exit(0)
```

無論正常結束或 **KeyboardInterrupt**，離開前先將**燈與馬達皆設為關閉**，再斷線、結束程序，避免程式結束後繼電器仍導通。

---

### 2.3 併發處理：Threading 如何分開影像分析與硬體 I/O

#### （1）架構原則

- **影像分析**（OpenCV 擷取、HSV 計算、寫檔）與 **硬體 I/O**（GPIO、感測器讀取）分別位於**不同裝置**：影像在 **image_recognition Pi**，硬體在 **sensor Pi**，因此**不同行程**，CPU 與記憶體隔離。
- 在**單一裝置內**，以 **threading** 分離「**訂閱 MQTT（即時反應）**」與「**週期性採樣／影像運算＋發佈**」，避免耗時迴圈阻塞控制指令的處理。

#### （2）sensor 模組：硬體 I/O 與控制指令分線程

**檔案：** `sensor/mqtt_for_sensor.py`，約第 455–472 行。

| 執行緒 | 進入點 | MQTT 行為 | 工作內容 |
|--------|--------|-----------|----------|
| **task_sub** | DataSubscriber() | **Connect(False)** → **loop_forever()**（阻塞） | 專職訂閱 **switch/light**、**switch/watering**、**operation/command**、**switch/auto/control**；**on_message** 內直接 **GPIO.output()** 改寫燈與馬達，即時回應網頁或後端指令 |
| **task_pub** | DataPublisher() | **Connect(True)** → **loop_start()**（非阻塞） | **while True**：**CollectSensorData()**（DHT11 + MCP3008）→ 有效則 Publish(**env/plant/detection/data**)，**time.sleep(5)** |

因此：**硬體控制（GPIO 改寫）** 與 **感測器讀取（含可能觸發 HandleAbnormal 的邏輯）** 分屬不同執行緒；即使 CollectSensorData 或 sleep(5) 執行中，**on_message** 仍可即時處理開關燈／馬達指令。

#### （3）image_recognition 模組：影像分析與 MQTT 收訊分線程

**檔案：** `image_recognition/mqtt_for_image.py`，約第 528–544 行。

| 執行緒 | 進入點 | MQTT 行為 | 工作內容 |
|--------|--------|-----------|----------|
| **task_sub** | DataSubscriber() | **Connect(False)** → **loop_forever()**（阻塞） | 專職訂閱 **response/monitor|anatomy/message**、**manually/take/picture**、**receive/sensor/light/status**；收到手動拍照即觸發 **ManuallyTakePicture()** |
| **task_pub** | DataPublisher() | **Connect(True)** → **loop_start()**（非阻塞） | **while True**：**SaveImage()**（攝影機＋OpenCV＋健康度計算）→ Publish 原圖／辨識圖／健康度，**time.sleep(10)** |

因此：**影像分析（SaveImage）** 僅在 **task_pub** 執行，**不會阻塞 task_sub**；使用者觸發手動拍照或後端回覆存檔結果時，訂閱端可立即處理，無需等待 SaveImage 或 sleep(10) 結束。

#### （4）後端 MQTT 迴圈

**檔案：** `website/.../mqtt_loop_connection.py`。

WebClient 以 **threading.Thread(target=self.__loop).start()** 執行 **loop_forever()**，MQTT 收訊與處理（含影像存檔、DB 寫入、門檻判斷、operation/command 發送）在**背景執行緒**進行，不阻塞主站 REST 或 MQTT 應用之其他邏輯。

---

## 三、關鍵技術亮點：長時間運作 (Long-run) 穩定性

以下總結本專案如何透過設計與實作，確保系統在**長時間運作**下維持穩定、可預期之行為。

| 面向 | 實作方式 |
|------|----------|
| **硬體安全預設** | 初始化與結束時繼電器皆為 **HIGH（關閉）**；感測器讀值 **0 或 Null** 時 **HandleAbnormal** 立即關閉對應繼電器，並寫 error log，避免在不可靠狀態下持續驅動。 |
| **無效資料不進入控制鏈** | **CollectSensorData()** 異常時 **return None/False**，主迴圈**不 Publish** 該筆資料，後端與自動控制不會依無效感測值下達指令；下一輪再重試讀取。 |
| **單一錯誤不導致程序崩潰** | **on_message**、**DataPublisher**、**DataSubscriber**、**CurrentModePublisher**（sensor）及後端 **__on_message**、**CollectSensorData**（check_abnormal_data）等外層皆以 **try/except** 捕獲例外，並呼叫 **CatchError** 或 **__HandleError** **僅寫入 log、不 re-raise**，因此單一 MQTT 訊息錯誤或單筆感測異常不會中斷 MQTT 迴圈或結束程序。 |
| **併發隔離** | 訂閱與發佈分線程、分裝置（影像 Pi vs 感測器 Pi），**影像運算不佔用感測器 Pi**，**控制指令不因感測器採樣或影像擷取延遲**；後端 MQTT 迴圈在獨立執行緒，與 REST 或其他邏輯分離。 |
| **可追溯性** | 異常與存取訊息寫入 **error**／**access** 目錄之 log 檔（**StorageExecuteMessage**、**WriteException**），便於事後分析與除錯。 |
| **結束時狀態一致** | **ForceStop()** 在程式結束（含 KeyboardInterrupt）前強制 **GPIO.output(light_pin, True)**、**GPIO.output(motor_pin, True)**，再斷線、退出，避免留下「程式已關閉但繼電器仍導通」之狀態。 |

整體而言：透過**安全預設、異常即關閉繼電器、不推送無效資料、例外僅記錄不拋出、訂閱／發佈與裝置分離、log 與結束時清理**，在長期運行下兼顧硬體安全與程式穩定。

---

## 四、對照索引（檔案與行號參考）

| 邏輯項目 | 檔案 | 約略行號 |
|----------|------|----------|
| GPIO / SPI 初始化 | sensor/mqtt_for_sensor.py | 17–24 |
| 感測器讀取與 Null／0 判定 | sensor/mqtt_for_sensor.py | 372–409（CollectSensorData）、314–325（LightData） |
| 異常時立即關閉繼電器 | sensor/mqtt_for_sensor.py | 219–234（HandleAbnormal） |
| 主迴圈不推送無效資料 | sensor/mqtt_for_sensor.py | 424–450（DataPublisher 內 while） |
| 結束時關閉繼電器 | sensor/mqtt_for_sensor.py | 206–217（ForceStop） |
| 感測器端雙執行緒 | sensor/mqtt_for_sensor.py | 455–472（task_sub / task_pub 與 __main__） |
| 影像端雙執行緒 | image_recognition/mqtt_for_image.py | 528–544（task_sub / task_pub 與 __main__） |
| 後端 MQTT 與控制 API | website/.../mqtt_loop_connection.py、switch_relay.py、take_picture.py | 見各檔 |

以上內容皆可依模組與檔案路徑於專案原始碼中對照查閱。
