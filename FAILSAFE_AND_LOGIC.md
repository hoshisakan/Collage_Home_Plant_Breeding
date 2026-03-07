# 邏輯判斷與 Failsafe 設計：感測器異常時的決策與系統穩定性

本文件彙整專案中**負責邏輯判斷**的程式碼，重點說明：**感測器數值異常時，系統如何決定關閉馬達或發出警告（Failsafe）**，以及**如何確保單一錯誤不會導致整個系統崩潰**。

---

## 一、邏輯判斷與 Failsafe 的分布

| 層級 | 檔案 | 職責 | Failsafe 行為 |
|------|------|------|----------------|
| **邊緣 (sensor)** | `sensor/mqtt_for_sensor.py` | 感測器原始值檢查、即時關閉繼電器 | 讀取失敗或為 0 時**立即關燈／關馬達**、不推送無效資料、寫 error log |
| **後端 (website)** | `website/.../check_abnormal_data.py` | 門檻式異常判定、產生控制指令、發送警報 | 依溫溼度／亮度／土壤／水位門檻決定 **開關燈、開關馬達**，並可發送 **OneSignal 推播** |
| **後端 (website)** | `website/.../mqtt_loop_connection.py` | 接收感測資料、呼叫異常檢測、發送 `operation/command` | 僅在**自動模式**時將後端產生的指令送給感測器端執行 |

**Failsafe 的兩層分工**：  
- **邊緣**：針對「感測器讀不到或讀到 0」做**立即硬體安全**（關閉繼電器）。  
- **後端**：針對「數值在可讀但超出合理範圍」做**門檻判斷**，決定是否關燈／關馬達並發送**警告**。

---

## 二、邊緣 Failsafe：感測器讀取異常時關閉馬達／燈具

邏輯位於 **`sensor/mqtt_for_sensor.py`**。當感測器**讀取失敗**或**讀值為 0**（視為接線／感測器異常）時，**不信任該筆資料**，並**主動關閉相關硬體**，避免在不可靠狀態下持續驅動。

### 2.1 異常判定條件與觸發時機

| 觸發點 | 條件 | 動作 |
|--------|------|------|
| **CollectSensorData()** | `humidity is None or temperature is None`（DHT11 讀取失敗） | 呼叫 **HandleAbnormal(data)**，**return None**，不推送該筆資料 |
| **CollectSensorData()** | `soil == 0 or light == 0 or water_level == 0`（ADC 異常） | 呼叫 **HandleAbnormal(data)**，**return False**，不推送該筆資料 |
| **LightData()** | `light == 0`（亮度通道異常） | 呼叫 **HandleAbnormal(data)**，**return False**，不推送燈狀態 |

### 2.2 HandleAbnormal：依異常項目關閉對應繼電器

```python
# === 檔案：sensor/mqtt_for_sensor.py（約第 219–234 行）===

def HandleAbnormal(abnormal=None):
    if abnormal is not None:
        abnormal_message = {}
        for key, value in abnormal.items():
            if value is None or value == 0:
                abnormal_message[key] = value
                if key == 'brightness':
                    GPIO.output(light_pin, True)   # 亮度異常 → 關燈（安全預設）
                elif key == 'soil' or key == 'water_level':
                    GPIO.output(motor_pin, True)   # 土壤／水位異常 → 關馬達
        abnormal_message['date'] = abnormal['date']
        error_message = '異常訊息:\n{}'.format(abnormal_message)
        StorageExecuteMessage(True, error_message)  # 寫入 error 目錄，可追溯
```

**Failsafe 邏輯說明**：

- **brightness 異常**（None 或 0）：無法可靠判斷環境光，為避免誤判持續開燈，**關閉燈光繼電器**。
- **soil 或 water_level 異常**：無法可靠判斷土壤或水位，為避免空轉馬達或錯誤澆水，**關閉馬達繼電器**。
- 所有異常皆**寫入 error log**，不丟棄紀錄，方便事後分析。

### 2.3 主迴圈不推送無效資料（避免錯誤資料影響後端）

```python
# === 檔案：sensor/mqtt_for_sensor.py，DataPublisher() 內（約第 424–450 行）===

while True:
    message_data = CollectSensorData()

    if message_data is not None and message_data is not False:
        send_result = sensor_pub.Publish(
            pub_topic='env/plant/detection/data',
            pub_message=message_data,
            pub_qos=2, pub_retain=False
        )
        # 成功則寫 access log，失敗則寫 error log
    else:
        message = "Invalid publish data is {}. . .".format(message_data)
        StorageExecuteMessage(True, message)
    time.sleep(5)
```

**說明**：當 **CollectSensorData()** 因異常而回傳 **None** 或 **False** 時，**不呼叫 Publish**，僅寫 error log，下一輪再重試。如此可避免單一感測器故障時，把無效或危險資料傳到後端、觸發錯誤決策。

### 2.4 程式結束時強制關閉繼電器 (ForceStop)

```python
# === 檔案：sensor/mqtt_for_sensor.py（約第 206–217 行）===

def ForceStop():
    global sensor_sub, sensor_pub
    GPIO.output(light_pin, True)
    GPIO.output(motor_pin, True)
    sensor_sub.Disconnect()
    sensor_pub.Disconnect()
    os._exit(0)
```

**說明**：無論是正常結束或 KeyboardInterrupt，離開前先將**燈與馬達皆設為關閉**，再斷線、結束程序，確保不會留下「程式已關閉但繼電器仍導通」的狀態。

---

## 三、後端邏輯判斷：門檻式異常與控制指令／警告

邏輯位於 **`website/.../tasks/mqtt/check_abnormal_data.py`**。後端收到 **env/plant/detection/data** 後，依**門檻**判斷溫度、濕度、亮度、土壤、水位是否異常，並產生 **開／關燈、開／關馬達** 的指令；必要時發送 **OneSignal 推播** 作為警告。

### 3.1 整體流程（mqtt_loop_connection 的呼叫方式）

```python
# === 檔案：website/.../mqtt_loop_connection.py，__on_message 內 ===

if receive_topic == 'env/plant/detection/data':
    receive_data = json.loads(decode_message)
    if receive_data:
        # 寫入 DB（略）
        command = CAD.CollectSensorData(receive_data)  # 門檻檢查，回傳控制指令
        read_realy_auto_mode = HandleData.read_realy_status()
        if read_realy_auto_mode is True:
            self.publish_data(topic='operation/command', payload=command, qos=2, retain=False)
        else:
            print('現在是手動模式. . .')
```

**說明**：  
- **CollectSensorData(receive_data)** 會依門檻更新內部狀態並回傳 **command**（如 `switch_light_state`、`switch_motor_state` 等）。  
- **僅在自動模式**（`read_realy_auto_mode is True`）時才發送 **operation/command**，感測器端收到後才會改寫 GPIO；手動模式下後端仍會做門檻判斷與警報，但不下達硬體指令。

### 3.2 門檻判定與「關閉馬達／發出警告」的對應

| 函式 | 感測項目 | 門檻／條件 | 控制／警告行為 |
|------|----------|------------|----------------|
| **CheckTemperature** | 溫度 | &lt; 16°C 或 ≥ 30°C | 不切換溫度相關開關；**允許發送警報**（低溫／高溫警報） |
| **CheckEnvironmentHumidity** | 濕度 | &lt; 45% 或 &gt; 65% RH | 不切換濕度開關；**允許發送警報**（過低／過高） |
| **WhetherTurnOnLight** | 亮度 | &lt; 51% 視為不足 | **開燈指令** + 警報（日照不足）；≥ 51% 則**關燈**、不警報 |
| **WhetherTurnOnWatering** | 水位、土壤 | 水位 ≤ 30% 或土壤 ≤ 30% 等組合 | **關馬達**（水量過低或土壤已足）或**開馬達**（土壤不足且水量足），並依情境**發送警報** |
| **CheckHealthStatus** | 健康度 | &lt; 40% | **允許發送警報**（生長不良） |

感測器端實際「關閉馬達」的時機有兩類：  
1. **邊緣 HandleAbnormal**：讀值為 None／0 時**立即關馬達／關燈**。  
2. **後端 operation/command**：門檻判斷後若決定關馬達／關燈，在**自動模式**下透過 **operation/command** 送給感測器端，由 **on_message** 執行 **GPIO.output(..., HIGH)**。

### 3.3 後端 CollectSensorData：彙總門檻與發送警報

```python
# === 檔案：website/.../check_abnormal_data.py（約第 224–250 行）===

def CollectSensorData(check_data=None):
   try:
      CheckTemperature(check_data['temperature'])
      CheckEnvironmentHumidity(check_data['humidity'])
      WhetherTurnOnLight(check_data['brightness'])
      WhetherTurnOnWatering(check_data['water_level'], check_data['soil'])
      for key in storage_response['send']:
        if storage_response['send'][key] == True:
          SendAbnormalAlertMessage()  # OneSignal 推播
          break
      return storage_response['mode']   # 回傳給 mqtt_loop_connection 作為 operation/command
   except Exception as e:
      CatchError(e)
```

**說明**：  
- 各門檻函式會更新 **storage_response['mode']**（控制指令）與 **storage_response['send']**（是否發送警報）。  
- 若有任一 **send** 為 True，則呼叫 **SendAbnormalAlertMessage()** 發送一次推播。  
- **try/except CatchError(e)**：單一筆資料或鍵值錯誤時只記錄、不往上拋，**不中斷 MQTT 回呼**，見第四節。

---

## 四、確保單一錯誤不導致系統崩潰的設計

以下為專案中**避免單一錯誤造成程序崩潰或 MQTT 迴圈中斷**的作法。

### 4.1 邊緣 (sensor)：回呼與發佈迴圈皆捕獲例外

| 位置 | 作法 | 效果 |
|------|------|------|
| **SensorMqtt.on_message()** | 整段邏輯包在 **try:** 內，**except Exception as e: CatchError(e)** | 單一 MQTT 訊息解碼錯誤或 GPIO 操作異常時，只寫 error log，**訂閱執行緒繼續運行**，不崩潰 |
| **DataPublisher()** | **while True** 外層 **try: ... except Exception as e: CatchError(e)** | **CollectSensorData()** 或 **Publish()** 拋錯時，記錄後**不結束程式**，下一輪 sleep(5) 後繼續讀取 |
| **DataSubscriber()** | **try: ... except Exception as e: CatchError(e)** | 訂閱端初始化或連線錯誤時記錄，避免未處理例外導致程序退出 |
| **CurrentModePublisher()** | **try: ... except Exception as e: CatchError(e)** | 發送當前模式時若失敗只記錄，不影響主流程 |

**CatchError** 會將例外類型、訊息、檔案、行號寫入 **error** 目錄下的 log，**不 re-raise**，因此呼叫端不會因單一錯誤而崩潰。

### 4.2 後端 (website)：MQTT 回呼與異常檢測皆捕獲例外

| 位置 | 作法 | 效果 |
|------|------|------|
| **WebClient.__on_message()** | **try: ... except FileExistsError as fer: self.__HandleError(fer); except Exception as e: self.__HandleError(e)** | 單一主題的 payload 解碼、DB 寫入、影像存檔或 **CollectSensorData** 出錯時，只呼叫 **__HandleError**，**不中斷 MQTT 迴圈** |
| **check_abnormal_data.CollectSensorData()** | **try: ... except Exception as e: CatchError(e)** | 門檻檢查或鍵值存取錯誤時只記錄，回傳值可能為 None，呼叫端（mqtt_loop_connection）需能接受；**publish_data** 前若 command 為 None 需防呆（依現有實作，仍會嘗試 publish，若需更嚴謹可再補判斷） |
| **CollectGrowingData()** | **try: ... except Exception as e: CatchError(e)** | 健康度門檻檢查或警報發送失敗時只記錄，不往上拋 |

如此可確保：**單一筆感測資料異常或單一則 MQTT 訊息錯誤，不會讓後端 MQTT 客戶端或感測器端程序崩潰**。

### 4.3 影像端 (image_recognition)：回呼與發佈迴圈捕獲例外

| 位置 | 作法 | 效果 |
|------|------|------|
| **SurveillanceImageMqtt.on_message()** | **try: ... except Exception as e: CatchError(e)** | 手動拍照、response 處理、JSON 解析等錯誤時只記錄，訂閱執行緒不中斷 |
| **DataPublisher()** | **try: ... except Exception as e: CatchError(e)** | **SaveImage()** 或 Publish 失敗時記錄，**while True** 繼續，下一輪 10 秒後重試 |

### 4.4 小結：單一錯誤不崩潰的設計要點

- **邊緣**：感測器讀取異常時以 **HandleAbnormal** 做**立即硬體 Failsafe**（關燈／關馬達），並以 **return None/False** 避免推送無效資料；所有可能拋錯的入口（on_message、DataPublisher、DataSubscriber、CurrentModePublisher）皆 **try/except 並記錄**，不 re-raise。  
- **後端**：門檻邏輯與警報發送放在 **try/except** 內，MQTT **__on_message** 整段捕獲 **FileExistsError** 與 **Exception**，只呼叫 **__HandleError**，不中斷迴圈。  
- **影像端**：on_message 與 DataPublisher 外層 **try/except CatchError**，錯誤時只寫 log，迴圈繼續。  
- **共用原則**：例外處理函式（**CatchError**、**__HandleError**）僅**記錄**，**不再次拋出**，因此單一錯誤不會向上傳播導致程序結束。

---

## 五、流程總覽（Failsafe 與警告）

```
感測器 Pi 讀取 (CollectSensorData / LightData)
    │
    ├─ 讀取失敗或為 0 (DHT None / ADC 0)
    │      → HandleAbnormal(data)
    │      → GPIO 關燈或關馬達 + 寫 error log
    │      → return None / False → 不 Publish
    │
    └─ 讀取正常
           → Publish(env/plant/detection/data) 或 receive/sensor/light/status
                    │
                    ▼
後端收到 env/plant/detection/data
    → check_abnormal_data.CollectSensorData(receive_data)
    → 門檻判斷（溫度／濕度／亮度／土壤／水位）
    → 若 send==True → SendAbnormalAlertMessage()（OneSignal）
    → 回傳 command（switch_light_state, switch_motor_state 等）
    → 若為自動模式 → Publish(operation/command)
                    │
                    ▼
感測器 Pi 收到 operation/command (on_message)
    → 依 command 改寫 GPIO（開／關燈、開／關馬達）
```

---

## 六、彙總表

| 項目 | 邊緣 (sensor) | 後端 (website) |
|------|----------------|----------------|
| **異常判定依據** | 感測器**讀取失敗 (None)** 或 **讀值為 0** | **門檻**（溫度、濕度、亮度、土壤、水位、健康度） |
| **關閉馬達／燈的時機** | **HandleAbnormal** 內依 key 立即 **GPIO.output(..., True)** | 門檻判斷後經 **operation/command** 下達，感測器端 **on_message** 執行 GPIO |
| **發出警告** | 僅寫入 **error log** | **OneSignal 推播**（CollectAlertMessage + SendAbnormalAlertMessage） |
| **單一錯誤不崩潰** | **on_message / DataPublisher / DataSubscriber / CurrentModePublisher** 皆 **try/except CatchError**，不 re-raise | **__on_message** 捕獲 **FileExistsError** 與 **Exception**；**CollectSensorData / CollectGrowingData** 內 **try/except CatchError** |

以上即為專案中**邏輯判斷**、**感測器異常時關閉馬達或發出警告的 Failsafe 邏輯**，以及**確保系統不因單一錯誤而崩潰**的設計彙整。
