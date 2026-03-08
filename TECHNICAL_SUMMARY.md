# 家庭植栽監控系統 — 技術總結報告

## 一、核心架構 (Core Architecture)

### 1.1 軟硬體通訊與解耦設計

- **Broker**：Mosquitto，TLS 埠 **8883**，集中轉發；後端與兩台 Raspberry Pi 皆為 MQTT 客戶端，**不直連彼此**，達成 **Decoupled（解耦合）** 架構。
- **角色與職責**：
  - **感測器 Pi (sensor)**：DHT11、MCP3008（光／土壤／水位），**GPIO 17、18** 控制燈與馬達繼電器；訂閱 `switch/light`、`switch/watering`、`operation/command`、`switch/auto/control`，發佈 `env/plant/detection/data`、`receive/sensor/light/status`、`realy/current/mode`。
  - **影像 Pi (image_recognition)**：OpenCV 擷取與健康度計算；發佈 `immediate/monitor/image`、`immediate/anatomy/image`、`immediate/plant/health`，訂閱 `manually/take/picture`、`response/monitor|anatomy/message`。
  - **Flask 後端 (website)**：REST API；訂閱感測／影像／健康度／繼電器狀態並寫入 DB；**僅在自動模式**發佈 `operation/command`；手動操作經 MqttClient 發佈控制主題。
- **資料流**：感測 → `env/plant/detection/data` → 後端門檻判斷 → 自動模式下 `operation/command`；控制 → 控制主題 → Broker → 感測器 Pi **on_message** → **GPIO.output()**；影像 → 原圖／辨識圖／健康度 → 後端存檔與 DB。

### 1.2 架構術語與要點

- **Decoupled**：邊緣裝置不暴露 HTTP，僅經 **Protocol Integration (MQTT)** 與後端耦合；**唯一直接驅動 GPIO** 者為 `sensor/mqtt_for_sensor.py`，後端與影像端不碰硬體。
- **Asynchronous Control（異步控制）**：控制指令經 MQTT 非同步下達；邊緣端以**訂閱專用執行緒**處理 `on_message`，與感測器採樣／影像運算執行緒分離，確保控制延遲不受採樣週期或重運算影響。
- **State Machine（狀態機）**：繼電器模式由 `open_auto_control`、`open_manually_light_control`、`open_manually_motor_control` 等旗標與主題 `operation/command`、`switch/light`、`switch/watering`、`switch/auto/control` 驅動；僅在 `open_auto_control is True` 時執行 `operation/command`，手動／自動切換具明確狀態轉換。
- **GPIO 語意**：BCM 17 馬達、18 燈光；**HIGH = 關閉繼電器、LOW = 導通**；初始化 **initial=GPIO.HIGH**，符合 Fail-Safe 預設。

---

## 二、故障安全機制 (Failsafe Mechanisms)

### 2.1 數據完整性驗證 (Data Integrity)

透過 **閾值 (Threshold)** 與有效值檢查，防止硬體異常（斷路、讀值漂移、感測器失效）觸發錯誤動作：

| 層級 | 機制 | 說明 |
|------|------|------|
| **邊緣** | **有效值檢查** | `CollectSensorData()`、`LightData()`：**humidity/temperature is None**（DHT11 斷線／讀取失敗）、**soil == 0 or light == 0 or water_level == 0**（ADC 斷路或異常）視為無效，不信任該筆資料；呼叫 **HandleAbnormal(data)**，**return None/False**，**不 Publish**，避免錯誤資料驅動後端決策。 |
| **邊緣** | **依異常項目關閉執行器** | **HandleAbnormal()** 依 key：`brightness` 異常 → **GPIO.output(light_pin, True)** 關燈；`soil` 或 `water_level` 異常 → **GPIO.output(motor_pin, True)** 關馬達；並寫入 **error** 目錄 log，可追溯。 |
| **邊緣** | **發佈前再次驗證** | **DataPublisher()** 主迴圈僅在 `message_data is not None and message_data is not False` 時呼叫 **Publish**；否則寫 error log，下一輪重試。 |
| **後端** | **門檻式閾值檢查** | `check_abnormal_data.py`：**CheckTemperature**（16～30°C）、**CheckEnvironmentHumidity**（45～65% RH）、**WhetherTurnOnLight**（亮度 &lt;51% 開燈）、**WhetherTurnOnWatering**（水位 ≤30% 停馬達、土壤＋水位組合）、**CheckHealthStatus**（健康度 &lt;40% 警報）；超出閾值則更新 **storage_response['mode']**／**['send']**，**僅在自動模式**發送 **operation/command**，防止漂移或異常值觸發錯誤開關。 |
| **後端** | **資料重複性檢查** | `check_data_repeatability_for_health` 避免重複寫入，維持 DB 一致性。 |

**設計要點**：邊緣著重「讀不到或為 0」之**立即硬體安全**；後端著重「數值在可讀但超出合理範圍」之**門檻判斷**，雙層把關，避免斷路或讀值漂移導致誤動作。

### 2.2 心跳偵測與通訊中斷之安全策略 (Heartbeat & Safety Mode)

- **現行設計**：
  - **上電／初始化**：GPIO **initial=GPIO.HIGH**，繼電器處於關閉狀態（Safety 預設）。
  - **程式結束**：**ForceStop()** 先 **GPIO.output(light_pin, True)**、**GPIO.output(motor_pin, True)**，再斷線、**os._exit(0)**，確保離開時硬體進入安全狀態。
  - **異常時不推送**：感測器讀取失敗或為 0 時不 Publish，避免錯誤資料影響後端；邊緣端立即關閉對應繼電器。
- **心跳偵測 (Heartbeat) — 與韌體 Watchdog 對齊之擴充**：  
  可於邊緣或後端實作**週期性連線狀態偵測**（例如訂閱/發佈端偵測與 Broker 之連線、或後端偵測最後一筆感測資料時間戳）；**逾時未收到有效心跳或資料時，視為通訊中斷，自動進入 Safety Mode**：邊緣端強制 **GPIO.output(light_pin, True)**、**GPIO.output(motor_pin, True)**，停止所有執行器，直至連線恢復。此設計與韌體常見之 Watchdog 與 Safe State 思維一致，可納入技術規範作為擴充項目。

### 2.3 互斥控制 (Mutual Exclusion)

- **現行設計**：感測器 Pi 上 **GPIO 寫入僅發生於單一執行緒** — **task_sub** 之 **on_message()** 專職處理所有控制主題（`switch/light`、`switch/watering`、**operation/command**、`switch/auto/control`），**task_pub** 僅負責感測器讀取與 MQTT 發佈，**不寫入 GPIO**。因此對硬體 I/O 而言，**實質為單一寫入者**，無多執行緒同時操作同一腳位之競態。
- **互斥之規範化**：若未來擴充為**多執行緒寫入同一 GPIO 或同一硬體資源**，應以 **threading.Lock** 保護 **GPIO.output()** 之關鍵區段（Critical Section），確保同一時間僅一執行緒驅動該 I/O，符合工業級韌體對共用資源之互斥要求。

### 2.4 異常處理（單一錯誤不導致系統崩潰）

| 位置 | 作法 | 效果 |
|------|------|------|
| **sensor** | **on_message**、**DataPublisher**、**DataSubscriber**、**CurrentModePublisher** 外層 **try: ... except Exception as e: CatchError(e)** | 單一訊息解碼或 GPIO 異常只寫 error log，**不 re-raise**，訂閱／發佈迴圈繼續。 |
| **website** | **WebClient.__on_message** 內 **try: ... except FileExistsError / Exception: __HandleError()** | 單一主題之 payload 解碼、DB 寫入、影像存檔或 **CollectSensorData** 出錯時不中斷 MQTT 迴圈。 |
| **website** | **CollectSensorData()**、**CollectGrowingData()** 內 **try: ... except Exception as e: CatchError(e)** | 門檻檢查或鍵值錯誤只記錄，回傳可能為 None；不往上拋。 |
| **image_recognition** | **on_message**、**DataPublisher** 外層 **try: ... except ... CatchError(e)** | **SaveImage()** 或 Publish 失敗時記錄，**while True** 下一輪繼續。 |
| **共用** | **CatchError**／**__HandleError** 僅**記錄**（含檔案、行號、例外類型），**不再次拋出** | 單一錯誤不向上傳播，程序不退出。 |

### 2.5 其他 Failsafe 要點

- **ForceStop()**（sensor）：程式結束或 KeyboardInterrupt 時，先關閉燈與馬達再斷線，避免「程式已關閉但繼電器仍導通」。
- **水位與馬達乾燒保護**：邊緣讀值為 0 即關馬達；後端 **water_level ≤ 30%** 產出停馬達指令；水位採樣具最高優先權（文件建議 3～5 秒週期）。

---

## 三、開發亮點 (Engineering Highlights)

### 3.1 多執行緒與 Asynchronous Control

- **後端**：MQTT 客戶端以 **threading.Thread(target=self.__loop)** 執行 **loop_forever()**；REST 與 MQTT 迴圈分離，彼此不阻塞。
- **影像 Pi**：**task_sub**（**loop_forever()**）專職訂閱；**task_pub**（**loop_start()**）執行 **SaveImage()** 與發佈，每 10 秒一輪；手動拍照與 response 由 **task_sub** 即時處理，不受 **task_pub** 週期影響。
- **感測器 Pi**：**task_sub** 專職訂閱並執行 **GPIO.output()**；**task_pub** 僅 **CollectSensorData()** 與發佈，每 5 秒一輪；開燈／澆水／自動指令即時改寫 GPIO，不受採樣與 **time.sleep(5)** 影響。

### 3.2 系統穩定度要求與對應設計

- 控制類主題由訂閱專用執行緒處理，避免 **time.sleep()** 或重運算延遲指令。
- 影像 Pi 與感測器 Pi 分機；影像運算與硬體控制分線程，影像運算不影響即時硬體監控。
- 單一錯誤不崩潰：所有 MQTT 回呼與週期性發佈迴圈外層 **try/except**，例外處理僅記錄、不 re-raise。
- 無效資料不影響決策：感測器讀取失敗或為 0 時不推送；後端僅在自動模式發送 **operation/command**。
- 安全預設：GPIO **initial=GPIO.HIGH**；離開時 **ForceStop** 強制關燈、關馬達。

---

## 四、對系統穩定度之貢獻

- **複雜邏輯轉化為 Technical Spec（技術規範）**：專案內 **SYSTEM_ARCHITECTURE.md**、**FAILSAFE_AND_LOGIC.md**、**FLASK_AND_THREADING.md**、**HARDWARE_SPEC_AND_THRESHOLDS.md**、**HARDWARE_CODE_REFERENCE.md**、**HARDWARE_LIFECYCLE.md**、**CODE_FUNCTION_MAPPING.md** 等文件，將架構、故障安全、門檻、GPIO/SPI 生命週期與程式對照表格化、條列化，並標註檔案與行號，使複雜邏輯可被覆核、擴充與交接，符合工業開發對技術規範之要求。
- **開發初期即納入電源管理與異常保護**：  
  - **電源／上電**：GPIO 初始化即設 **initial=GPIO.HIGH**，上電後繼電器不導通，避免未預期負載。  
  - **異常保護**：感測器讀取失敗或為 0 時立即關閉對應繼電器（**HandleAbnormal**）、不推送無效資料；程式結束前 **ForceStop** 強制關閉燈與馬達；後端以閾值過濾異常值，僅在自動模式下達 **operation/command**。  
  此種「預設安全、異常時收斂至安全狀態、無效資料不驅動決策」之思維，與韌體開發中電源管理、Watchdog、Safe State 之核心邏輯一致，有利於在面試中展現對系統穩定度與可維運性之重視。

---
