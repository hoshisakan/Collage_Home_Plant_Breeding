# 硬體相關程式碼彙整：GPIO、馬達驅動與感測器讀取

本文件從專案中摘出**所有涉及 GPIO 控制、馬達驅動、感測器讀取（SPI／數位感測）**的程式碼，並以註解說明**硬體初始化**與**異常判定**的處理方式。

---

## 一、涵蓋範圍與檔案位置

| 類型 | 介面 | 檔案 | 說明 |
|------|------|------|------|
| **GPIO 輸出** | RPi.GPIO (BCM) | `sensor/mqtt_for_sensor.py` | 燈光繼電器 (pin 18)、馬達繼電器 (pin 17) |
| **馬達驅動** | 同上，透過繼電器 | 同上 | 開／關馬達與 5 秒時序 |
| **類比感測** | **SPI** (MCP3008) | 同上 | 亮度 CH0、土壤 CH1、水位 CH2 |
| **溫溼度感測** | 數位單線 (DHT11) | 同上 | GPIO 4，非 I2C／SPI |

專案中**未使用 I2C**；感測器讀取僅有 **SPI (MCP3008)** 與 **DHT11（單線協定）**。上述邏輯全部集中在 **`sensor/mqtt_for_sensor.py`**，其餘模組（website、image_recognition）不直接操作硬體。

---

## 二、硬體初始化 (Initialization)

初始化在**模組載入時**執行（無額外 `main()` 前段），順序：GPIO 模式 → 腳位定義 → 輸出預設電位 → SPI (MCP3008)。DHT11 無模組頂層初始化，在讀取函式內以 `read_retry` 指定腳位。

### 2.1 GPIO 模式與繼電器腳位

```python
# === 檔案：sensor/mqtt_for_sensor.py（約第 17–24 行）===

import RPi.GPIO as GPIO
# ...

GPIO.setmode(GPIO.BCM)           # 使用 BCM 腳位編號，與接線圖一致
GPIO.setwarnings(False)           # 避免重複設定腳位時產生警告

motor_pin = 17                    # 澆水馬達繼電器：BCM 17
light_pin = 18                    # 燈光繼電器：BCM 18

# 輸出腳位、初始為 HIGH = 繼電器不導通（安全預設，避免上電瞬間誤動作）
GPIO.setup(motor_pin, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.HIGH)
```

**說明：**

- **硬體初始化**：先定 **GPIO 編號模式 (BCM)**，再對兩支輸出腳做 **setup**，並以 **`initial=GPIO.HIGH`** 確保程式一啟動時燈與馬達皆為關閉，符合 Fail-Safe。
- **異常／關機**：後續在 `ForceStop()`、`HandleAbnormal()` 中同樣以 **HIGH** 關閉繼電器，與初始化語意一致。

### 2.2 SPI 與 MCP3008 (類比感測)

```python
# === 檔案：sensor/mqtt_for_sensor.py（約第 18–21 行）===

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
```

**說明：**

- **硬體初始化**：在模組頂層建立 **MCP3008** 實例，使用 **SPI 0、Device 0**（/dev/spidev0.0）。之後所有類比讀取皆透過 **`mcp.read_adc(channel)`**，不需重複初始化 SPI。
- **異常判定**：不在初始化階段檢查 SPI 是否可用；若讀取失敗或為 0，在 **CollectSensorData()**、**LightData()** 中視為異常並觸發 **HandleAbnormal()**（見第四節）。

---

## 三、GPIO 控制與馬達驅動

所有繼電器控制皆透過 **`GPIO.output(pin, value)`** 實作；**LOW = 導通、HIGH = 關閉**（低電位觸發繼電器）。

### 3.1 開燈／關燈（燈光繼電器，GPIO 18）

```python
# === 檔案：sensor/mqtt_for_sensor.py，SensorMqtt.on_message() 內 ===

# 開燈：將腳位設為 LOW，繼電器導通
if command is True:
    self.__light_current_status = GPIO.LOW
    GPIO.output(light_pin, self.__light_current_status)
    print("開啟自動開燈功能")
else:
    self.__light_current_status = GPIO.HIGH
    GPIO.output(light_pin, self.__light_current_status)
    print("關閉自動開燈功能")
```

### 3.2 馬達驅動（澆水繼電器，GPIO 17）與 5 秒時序

```python
# === 檔案：sensor/mqtt_for_sensor.py，SensorMqtt.on_message() 內 ===

if command is True:
    self.__motor_current_status = GPIO.LOW
    GPIO.output(motor_pin, self.__motor_current_status)
    print("手動開始澆水")
    time.sleep(5)                           # 維持導通 5 秒
    self.__motor_current_status = GPIO.HIGH
    GPIO.output(motor_pin, self.__motor_current_status)
    print("關閉自動澆水")
else:
    self.__motor_current_status = GPIO.HIGH
    GPIO.output(motor_pin, self.__motor_current_status)
```

**說明：**

- **馬達驅動**：僅有「開一段時間後自動關」或「直接關」兩種；以 **`time.sleep(5)`** 固定澆水時長，避免長時間通電。
- **硬體與異常**：未在驅動前再讀感測器；異常時由 **HandleAbnormal()** 強制 **`GPIO.output(motor_pin, True)`** 關閉馬達。

### 3.3 程式結束時關閉所有繼電器 (Fail-Safe)

```python
# === 檔案：sensor/mqtt_for_sensor.py，ForceStop()（約第 206–217 行）===

def ForceStop():
    global sensor_sub, sensor_pub
    # 離開前將燈與馬達皆設為關閉，避免程序結束後繼電器仍導通
    GPIO.output(light_pin, True)
    GPIO.output(motor_pin, True)
    sensor_sub.Disconnect()
    sensor_pub.Disconnect()
    os._exit(0)
```

---

## 四、感測器讀取

### 4.1 SPI — MCP3008 類比讀取 (亮度、土壤、水位)

```python
# === 檔案：sensor/mqtt_for_sensor.py ===

# 單一通道讀取（亮度），用於開／關燈後回報 — LightData() 內
light = mcp.read_adc(0)

# 三通道讀取，用於定時上報 — CollectSensorData() 內
light = mcp.read_adc(0)      # CH0：環境亮度
soil = mcp.read_adc(1)       # CH1：土壤濕度
water_level = mcp.read_adc(2)  # CH2：水位深度
```

**說明：**

- **硬體介面**：MCP3008 為 **10-bit ADC**，讀值 0–1023；程式內以 **ConvertPercent()** 轉成 0–100 百分比再上傳。
- **異常判定**：若 **`light == 0`**、**`soil == 0`** 或 **`water_level == 0`**，視為接線或感測異常，不推送該筆資料，並呼叫 **HandleAbnormal()** 做安全關閉（見下節）。

### 4.2 數位感測 — DHT11 溫溼度 (GPIO 4，單線協定)

```python
# === 檔案：sensor/mqtt_for_sensor.py，CollectSensorData() 內（約第 373 行）===

humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
```

**說明：**

- **硬體介面**：DHT11 接在 **GPIO 4 (BCM)**；**read_retry** 會重試讀取，失敗時回傳 **None**。
- **異常判定**：若 **`humidity is None or temperature is None`**，視為讀取失敗，呼叫 **HandleAbnormal(data)**、**return None**，不將該筆資料送上 MQTT；主迴圈僅寫 log 並在下一輪重試。

### 4.3 ADC 轉百分比 (共用於 MCP3008 三通道)

```python
# === 檔案：sensor/mqtt_for_sensor.py，ConvertPercent()（約第 360–370 行）===

def ConvertPercent(**kwargs):
    sensorUpper = 1023
    sensorLower = 0
    tempList = []
    for key, value in kwargs.items():
        tempSensorValue = abs(value - sensorUpper)
        percentage = int(float((tempSensorValue - sensorLower) * 100) / (sensorUpper - sensorLower))
        tempList.append(percentage)
    return tempList
```

---

## 五、異常判定與硬體安全 (Exception / Abnormal Handling)

感測器讀不到或為不合理值時：**不推送該筆資料**、**寫入錯誤 log**，並依項目**強制關閉燈或馬達**，避免在異常狀態下持續驅動硬體。

### 5.1 感測資料有效值檢查（主迴圈資料來源）

```python
# === 檔案：sensor/mqtt_for_sensor.py，CollectSensorData() 內（約第 399–409 行）===

if humidity is None or temperature is None:
    HandleAbnormal(data)
    return None
elif soil == 0 or light == 0 or water_level == 0:
    HandleAbnormal(data)
    return False
else:
    # 資料有效，轉成 JSON 回傳供 MQTT 發送
    convertion_json = json.dumps(data)
    return convertion_json
```

**說明：**

- **DHT11**：回傳 **None** 即視為讀取失敗，觸發 **HandleAbnormal**，並 **return None**。
- **MCP3008**：原始值 **0** 視為異常（斷線或感測器故障），同樣 **HandleAbnormal**、**return False**。
- 主迴圈僅在 **`message_data is not None and message_data is not False`** 時才 Publish，否則只寫 error log，下一輪再重試讀取。

### 5.2 亮度單次讀取的異常處理

```python
# === 檔案：sensor/mqtt_for_sensor.py，LightData() 內（約第 314–330 行）===

def LightData(light_sta):
    light = mcp.read_adc(0)
    convertResult = ConvertPercent(brightness=light)
    # ...
    if light == 0:
        HandleAbnormal(data)
        return False
    else:
        # 正常則組 JSON 回傳
        return convertion_json
```

### 5.3 異常時強制關閉繼電器 (HandleAbnormal)

```python
# === 檔案：sensor/mqtt_for_sensor.py（約第 219–234 行）===

def HandleAbnormal(abnormal=None):
    if abnormal is not None:
        abnormal_message = {}
        for key, value in abnormal.items():
            if value is None or value == 0:
                abnormal_message[key] = value
                if key == 'brightness':
                    GPIO.output(light_pin, True)   # 亮度異常 → 關燈
                elif key == 'soil' or key == 'water_level':
                    GPIO.output(motor_pin, True)   # 土壤／水位異常 → 關馬達
        abnormal_message['date'] = abnormal['date']
        error_message = '異常訊息:\n{}'.format(abnormal_message)
        StorageExecuteMessage(True, error_message)  # 寫入 error 目錄 log
```

**說明：**

- **硬體安全**：依異常項目決定關閉對象——**brightness** 異常關燈、**soil / water_level** 異常關馬達，避免在感測失效時持續動作。
- **可追溯**：將異常內容與時間寫入 **error** log，便於事後分析。

### 5.4 MQTT 回呼內的例外處理（避免單一訊息導致程序崩潰）

```python
# === 檔案：sensor/mqtt_for_sensor.py，SensorMqtt.on_message()（約第 55–164 行）===

def on_message(self, client, userdata, message):
    try:
        decode_message = str(message.payload.decode("utf-8", "ignore"))
        receive_data = json.loads(decode_message)
        receive_topic = message.topic
        # ... 依 topic 改寫 GPIO、呼叫 LightPublisher、__send_current_status ...
    except Exception as e:
        CatchError(e)   # 記錄錯誤並寫入 error log，不中斷訂閱執行緒
```

---

## 六、彙總表

| 項目 | 位置 | 硬體初始化要點 | 異常／防呆要點 |
|------|------|----------------|----------------|
| **GPIO 輸出** | 模組頂層、on_message、ForceStop、HandleAbnormal | BCM、OUT、initial=HIGH | 異常時與結束時皆設 HIGH 關閉繼電器 |
| **馬達驅動** | on_message | 同 GPIO，無額外 init | 5 秒時序；HandleAbnormal 關馬達 |
| **SPI (MCP3008)** | 模組頂層、CollectSensorData、LightData | SPI 0.0 建立 MCP3008 實例 | read_adc 為 0 時 HandleAbnormal、不推送 |
| **DHT11** | CollectSensorData | 無頂層 init，read_retry(..., 4) 指定 GPIO 4 | 回傳 None 時 HandleAbnormal、return None |
| **主迴圈** | DataPublisher | — | 僅在 message_data 有效時 Publish，否則寫 log |
