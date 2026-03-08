# 家庭植栽監控系統 (Home Plant Breeding)

## 專案簡介

本專案為 **端對端物聯網監控系統**：於 **Raspberry Pi** 上執行感測器採集、繼電器控制與影像健康度分析，經 **MQTT (Mosquitto)** 與後端 **Flask API** 通訊，並由 **Vue 前端** 提供儀表板與即時控制。設計重點為**軟硬體整合之邏輯邊界**：後端與邊緣經協定解耦、硬體 I/O 集中於單一模組、感測異常時收斂至安全狀態，以確保系統可維運與硬體保護。

- **系統架構**：分層與模組邊界、MQTT 協定與資料流向之明確定義。  
- **硬體控制**：GPIO 初始化與電位語意、異常時 **Safety Mode**（繼電器關閉）。  
- **穩定性**：感測器有效值檢查、閾值判斷、訂閱／發佈執行緒分離、單一錯誤不導致程序崩潰。

---

## 系統架構 (System View)

### 分層設計 (Layered Architecture)

| 層級 | 角色 | 技術 | 職責 |
|------|------|------|------|
| **Presentation** | Vue 前端 | SPA、REST API | 儀表板、圖表、開關燈／澆水／手動拍照 |
| **Application** | Flask 後端 | REST、MQTT、DB | API、MQTT 訂閱／發佈、資料持久化、控制指令下達 |
| **Message Broker** | Mosquitto | MQTT、TLS 8883 | 感測、影像、控制主題之集中轉發 |
| **Edge - 感測** | sensor (Raspberry Pi) | RPi.GPIO、DHT11、MCP3008、MQTT | 感測讀取、繼電器輸出、定時上報與指令回應 |
| **Edge - 影像** | image_recognition (Raspberry Pi) | OpenCV、MQTT | 攝影機擷取、健康度計算、定時／手動上傳 |

資料流：**使用者 → 前端 → Flask → MQTT → 感測器 Pi (GPIO)**；**感測器 Pi / 影像 Pi → MQTT → Flask → DB / 前端**。邊緣不暴露 HTTP，僅經 **Protocol Integration (MQTT)** 與後端通訊。

### 容器化部署 (website 模組)

| 服務 | 說明 | 埠 |
|------|------|-----|
| **vue** | 前端建置與開發 | 8082→8080, 8081→8086 |
| **flask** | 後端 API + uWSGI | 5000, 5001 |
| **nginx** | 反向代理、靜態與 SSL | 80, 443 |
| **mysql** | 感測／健康度／繼電器狀態 | 3306 |
| **mosquitto** | MQTT Broker (TLS 8883) | 1883, 8883, 9001, 9002 |
| **phpMyAdmin** | DB 管理 (可選) | 8080 |

Raspberry Pi 端 (sensor、image_recognition) 以 **原生 Python + systemd / init 腳本** 執行，連至同一 Mosquitto Broker，與容器化後端協同運作。

---

## 技術核心與規範 (Technical Highlights)

以下彙整本系統在**核心架構**與**故障安全**上之設計要點，強調硬體保護與系統穩定性，對應工業級嵌入式／韌體開發之常見規範。

### Core Architecture

- **Decoupled（解耦合）**：後端與兩台 Pi 皆經 MQTT Broker 通訊，不直連；**唯一直接驅動 GPIO** 者為 `sensor/mqtt_for_sensor.py`，後端與影像端不碰硬體，降低耦合與單點故障影響。
- **Asynchronous Control（異步控制）**：控制指令經 MQTT 非同步下達；邊緣端以**訂閱專用執行緒**處理 `on_message`，與感測採樣／影像運算執行緒分離，確保控制延遲不受採樣週期或重運算影響。
- **State Machine（狀態機）**：繼電器模式由旗標（如 `open_auto_control`、手動／自動）與 MQTT 主題（`operation/command`、`switch/light`、`switch/watering`、`switch/auto/control`）驅動；僅在自動模式時執行 `operation/command`，狀態轉換明確。

### Failsafe Mechanisms

- **Data Integrity（數據完整性驗證）**  
  - **邊緣**：感測器讀取 **None**（DHT11 失敗）或 **0**（ADC 斷路／異常）視為無效；呼叫 **HandleAbnormal** 依項目關燈或關馬達，**不 Publish** 該筆資料，避免錯誤資料驅動後端。  
  - **後端**：以 **閾值 (Threshold)** 檢查溫溼度、亮度、水位、土壤、健康度（如溫度 16～30°C、濕度 45～65% RH、水位 ≤30% 停馬達）；僅在自動模式發送 **operation/command**，防止讀值漂移或異常值觸發錯誤動作。

- **Safety Mode（安全模式）**  
  - **上電／初始化**：GPIO **initial=GPIO.HIGH**，繼電器關閉，為安全預設。  
  - **程式結束**：**ForceStop()** 先關閉燈與馬達再斷線，確保離開時硬體進入安全狀態。  
  - **心跳偵測 (Heartbeat)** 可擴充：週期性偵測與 Broker／後端連線，逾時未收到則進入 **Safety Mode**（強制關閉繼電器），與韌體 Watchdog 思維一致。

- **Mutual Exclusion（互斥控制）**  
  - 感測器 Pi 上 **GPIO 寫入僅發生於單一執行緒**（**task_sub** 之 **on_message**）；**task_pub** 僅負責感測讀取與發佈，不寫入 GPIO，實質為**單一寫入者**，無多執行緒同時操作同一 I/O 之競態。  
  - 若未來多執行緒寫入同一硬體資源，應以 **threading.Lock** 保護 **GPIO.output()** 關鍵區段，符合工業級韌體對共用資源之互斥要求。

- **異常處理**：所有 MQTT 回呼與週期性發佈迴圈外層 **try/except**，例外處理僅記錄、不 re-raise，單一錯誤不導致程序崩潰。

---

**→ [查看詳細技術總結報告 (TECHNICAL_SUMMARY.md)](./TECHNICAL_SUMMARY.md)**

---

## 專案結構與程式碼位置

| 模組 | 路徑 | 說明 |
|------|------|------|
| **website** | `website/` | 前端 (Vue)、後端 (Flask)、MQTT 客戶端、Docker 與 Nginx 設定 |
| **sensor** | `sensor/` | 感測器與 GPIO 控制 (`mqtt_for_sensor.py`)、MQTT 基底、設定與 init 服務腳本 |
| **image_recognition** | `image_recognition/` | 影像擷取與健康度 (`mqtt_for_image.py`)、MQTT 基底、設定與服務腳本 |

對照實作建議順序：**sensor**（GPIO、感測器、HandleAbnormal／ForceStop）→ **image_recognition**（攝影機、雙執行緒）→ **website**（API、MQTT 訂閱／發佈、DB）。

---

## 硬體清單

### 感測器 (Sensors)

| 元件 | 介面 | 腳位／通道 | 用途 |
|------|------|------------|------|
| **DHT11** | 數位 (單線) | GPIO 4 (BCM) | 環境溫度、濕度 |
| **MCP3008** | SPI | SPI 0, CH0 / CH1 / CH2 | CH0：亮度；CH1：土壤濕度；CH2：水位 |

### 執行器 (Actuators)

| 元件 | 介面 | 腳位 | 電位語意 |
|------|------|------|----------|
| **燈光繼電器** | GPIO 輸出 | BCM 18 | HIGH：關燈；LOW：開燈 |
| **澆水馬達繼電器** | GPIO 輸出 | BCM 17 | HIGH：關閉；LOW：開啟（可搭配 5 秒時序） |

### 影像與運算

| 元件 | 說明 |
|------|------|
| **USB / CSI 攝影機** | OpenCV `VideoCapture(0)`，用於監控與植物健康度（綠/棕比例）分析 |

腳位與介面細部對應見 **SYSTEM_ARCHITECTURE.md**、**HARDWARE_CODE_REFERENCE.md**；感測器調度與門檻見 **HARDWARE_SPEC_AND_THRESHOLDS.md**。

---

## 環境與執行 (Environment Setup & Execution)

### 後端與週邊 (website)

- 依 **Docker Compose** 編排啟動 vue、flask、nginx、mysql、mosquitto 等服務；埠與設定見上方「容器化部署」表。
- 後端 Flask 與 MQTT 客戶端可依部署需求以不同 uWSGI 行程執行（主站 API 與 MQTT 訂閱分離）。

### 邊緣 (sensor / image_recognition)

- **sensor**：於 Raspberry Pi 上執行 `mqtt_for_sensor.py`；可透過 **systemd** 或專案內 **sensor/service/sensor** init 腳本啟動，確保開機後感測與 GPIO 服務常駐。
- **image_recognition**：於 Raspberry Pi 上執行 `mqtt_for_image.py`；可透過 **image_recognition/service/recognition** 腳本啟動。
- 兩端須能連至與後端相同之 Mosquitto Broker（TLS 8883），並設定正確之 Broker 位址、埠與憑證（見各模組 `module/config.py` 或對應設定檔）。

---

## 延伸技術文件

| 文件 | 對應概念 | 內容簡述 |
|------|----------|----------|
| **[TECHNICAL_SUMMARY.md](./TECHNICAL_SUMMARY.md)** | 技術總結 | 核心架構、Failsafe（Data Integrity、Heartbeat、Mutual Exclusion）|
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | 架構、協定 | MQTT 主題與資料流向、GPIO 與感測器／執行器對應 |
| **[FAILSAFE_AND_LOGIC.md](./FAILSAFE_AND_LOGIC.md)** | Failsafe、邏輯 | 感測異常時關閉馬達／燈具、單一錯誤不崩潰設計 |
| **[FLASK_AND_THREADING.md](./FLASK_AND_THREADING.md)** | API、多執行緒 | REST 與 MQTT 分離、雙執行緒分離影像運算與硬體監控 |
| **[HARDWARE_LIFECYCLE.md](./HARDWARE_LIFECYCLE.md)** | 生命週期 | 初始化、主迴圈、收到指令時之電位改寫與 ForceStop |
| **[HARDWARE_CODE_REFERENCE.md](./HARDWARE_CODE_REFERENCE.md)** | 硬體程式碼 | GPIO／馬達／感測器讀取區塊與異常判定註解 |
| **[HARDWARE_SPEC_AND_THRESHOLDS.md](./HARDWARE_SPEC_AND_THRESHOLDS.md)** | 門檻與調度 | 感測器讀取間隔、水位優先權與馬達乾燒保護、後端閾值 |
| **[CODE_FUNCTION_MAPPING.md](./CODE_FUNCTION_MAPPING.md)** | 程式對照 | 模組化功能表、初始化、HandleAbnormal 位置、Threading 與行號索引 |
| **[CRITICAL_CODE_ANALYSIS.md](./CRITICAL_CODE_ANALYSIS.md)** | 關鍵程式碼 | GPIO 電位實作、例外處理、異步／並行 |
| **[MODULE_OVERVIEW.md](./MODULE_OVERVIEW.md)** | 模組總覽 | website / image_recognition / sensor 功能彙整 |

---

## 技術棧摘要

| 類別 | 技術 |
|------|------|
| **Edge (Pi)** | Python 3、RPi.GPIO、Adafruit_DHT、Adafruit_MCP3008、OpenCV、paho-mqtt |
| **Backend** | Flask、paho-mqtt、MySQL、uWSGI |
| **Frontend** | Vue.js、SPA |
| **Infrastructure** | Docker Compose、Nginx、Mosquitto (MQTT)、MySQL 5.7 |

---

*本專案強調 Decoupled 架構、Data Integrity 與 Safety Mode、硬體 I/O 之 Mutual Exclusion 與穩定異常處理，適合作為軟硬體整合與工業級系統設計之參考。*
