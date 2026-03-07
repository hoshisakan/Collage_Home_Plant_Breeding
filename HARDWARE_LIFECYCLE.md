# 硬體控制腳本程式生命週期 (Life Cycle)

本文件針對專案中 **website**、**sensor**、**image_recognition** 三個模組裡，負責控制硬體（Relay、Sensors、攝影機）的 Python 腳本，整理其程式生命週期，包含：**初始化 (Initialization)**、**主迴圈 (Main Loop)**，以及**收到網頁／MQTT 指令時如何觸發硬體動作或改寫電位**。

---

## 一、概覽：誰直接控制硬體？

| 模組 | 腳本 | 直接控制的硬體 | 說明 |
|------|------|----------------|------|
| **sensor** | `mqtt_for_sensor.py` | GPIO 輸出（繼電器）、DHT11、MCP3008 | 唯一在實體腳位上設定 GPIO、讀取感測器的腳本 |
| **image_recognition** | `mqtt_for_image.py` | 攝影機（OpenCV VideoCapture） | 不操作 RPi.GPIO；可經 MQTT 發送開燈指令給 sensor 端 |
| **website** | 無常駐於裝置上的硬體腳本 | — | 後端僅提供 REST API 並發佈 MQTT；網頁指令經 MQTT 由 **sensor** 端接收並驅動 GPIO |

以下依 **sensor**、**image_recognition**、**website** 順序說明生命週期；其中「收到網頁指令」的完整路徑為：**瀏覽器 → Flask API → MQTT Broker → sensor / image_recognition 的 `on_message`**。

---

## 二、sensor — `mqtt_for_sensor.py`

此腳本在 **感測器端 Raspberry Pi** 上執行，直接控制 **GPIO 繼電器** 與 **感測器**，並透過 MQTT 與後端通訊。

### 2.1 初始化 (Initialization)

初始化在**模組載入時**即執行（無額外 `main()` 前段），順序如下。

#### （1）GPIO 模式與腳位設定

| 步驟 | 程式碼位置 | 說明 |
|------|------------|------|
| 設定 GPIO 編號模式 | `GPIO.setmode(GPIO.BCM)` | 使用 BCM 腳位編號（如 17、18） |
| 關閉 GPIO 警告 | `GPIO.setwarnings(False)` | 避免重複設定腳位時出現警告 |
| 馬達繼電器腳位 | `motor_pin = 17` | BCM 17，對應澆水馬達繼電器 |
| 燈光繼電器腳位 | `light_pin = 18` | BCM 18，對應燈光繼電器 |
| 設定為輸出、預設關閉 | `GPIO.setup(motor_pin, GPIO.OUT, initial=GPIO.HIGH)`<br/>`GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.HIGH)` | 輸出模式；`HIGH` = 繼電器關閉（安全預設） |

亦即：**初始化階段** 已將 **GPIO 17、18 設為輸出 (OUT)**，並設為 **HIGH**，不驅動繼電器。

#### （2）類比感測（MCP3008）與溫溼度（DHT11）

| 硬體 | 程式碼 | 說明 |
|------|--------|------|
| MCP3008 ADC（SPI） | `SPI_PORT = 0`, `SPI_DEVICE = 0`<br/>`mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))` | 初始化 SPI，用於讀取類比感測（光線、土壤、水位） |
| DHT11 | 無在模組頂層初始化 | 在 `CollectSensorData()` 內以 `Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)` 讀取，GPIO 4 為資料腳位 |

#### （3）全域狀態變數

- `auto_control_light`、`open_auto_control`、`open_manually_light_control`、`open_manually_motor_control` 等，用於記錄目前為自動或手動模式，供 `on_message` 判斷是否執行後端下達的自動控制。

#### （4）程式進入點與執行緒

- `if __name__ == '__main__':` 時建立兩條執行緒並啟動：
  - **task_sub**：`DataSubscriber()` → 建立 MQTT 訂閱端，呼叫 `sensor_sub.Connect(False)` → **blocking** `loop_forever()`，持續等待 MQTT 訊息。
  - **task_pub**：`DataPublisher()` → 建立 MQTT 發佈端，呼叫 `sensor_pub.Connect(True)`（非阻塞 `loop_start()`），然後進入**主迴圈**（見下）。

---

### 2.2 主迴圈 (Main Loop) — 定期讀取感測器

- **實際主迴圈**位於 **`DataPublisher()`** 內，以 **`while True:`** 無限迴圈執行。
- 每次迴圈流程：
  1. 呼叫 **`CollectSensorData()`** 讀取所有感測器：
     - **DHT11**（GPIO 4）：`Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)` → 溫度、濕度。
     - **MCP3008**：`mcp.read_adc(0)` 亮度、`mcp.read_adc(1)` 土壤濕度、`mcp.read_adc(2)` 水位。
  2. 將原始 ADC 值以 **`ConvertPercent()`** 轉成百分比（0–1023 → 0–100）。
  3. 若資料有效（非 `None` 且非 0 異常），則以 **`sensor_pub.Publish()`** 發送到 MQTT 主題 **`env/plant/detection/data`**。
  4. 若偵測到異常（如 `humidity is None` 或 `soil == 0` 等），則呼叫 **`HandleAbnormal()`**（會**強制關閉燈/馬達 GPIO**，見 2.3）。
  5. **`time.sleep(5)`** → **每 5 秒** 執行一輪。

因此：**主迴圈以 5 秒為週期，定期讀取 DHT11 與 MCP3008，並將結果經 MQTT 上傳。**

---

### 2.3 收到網頁／MQTT 指令時 — 觸發硬體中斷或改寫電位

網頁操作（開關燈、澆水、自動模式）會先打到 **website 後端 Flask API**，後端再**發佈 MQTT**；感測器端 **訂閱端** 的 **`SensorMqtt.on_message()`** 收到訊息後，**直接改寫 GPIO 輸出電位**，並依需求驅動繼電器。

訂閱主題與對應硬體行為如下。

#### （1）`operation/command`（後端自動控制）

- **條件**：`open_auto_control is True`（目前為自動模式）。
- **內容**：
  - `switch_light_state: True/False` → 設定 `__light_current_status = GPIO.LOW / GPIO.HIGH`，並執行 **`GPIO.output(light_pin, self.__light_current_status)`**（改寫 **GPIO 18** 電位）。
  - 澆水指令 `True` → **`GPIO.output(motor_pin, GPIO.LOW)`** 開啟馬達，**`time.sleep(5)`** 後 **`GPIO.output(motor_pin, GPIO.HIGH)`** 關閉（**GPIO 17**）。
- 執行後呼叫 **`LightPublisher()`**（讀取 MCP3008 CH0 亮度並發佈到 `receive/sensor/light/status`），並以 **`__send_current_status()`** 發佈目前模式到 **`realy/current/mode`**。

#### （2）`switch/light`（手動開／關燈）

- 先將 **`open_auto_control = False`**（改為手動模式）。
- `light_status: True` → **`GPIO.output(light_pin, GPIO.LOW)`**（開燈）；  
  `light_status: False` → **`GPIO.output(light_pin, GPIO.HIGH)`**（關燈）。
- 同樣會呼叫 **`LightPublisher()`** 與 **`__send_current_status()`**。

#### （3）`switch/watering`（手動澆水）

- `watering_status: True` → **`GPIO.output(motor_pin, GPIO.LOW)`**，**`time.sleep(5)`** 後 **`GPIO.output(motor_pin, GPIO.HIGH)`**；  
  `False` → 僅設為 **`GPIO.HIGH`** 關閉馬達。
- 同樣會 **`__send_current_status()`**。

#### （4）`switch/auto/control`（切換自動／手動模式）

- 僅更新 **`open_auto_control`** 等狀態變數，**不在此處改寫 GPIO**；後續由 **`operation/command`** 或 **`switch/light`** / **`switch/watering`** 再驅動硬體。

#### （5）異常時強制關閉硬體 — `HandleAbnormal()`

- 在 **主迴圈** 的 **`CollectSensorData()`** 或 **`LightData()`** 中，若偵測到異常（如 `brightness == 0`、`soil == 0`、`water_level == 0`），會呼叫 **`HandleAbnormal()`**。
- 其中會執行：
  - **`GPIO.output(light_pin, True)`**（關燈）；
  - **`GPIO.output(motor_pin, True)`**（關馬達）。
- 亦即：**異常時會中斷當前繼電器狀態，強制將燈與馬達關閉。**

#### （6）程式結束 — `ForceStop()`

- 鍵盤中斷（Ctrl+C）時呼叫 **`ForceStop()`**：
  - **`GPIO.output(light_pin, True)`**、**`GPIO.output(motor_pin, True)`**，確保關閉繼電器；
  - 中斷 MQTT 連線並 **`os._exit(0)`**。

---

### 2.4 生命週期流程簡圖（sensor）

```
模組載入
  → GPIO.setmode(BCM)、setwarnings(False)
  → GPIO.setup(17, OUT, HIGH)、GPIO.setup(18, OUT, HIGH)
  → MCP3008 初始化（SPI）
  → 全域變數初始化
  ↓
__main__：啟動 task_sub（訂閱）、task_pub（發佈 + 主迴圈）
  ↓
┌─ task_sub：loop_forever() 等待 MQTT
│     → on_message() 收到 switch/light、switch/watering、operation/command、switch/auto/control
│     → 依主題改寫 GPIO 17/18 電位（LOW=開啟繼電器，HIGH=關閉）
│     → 必要時 LightPublisher()、__send_current_status()
│
└─ task_pub：while True
      → CollectSensorData()（DHT11 + MCP3008）
      → 異常則 HandleAbnormal() → GPIO 17/18 設 HIGH
      → Publish(env/plant/detection/data)
      → time.sleep(5)
```

---

## 三、image_recognition — `mqtt_for_image.py`

此腳本在 **影像辨識端 Raspberry Pi** 上執行，控制的「硬體」為 **攝影機**（OpenCV），**未使用 RPi.GPIO**；若需開燈拍照，則經 MQTT 發送 **`switch/light`** 給 **sensor** 端，由 sensor 改寫 GPIO。

### 3.1 初始化 (Initialization)

- **無 GPIO 設定**；僅載入 MQTT 基底類別、OpenCV、numpy 等。
- **攝影機** 不在模組頂層初始化，而是在 **`SaveImage()`** 內以 **`cv2.VideoCapture(0)`** 開啟，擷取一輪後 **`cap.release()`**、**`cv2.destroyAllWindows()`**，因此是**按次開啟／關閉**，非常駐佔用。

### 3.2 主迴圈 (Main Loop) — 定期擷取影像

- **主迴圈**在 **`DataPublisher()`** 內，**`while True:`**：
  1. 呼叫 **`SaveImage()`**：
     - **`cv2.VideoCapture(0)`** 開啟攝影機；
     - **`cap.read()`** 取得一幀，以 HSV 分析綠色／棕色區域並計算健康度；
     - 寫入本地 `img/`、`anatomy/`，並回傳是否成功與健康度。
  2. 若成功，則依序 **Publish** 到 **`immediate/monitor/image`**、**`immediate/anatomy/image`**、**`immediate/plant/health`**。
  3. **`time.sleep(10)`** → **每 10 秒** 執行一輪。

因此：**主迴圈以 10 秒為週期，定期開啟攝影機擷取並上傳影像與健康度。**

### 3.3 收到網頁／MQTT 指令時 — 觸發硬體（攝影機）動作

- **訂閱主題** 由 **`DataSubscriber()`** 建立的 **`SurveillanceImageMqtt`** 以 **`Connect(False)`**（即 **`loop_forever()`**）處理。
- **`on_message()`** 收到 **`manually/take/picture`** 且 payload 中 **`manually_take_picture: True`** 時，會呼叫 **`ManuallyTakePicture()`**：
  - 內部同樣呼叫 **`SaveImage()`**（即 **再次開啟攝影機、擷取一幀、分析、寫檔**）；
  - 再以獨立的 MQTT 客戶端發佈到相同三個主題（監控圖、辨識圖、健康度）。
- 亦即：**網頁「手動拍照」→ 後端發佈 `manually/take/picture` → 影像端 `on_message` 觸發一次攝影機擷取並上傳。**

此腳本**不直接改寫任何 GPIO 電位**；若需拍照前開燈，可透過專案中 **`SendModePublisher()`** 發送 **`switch/light`**，由 **sensor** 端 **`on_message`** 改寫 **GPIO 18**。

### 3.4 生命週期流程簡圖（image_recognition）

```
模組載入
  → 無 GPIO 初始化；僅 MQTT、OpenCV 等
  ↓
__main__：啟動 task_sub（訂閱）、task_pub（發佈 + 主迴圈）
  ↓
┌─ task_sub：loop_forever() 等待 MQTT
│     → on_message()：manually/take/picture → ManuallyTakePicture() → SaveImage() + Publish
│     → response/monitor|anatomy/message → 刪除本地暫存圖
│     → receive/sensor/light/status → 紀錄燈狀態
│
└─ task_pub：while True
      → SaveImage()（VideoCapture(0) → read → HSV 分析 → 寫檔）
      → Publish(immediate/monitor/image, immediate/anatomy/image, immediate/plant/health)
      → time.sleep(10)
```

---

## 四、website — 後端與網頁指令的關係

- **website** 專案中**沒有**在 Raspberry Pi 上常駐執行、直接控制 GPIO 或感測器的 Python 腳本。
- **硬體控制** 的流程是：
  1. 使用者在**網頁**上操作（例如按「開燈」「澆水」「手動拍照」）。
  2. 前端呼叫 **Flask API**（如 `/relay/manually/open/light`、`/manually/take/picture`）。
  3. 後端使用 **`MqttClient`**（或同等邏輯）**發佈**對應 MQTT 主題（如 **`switch/light`**、**`switch/watering`**、**`manually/take/picture`**）。
  4. **sensor** 或 **image_recognition** 的 **`on_message`** 收到後，依前兩節說明**改寫 GPIO** 或**觸發攝影機**。

因此：**「收到網頁指令」在硬體端的對應，就是 MQTT 訂閱端的 `on_message` 被觸發；實際電位改寫發生在 sensor 的 `mqtt_for_sensor.py`。**

---

## 五、彙總表

| 項目 | sensor（mqtt_for_sensor.py） | image_recognition（mqtt_for_image.py） |
|------|------------------------------|----------------------------------------|
| **初始化 GPIO 模式** | `GPIO.setmode(GPIO.BCM)`；`GPIO.setup(17, OUT, initial=HIGH)`、`GPIO.setup(18, OUT, initial=HIGH)`；MCP3008 SPI 初始化 | 無 GPIO；攝影機在 `SaveImage()` 內按次 `VideoCapture(0)` |
| **主迴圈位置** | `DataPublisher()` 的 `while True` | `DataPublisher()` 的 `while True` |
| **主迴圈週期** | **5 秒**（`time.sleep(5)`） | **10 秒**（`time.sleep(10)`） |
| **主迴圈讀取之硬體** | DHT11（GPIO 4）、MCP3008 CH0/1/2（光、土壤、水位） | 攝影機（OpenCV）一幀，並計算健康度 |
| **網頁／MQTT 指令觸發** | `on_message()` 收到 `switch/light`、`switch/watering`、`operation/command`、`switch/auto/control` → **直接 `GPIO.output(light_pin/motor_pin, LOW/HIGH)`** | `on_message()` 收到 `manually/take/picture` → **`ManuallyTakePicture()`** → 一次 **`SaveImage()`** + Publish |
| **異常／結束時硬體** | **HandleAbnormal()**：亮度/土壤/水位異常 → **GPIO 18、17 設 HIGH**；**ForceStop()**：程式結束前 **GPIO 18、17 設 HIGH** | 無 GPIO；僅 MQTT 斷線與程序結束 |

以上即為專案中負責控制硬體（Relay、Sensors、攝影機）的 Python 腳本之程式生命週期彙整。
