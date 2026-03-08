# 家庭植栽監控系統 — 技術總結報告

> 本文件依據專案內 **FAILSAFE_AND_LOGIC.md**、**SYSTEM_ARCHITECTURE.md**、**FLASK_AND_THREADING.md** 及相關 .md 與原始碼彙整，供面試時對照解說。條列式、精簡撰寫。

---

## 一、核心架構 (Core Architecture)

### 1.1 軟硬體如何透過 MQTT 溝通

- **Broker**：Mosquitto，TLS 埠 **8883**，集中轉發所有主題；後端與兩台 Raspberry Pi 皆為 MQTT 客戶端，**不直連彼此**。
- **角色與職責**：
  - **感測器 Pi (sensor)**：讀取 DHT11、MCP3008（光線／土壤／水位），以 **GPIO 17、18** 控制燈與馬達繼電器；訂閱 `switch/light`、`switch/watering`、`operation/command`、`switch/auto/control`，發佈 `env/plant/detection/data`、`receive/sensor/light/status`、`realy/current/mode`。
  - **影像 Pi (image_recognition)**：OpenCV 擷取影像、HSV 計算健康度；發佈 `immediate/monitor/image`、`immediate/anatomy/image`、`immediate/plant/health`，訂閱 `manually/take/picture`、`response/monitor|anatomy/message`。
  - **Flask 後端 (website)**：提供 REST API；訂閱感測／影像／健康度／繼電器狀態，寫入 DB；**僅在自動模式**時發佈 `operation/command`；手動操作經 **MqttClient** 發佈 `switch/light`、`switch/watering`、`switch/auto/control`。
- **資料流**：
  - **感測 → 後端**：感測器 Pi 每 5 秒發送 `env/plant/detection/data` → 後端寫 DB、門檻判斷 → 若自動模式則發送 `operation/command`。
  - **控制 → 硬體**：Flask 或影像端發佈控制主題 → Broker → 感測器 Pi **on_message** 內 **GPIO.output()** 改寫腳位。
  - **影像 → 後端**：影像 Pi 發佈原圖／辨識圖／健康度 → 後端存檔、寫 DB、健康度門檻與 OneSignal 警報。

### 1.2 架構要點

- **分層**：Presentation (Vue) → Application (Flask + MQTT) → Message Broker (Mosquitto) → Edge (sensor / image_recognition)；邊緣裝置**不暴露 HTTP**，僅經 **Protocol Integration (MQTT)** 與後端耦合。
- **硬體邊界**：**唯一直接驅動 GPIO 的程式**為 `sensor/mqtt_for_sensor.py`；後端與影像端**不碰 GPIO**，僅經 MQTT 下達指令。
- **GPIO 語意**：BCM 17 馬達、18 燈光；**HIGH = 關閉繼電器、LOW = 導通**；初始化 `initial=GPIO.HIGH`，安全預設。

---

## 二、故障安全機制 (Failsafe Mechanisms)

### 2.1 數據校驗（實際存在於程式中的邏輯）

| 層級 | 位置 | 校驗內容 | 行為 |
|------|------|----------|------|
| **邊緣 (sensor)** | `CollectSensorData()`、`LightData()` | `humidity/temperature is None`（DHT11 失敗）；`soil == 0 or light == 0 or water_level == 0`（ADC 異常） | 呼叫 **HandleAbnormal(data)**，**return None / False**，**不 Publish** 該筆資料。 |
| **邊緣** | `HandleAbnormal()` | 依 key 判斷：`brightness` 異常 → 關燈；`soil` 或 `water_level` 異常 → 關馬達 | **GPIO.output(light_pin/motor_pin, True)** 立即關閉繼電器；寫入 **error** 目錄 log。 |
| **邊緣** | `DataPublisher()` 主迴圈 | `message_data is not None and message_data is not False` | 僅在資料有效時呼叫 **Publish**；否則寫 error log，下一輪重試。 |
| **後端** | `check_abnormal_data.py` | 溫度 16～30°C、濕度 45～65% RH、亮度 &lt;51% 開燈、水位 ≤30% 停馬達、土壤＋水位組合 | **CheckTemperature**、**CheckEnvironmentHumidity**、**WhetherTurnOnLight**、**WhetherTurnOnWatering** 更新 **storage_response['mode']**／**['send']**；**僅在自動模式**時發送 **operation/command**。 |
| **後端** | 健康度 | `CheckHealthStatus`：健康度 &lt;40% 允許發送警報 | 寫 DB、OneSignal 推播；可擴充為下達硬體指令。 |
| **後端** | `check_data_repeatability_for_health` | 健康度資料重複性檢查 | 避免重複寫入 DB。 |

### 2.2 異常處理（單一錯誤不導致系統崩潰）

| 位置 | 作法 | 效果 |
|------|------|------|
| **sensor** | **on_message**、**DataPublisher**、**DataSubscriber**、**CurrentModePublisher** 外層 **try: ... except Exception as e: CatchError(e)** | 單一訊息解碼或 GPIO 異常只寫 error log，**不 re-raise**，訂閱／發佈迴圈繼續。 |
| **website** | **WebClient.__on_message** 內 **try: ... except FileExistsError / Exception: __HandleError()** | 單一主題的 payload 解碼、DB 寫入、影像存檔或 **CollectSensorData** 出錯時不中斷 MQTT 迴圈。 |
| **website** | **CollectSensorData()**、**CollectGrowingData()** 內 **try: ... except Exception as e: CatchError(e)** | 門檻檢查或鍵值錯誤只記錄，回傳可能為 None；不往上拋。 |
| **image_recognition** | **on_message**、**DataPublisher** 外層 **try: ... except ... CatchError(e)** | **SaveImage()** 或 Publish 失敗時記錄，**while True** 下一輪繼續（如 10 秒後重試）。 |
| **共用** | **CatchError**／**__HandleError** 僅**記錄**（含檔案、行號、例外類型），**不再次拋出** | 單一錯誤不向上傳播，程序不退出。 |

### 2.3 其他 Failsafe 要點

- **ForceStop()**（sensor）：程式結束或 KeyboardInterrupt 時，先 **GPIO.output(light_pin, True)**、**GPIO.output(motor_pin, True)**，再斷線、**os._exit(0)**，避免「程式已關閉但繼電器仍導通」。
- **水位**：邊緣讀值為 0 即關馬達；後端 **water_level ≤ 30%** 產出停馬達指令，**馬達乾燒保護**為最高採樣優先權（文件建議 3～5 秒週期）。

---

## 三、開發亮點 (Engineering Highlights)

### 3.1 多執行緒處理併發請求

- **後端 (website)**：MQTT 客戶端在**模組載入時**建立，**start_loop()** 以 **threading.Thread(target=self.__loop)** 執行 **loop_forever()**；REST 請求與 MQTT 迴圈**不同執行緒**（若 uWSGI 分開 main / mainMqtt 則為不同行程），彼此不阻塞。
- **影像 Pi (image_recognition)**：
  - **task_sub**：**DataSubscriber()**，**Connect(False)** → **loop_forever()**，專職訂閱（手動拍照、response 回覆、燈狀態）。
  - **task_pub**：**DataPublisher()**，**Connect(True)** → **loop_start()**，**SaveImage()**（攝影機＋OpenCV）＋發佈，每 10 秒一輪。
  - **效果**：收到「手動拍照」或後端回覆時 **task_sub** 可立即處理，**不受 task_pub 的 SaveImage 週期影響**；影像運算不阻塞 MQTT 收訊。
- **感測器 Pi (sensor)**：
  - **task_sub**：訂閱 **switch/light**、**switch/watering**、**operation/command**、**switch/auto/control**，**on_message** 內直接 **GPIO.output()**。
  - **task_pub**：**CollectSensorData()**（DHT11＋MCP3008）＋發佈 **env/plant/detection/data**，每 5 秒一輪。
  - **效果**：開燈／澆水／自動指令**即時**改寫 GPIO，**不受 task_pub 的 5 秒採樣與 sleep 影響**。

### 3.2 系統穩定度要求與對應設計

- **即時硬體控制**：控制類主題由**訂閱專用執行緒**處理，不與感測器讀取或影像運算共用同一迴圈，避免 **time.sleep()** 或重運算延遲指令。
- **影像運算不影響硬體監控**：影像 Pi 與感測器 Pi **分機**；影像 Pi 上 SaveImage 只在 **task_pub**，**task_sub** 專職收 MQTT，兩者分線程；感測器 Pi 上 GPIO 控制與感測器採樣分線程。
- **單一錯誤不崩潰**：所有 MQTT 回呼與週期性發佈迴圈外層 **try/except**，例外處理函式僅記錄、不 re-raise。
- **無效資料不影響決策**：感測器讀取失敗或為 0 時不推送；後端僅在自動模式發送 **operation/command**，手動模式下仍做門檻判斷與警報但不下達硬體指令。
- **安全預設**：GPIO 初始化 **initial=GPIO.HIGH**（繼電器關閉）；離開時 **ForceStop** 強制關燈、關馬達再結束程序。

---
