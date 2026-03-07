# Flask API 與多執行緒 (Threading) 處理

本文件整理專案中 **Flask API** 與 **多執行緒** 的設計，重點說明：**影像辨識結果如何傳遞給後端與硬體控制端**，以及**如何確保影像運算不會影響即時硬體監控**。

---

## 一、Flask API 總覽

### 1.1 應用入口與 Blueprint 註冊

後端有**兩個 Flask 應用**，職責分離：

| 應用 | 入口 | 用途 |
|------|------|------|
| **主站 API** | `app/web/main.py` → `create_app()` | 提供 REST API（環境資料、圖表、繼電器、手動拍照、登入註冊等），供前端呼叫 |
| **MQTT 專用** | `app/data/mainMqtt.py` → `create_mqtt_app()` | 僅註冊 MQTT 相關 Blueprint，並在模組載入時啟動 **WebClient**（訂閱感測／影像主題）；通常以**獨立行程**（如 uWSGI serverMqtt）執行 |

主站 API 註冊的 Blueprint 如下（節錄自 `main.py`）：

```python
# === 檔案：website/server/project/backend/app/web/main.py ===

from tasks.mqtt.environment_detection import detection
from tasks.control.switch_relay import relay
from tasks.control.take_picture import take
from tasks.chart.analysis_data import analysis
from tasks.table.search_abnormal import search
from tasks.user.login import login
from tasks.user.register import register
from tasks.user.reset import reset

app.register_blueprint(detection)   # url_prefix='/env'
app.register_blueprint(relay)      # url_prefix='/relay'
app.register_blueprint(take)       # url_prefix='/manually'
app.register_blueprint(analysis)   # url_prefix='/chart'
app.register_blueprint(search)     # url_prefix='/abnormal'
app.register_blueprint(login)
app.register_blueprint(register)
app.register_blueprint(reset)
```

### 1.2 與硬體／影像相關的 API 路由

| 前綴 | 路由 | 方法 | 功能 | 與硬體／影像的關係 |
|------|------|------|------|--------------------|
| **/relay** | `/manually/open/light` | POST | 手動開／關燈 | 發佈 MQTT `switch/light` → 感測器 Pi 改寫 **GPIO 18** |
| **/relay** | `/manually/open/watering` | POST | 手動澆水 | 發佈 MQTT `switch/watering` → 感測器 Pi 改寫 **GPIO 17** |
| **/relay** | `/auto/control/switch` | POST | 切換自動／手動模式 | 發佈 MQTT `switch/auto/control` |
| **/relay** | `/read/control/mode` | GET | 讀取目前繼電器模式 | 從 DB 讀取，不直接碰硬體 |
| **/manually** | `/take/picture` | GET | 手動觸發拍照 | 發佈 MQTT `manually/take/picture` → **影像 Pi** 執行一次 **SaveImage()** 並上傳 |
| **/env** | `/data` | GET | 取得環境感測資料 | 從 DB 查詢（資料來源為 MQTT 收到的 `env/plant/detection/data`） |
| **/env** | `/plant/health/data` | GET | 取得植物健康度 | 從 DB 查詢（資料來源為 MQTT 收到的 `immediate/plant/health`） |
| **/chart** | `/data/average` | POST | 圖表分析 | 查 DB，與即時硬體無直接關聯 |
| **/abnormal** | `/data/table` | GET/POST | 異常資料表 | 查 DB |

**重點**：硬體控制（燈、馬達）與手動拍照**不直接操作 GPIO 或攝影機**，而是由 Flask 經 **MqttClient** 發佈到對應 MQTT 主題，由**感測器 Pi** 或 **影像 Pi** 的訂閱迴圈接收並執行。

---

## 二、影像辨識結果如何傳遞給後端與硬體控制端

### 2.1 資料流概觀

```
影像 Pi (image_recognition)
    │  SaveImage() → 原圖、辨識圖、健康度
    │  Publish: immediate/monitor/image, immediate/anatomy/image, immediate/plant/health
    ▼
MQTT Broker (Mosquitto)
    ▼
後端 MQTT 客戶端 (WebClient.__on_message)  ← 在獨立行程、且 MQTT 迴圈跑在背景執行緒
    │
    ├─ immediate/monitor/image  → 存檔 → response/monitor/message
    ├─ immediate/anatomy/image  → 存檔 → response/anatomy/message
    └─ immediate/plant/health   → 寫入 DB (Growing_data) + CollectGrowingData(health_status)（警報）
```

**硬體控制端**（感測器 Pi）的指令**不是**由影像辨識結果直接驅動，而是由**感測器資料**驅動：

```
感測器 Pi (sensor)
    │  CollectSensorData() → env/plant/detection/data
    ▼
後端 __on_message
    → CAD.CollectSensorData(receive_data)  // 門檻判斷
    → 若為自動模式：publish_data('operation/command', command)
    ▼
感測器 Pi 訂閱 operation/command
    → on_message() 改寫 GPIO 18 / 17（燈／馬達）
```

因此：

- **影像辨識結果**（原圖、辨識圖、健康度）傳遞到**後端**：經 MQTT 主題由 **WebClient** 接收，進行**存檔、寫入 DB、健康度門檻檢查與警報**。
- **硬體控制**（開關燈、馬達）的指令來自**感測器資料**（`env/plant/detection/data`）的門檻邏輯（`operation/command`），**非**直接由健康度主題下達；健康度目前用於**儲存、圖表與警報**（如 CollectGrowingData 觸發 OneSignal），若未來要依健康度驅動繼電器，只需在後端依 `immediate/plant/health` 產出並發送 `operation/command` 即可，感測器端介面不變。

### 2.2 後端接收影像與健康度的程式位置

```python
# === 檔案：website/.../mqtt_loop_connection.py，WebClient.__on_message ===

elif receive_topic == 'immediate/monitor/image':
    monitor_image = message.payload
    save_result = self.__HandleImage(..., rec_topic='response/monitor/message')
elif receive_topic == 'immediate/anatomy/image':
    monitor_image = message.payload
    save_result = self.__HandleImage(..., rec_topic='response/anatomy/message')
elif receive_topic == 'immediate/plant/health':
    receive_data = json.loads(decode_message)
    check_result = HandleData.check_data_repeatability_for_health(receive_data)
    if check_result == False:
        HandleData.insertion_health_status_data(receive_data)
    command = CAD.CollectGrowingData(receive_data['health_status'])  # 警報用，可擴充為下達硬體指令
```

影像 Pi 發佈的 **response/monitor/message**、**response/anatomy/message** 由後端在存檔後回傳，影像 Pi 的**訂閱執行緒**收到後可刪除本地暫存圖，完成一輪傳遞。

---

## 三、多執行緒 (Threading) 設計

### 3.1 後端：MQTT 迴圈在背景執行緒

MQTT 客戶端在**載入模組時**建立並啟動，**迴圈跑在獨立執行緒**，不阻塞主行程：

```python
# === 檔案：website/.../mqtt_loop_connection.py ===

if __name__ != '__main__':
    webMqtt = WebClient(client_id, subscribe_topics)
    webMqtt.start_connect()
    webMqtt.start_loop()

# start_loop 實作：
def start_loop(self, timeout=None):
    thread = threading.Thread(target=self.__loop, args=(timeout,))
    thread.start()

def __loop(self, timeout=None):
    if not timeout:
        self.__client.loop_forever()
    else:
        self.__client.loop(timeout)
```

因此，**MQTT 訂閱與訊息處理**（含影像存檔、健康度寫 DB、感測器門檻與 operation/command）發生在**背景執行緒**；若 MQTT 應用與主站 API 以**不同 uWSGI 行程**運行，則 REST 請求與 MQTT 迴圈在**不同行程**，彼此不阻塞。

### 3.2 影像 Pi (image_recognition)：雙執行緒分離「影像運算」與「MQTT 收訊」

| 執行緒 | 進入點 | MQTT 模式 | 工作內容 |
|--------|--------|-----------|----------|
| **task_sub** | `DataSubscriber()` | `Connect(False)` → **loop_forever()**（阻塞） | 僅負責訂閱與 **on_message**：手動拍照、response 回覆、燈狀態等 |
| **task_pub** | `DataPublisher()` | `Connect(True)` → **loop_start()**（非阻塞） | **SaveImage()**（攝影機 + OpenCV 運算）+ 發佈影像與健康度，每 10 秒一輪 |

```python
# === 檔案：image_recognition/mqtt_for_image.py ===

task_sub = threading.Thread(target=DataSubscriber)
task_pub = threading.Thread(target=DataPublisher)

if __name__ == '__main__':
    task_sub.start()
    task_pub.start()
    task_sub.join()
    task_pub.join()
```

**SaveImage()** 內含 **cv2.VideoCapture(0)**、讀幀、HSV 分析、健康度計算與寫檔，屬於**較耗時運算**；若與訂閱放在同一執行緒，則在執行 SaveImage 期間無法處理 **manually/take/picture** 或 **response/***。  
透過**訂閱專用執行緒**（task_sub）與**發佈＋影像運算專用執行緒**（task_pub）分離：

- **即時性**：收到「手動拍照」或後端回覆時，**task_sub** 可立即處理，**不受 task_pub 的 SaveImage 週期影響**。
- **影像運算不阻塞 MQTT 收訊**：**task_pub** 的 **while True** 內執行 SaveImage 與 sleep(10)，不會卡住 **task_sub** 的 **loop_forever()**。

### 3.3 感測器 Pi (sensor)：雙執行緒分離「感測器讀取」與「硬體控制」

| 執行緒 | 進入點 | MQTT 模式 | 工作內容 |
|--------|--------|-----------|----------|
| **task_sub** | `DataSubscriber()` | `Connect(False)` → **loop_forever()**（阻塞） | 訂閱 **switch/light**、**switch/watering**、**operation/command**、**switch/auto/control**；**on_message** 內直接 **GPIO.output()**，即時控制燈與馬達 |
| **task_pub** | `DataPublisher()` | `Connect(True)` → **loop_start()**（非阻塞） | **CollectSensorData()**（DHT11 + MCP3008）+ 發佈 **env/plant/detection/data**，每 5 秒一輪 |

```python
# === 檔案：sensor/mqtt_for_sensor.py ===

task_sub = threading.Thread(target=DataSubscriber)
task_pub = threading.Thread(target=DataPublisher)

if __name__ == '__main__':
    task_sub.start()
    task_pub.start()
    task_sub.join()
    task_pub.join()
```

**即時硬體監控**依賴 **task_sub** 的 **on_message**：使用者在網頁按開燈／澆水，或後端發出 **operation/command**，皆須**即時**改寫 GPIO。若與 **CollectSensorData()** 放在同一執行緒，則在讀取感測器或 **time.sleep(5)** 期間會延遲執行控制指令。  
透過**訂閱專用執行緒**處理所有控制主題、**發佈專用執行緒**只做感測器採樣與上報：

- **硬體控制即時**：**task_sub** 專職收 MQTT 並改寫 GPIO，**不受 task_pub 的 5 秒採樣週期影響**。
- **感測器讀取不阻塞控制**：**task_pub** 的 **while True** 與 **time.sleep(5)** 不會卡住 **on_message**。

---

## 四、如何確保影像運算不影響即時硬體監控

### 4.1 裝置與職責分離

| 裝置 | 影像運算 | 硬體監控（GPIO） |
|------|----------|------------------|
| **影像 Pi** | 有（SaveImage、OpenCV） | 無（不操作 GPIO） |
| **感測器 Pi** | 無 | 有（燈、馬達、感測器讀取） |

影像辨識與硬體控制在**不同 Raspberry Pi** 上執行，**CPU 與程序彼此獨立**，因此**影像 Pi 上的 OpenCV 運算不會佔用感測器 Pi 的 CPU**，也不會阻塞感測器 Pi 的訂閱迴圈。

### 4.2 影像 Pi 內部：訂閱與發佈／運算分線程

- **task_sub**：只跑 **loop_forever()**，處理 **manually/take/picture**、**response/monitor|anatomy/message**、**receive/sensor/light/status**。
- **task_pub**：跑 **while True**，每次 **SaveImage()** 後 **time.sleep(10)**。

因此：

- **影像運算**（SaveImage）只在 **task_pub** 執行，**不會阻塞 task_sub**。
- **即時硬體監控**在**感測器 Pi** 上，由 **task_sub** 的 **on_message** 處理；影像 Pi 的運算與感測器 Pi 的執行緒**完全分離**。

### 4.3 感測器 Pi 內部：控制與採樣分線程

- **task_sub**：只處理控制類主題並改寫 GPIO，不執行 **CollectSensorData()** 或 **time.sleep(5)**。
- **task_pub**：只執行感測器讀取與 MQTT 發送，不處理 **switch/light**、**operation/command** 等。

因此，**即時硬體監控**（收到指令立即改寫 GPIO）不會被感測器讀取或 5 秒 sleep 拖慢。

### 4.4 小結

| 目標 | 作法 |
|------|------|
| 影像運算不影響硬體監控 | 影像 Pi 與感測器 Pi **分機**；影像 Pi 上 **SaveImage** 只在 **task_pub**，**task_sub** 專職收 MQTT，兩者**分線程**。 |
| 硬體控制即時 | 感測器 Pi **task_sub** 專職訂閱並執行 **GPIO.output**，**task_pub** 只做感測器採樣與上報，**分線程**。 |
| 後端不阻塞 | MQTT 迴圈以 **threading.Thread** 跑 **loop_forever()**，與 Flask 主線程（或另一 uWSGI 行程）分離。 |

---

## 五、Flask 觸發硬體／影像的程式碼範例

### 5.1 手動開燈（發佈 MQTT，由感測器 Pi 執行 GPIO）

```python
# === 檔案：website/.../tasks/control/switch_relay.py ===

@relay.route('/manually/open/light', methods=['POST'])
def change_light():
    mode = request.get_json()['mode']
    command = {'light_status': mode}
    data = json.dumps(command)
    with MqttClient('open_light') as client:
        client.publish('switch/light', data, 2, False)
    return jsonify({...})
```

### 5.2 手動拍照（發佈 MQTT，由影像 Pi 執行 SaveImage）

```python
# === 檔案：website/.../tasks/control/take_picture.py ===

@take.route('/take/picture', methods=['GET'])
def manually_take_picture():
    command = {'manually_take_picture': True}
    data = json.dumps(command)
    with MqttClient('take_picture') as client:
        client.publish('manually/take/picture', data, 2, False)
    return jsonify({'manually_take_picture': True})
```

### 5.3 後端 MQTT 迴圈啟動（背景執行緒）

```python
# === 檔案：website/.../mqtt_loop_connection.py ===

if __name__ != '__main__':
    webMqtt = WebClient(client_id, subscribe_topics)
    webMqtt.start_connect()
    webMqtt.start_loop()  # 內部：threading.Thread(target=self.__loop).start()
```

---

## 六、彙總表

| 項目 | 說明 |
|------|------|
| **Flask API** | 主站 `create_app()` 註冊多個 Blueprint（/env, /relay, /manually, /chart, /abnormal, 登入註冊等）；硬體與手動拍照經 **MqttClient** 發佈至 MQTT，由 Pi 端執行。 |
| **影像辨識結果傳遞** | 影像 Pi 發佈 **immediate/monitor/image**、**immediate/anatomy/image**、**immediate/plant/health** → 後端 **WebClient.__on_message** 存檔、寫 DB、健康度門檻與警報；硬體控制由 **env/plant/detection/data** → **operation/command** 驅動感測器 Pi。 |
| **多執行緒** | 後端：**WebClient** 以 **threading.Thread** 跑 **loop_forever()**；影像 Pi：**task_sub**（訂閱）＋**task_pub**（SaveImage＋發佈）；感測器 Pi：**task_sub**（訂閱＋GPIO）＋**task_pub**（感測器＋發佈）。 |
| **影像運算不影響硬體監控** | 影像與硬體分機；影像 Pi 上 SaveImage 與 MQTT 訂閱分線程；感測器 Pi 上 GPIO 控制與感測器採樣分線程。 |