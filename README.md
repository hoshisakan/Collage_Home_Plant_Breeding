# 家庭植栽監控系統 (Home Plant Breeding)

> 基於 **Raspberry Pi** 的軟硬體整合監控系統，具備分層架構、GPIO 硬體控制、感測器防呆與非同步監控設計，適合作為 **系統架構**、**硬體介面** 與 **穩定性思維** 的實作範例。

---

## 📌 專案簡介

本專案為一 **端對端 (End-to-End) 的物聯網監控系統**：在 **Raspberry Pi** 上執行感測器採集與繼電器控制、影像擷取與健康度分析，經 **MQTT (Mosquitto)** 與後端 **Flask API** 通訊，並透過 **Vue 前端** 提供儀表板與即時控制。設計上特別著重：

- **系統架構**：分層與模組邊界、通訊協定與資料流向的清晰定義  
- **硬體控制**：GPIO 初始化順序、電位切換語意、異常時的安全狀態 (Fail-Safe)  
- **穩定性**：感測器讀取防呆、例外處理、訂閱／發佈執行緒分離以降低 Race Condition 風險  

目標讀者包含對 **嵌入式系統**、**韌體／BIOS 介面** 與 **系統軟體** 有興趣的工程師與面試官。

---

## 🏗 系統架構 (System View)

### 分層設計 (Layered Architecture)

| 層級 | 角色 | 技術 | 職責 |
|------|------|------|------|
| **Presentation** | Vue 前端 | SPA、REST API 呼叫 | 儀表板、圖表、開關燈／澆水／手動拍照 |
| **Application** | Flask 後端 | REST、MQTT 客戶端、DB | API 提供、MQTT 訂閱／發佈、資料持久化、控制指令下達 |
| **Message Broker** | Mosquitto | MQTT、TLS 8883 | 感測資料、影像、控制指令的集中轉發 |
| **Edge - 感測** | sensor (Raspberry Pi) | RPi.GPIO、DHT11、MCP3008、MQTT | 感測器讀取、繼電器輸出、定時上報與指令回應 |
| **Edge - 影像** | image_recognition (Raspberry Pi) | OpenCV、MQTT | 攝影機擷取、健康度計算、定時／手動上傳 |

控制與資料流：**使用者 → 前端 → Flask → MQTT → 感測器 Pi (GPIO)**；**感測器 Pi / 影像 Pi → MQTT → Flask → DB / 前端**。邊緣裝置不直接暴露 HTTP，僅透過 **Protocol Integration (MQTT)** 與後端耦合。

### 容器化部署 (website 模組)

後端與週邊服務以 **Docker Compose** 編排，便於環境一致與擴展：

| 服務 | 說明 | 埠 |
|------|------|-----|
| **vue** | 前端建置與開發 | 8082→8080, 8081→8086 |
| **flask** | 後端 API + uWSGI | 5000, 5001 |
| **nginx** | 反向代理、靜態與 SSL | 80, 443 |
| **mysql** | 感測／健康度／繼電器狀態儲存 | 3306 |
| **mosquitto** | MQTT Broker (TLS 8883) | 1883, 8883, 9001, 9002 |
| **phpMyAdmin** | DB 管理 (可選) | 8080 |

Raspberry Pi 端 (sensor、image_recognition) 在裝置上以 **原生 Python + systemd / init 腳本** 執行，透過網路連至同一 Mosquitto Broker，與容器化後端協同運作。

---

## 🔬 深度技術導覽 (Technical Deep Dive)

以下文件為本專案在 **系統架構**、**硬體控制**、**邏輯與 Failsafe**、**Flask 與多執行緒** 上的核心說明，並對應 **BIOS／嵌入式系統** 常見的設計關注點。

### 核心文件一覽

| 文件 | 對應概念 | 核心內容簡述 |
|------|----------|----------------|
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | **Layered Architecture**、**Protocol Integration** | 系統全局架構、MQTT 主題與資料流向、Raspberry Pi GPIO 與感測器／執行器對應、Flask 與 MQTT 的整合方式 |
| **[HARDWARE_LIFECYCLE.md](./HARDWARE_LIFECYCLE.md)** | **Initialization**、**Main Loop**、**Fail-Safe** | 硬體控制腳本的程式生命週期：GPIO 與 SPI 初始化順序、主迴圈週期（感測 5s／影像 10s）、收到網頁指令時的電位改寫與異常時強制關閉繼電器 |
| **[CRITICAL_CODE_ANALYSIS.md](./CRITICAL_CODE_ANALYSIS.md)** | **Resource / Concurrency**、**Exception Handling** | GPIO 高低電位實作、感測器讀取防呆（None / 0 檢查、HandleAbnormal）、訂閱／發佈雙執行緒設計（loop_forever vs loop_start）以降低 **Race Condition** 風險、OpenCV 與感測器讀取的異步執行方式 |
| **[HARDWARE_CODE_REFERENCE.md](./HARDWARE_CODE_REFERENCE.md)** | **GPIO / SPI / 硬體初始化** | 專案內**所有** GPIO、馬達驅動、感測器讀取（SPI MCP3008、DHT11）的程式碼區塊彙整，附硬體初始化與異常判定註解 |
| **[FAILSAFE_AND_LOGIC.md](./FAILSAFE_AND_LOGIC.md)** | **Failsafe**、**單一錯誤不崩潰** | 感測器異常時如何決定關閉馬達／燈具（邊緣 HandleAbnormal、後端門檻與 operation/command）；try/except 與不 re-raise 的設計，確保單一錯誤不導致系統崩潰 |
| **[FLASK_AND_THREADING.md](./FLASK_AND_THREADING.md)** | **Flask API**、**多執行緒** | REST 與 MQTT 應用分離、與硬體／影像相關的 API 路由；影像辨識結果傳遞路徑（影像 Pi → 後端存檔／DB／警報；硬體控制由感測器資料 → operation/command）；雙執行緒分離影像運算與即時硬體監控 |
| **[CODE_FUNCTION_MAPPING.md](./CODE_FUNCTION_MAPPING.md)** | **程式與功能對照** | 模組化功能對照表（主要 Python 檔與 GPIO／Relay／Sensors 對應）；初始化流程、感測器 0／Null 時立即關閉繼電器之程式段落、Threading 併發、Long-run 穩定性要點與行號索引 |
| **[HARDWARE_SPEC_AND_THRESHOLDS.md](./HARDWARE_SPEC_AND_THRESHOLDS.md)** | **感測器調度與門檻** | 感測器調度對照表（DHT11、土壤、水位、光照之實際讀取間隔與建議生產環境數值）；**水位**最高採樣優先權與馬達乾燒保護（Failsafe）；後端門檻值參考 |

### 技術要點條列

- **Initialization**：BCM 腳位、OUT 模式、`initial=GPIO.HIGH` 安全預設；SPI (MCP3008) 與 DHT11 讀取時機；硬體相關程式碼僅在 **sensor/mqtt_for_sensor.py**，見 [HARDWARE_CODE_REFERENCE.md](./HARDWARE_CODE_REFERENCE.md)。
- **Protocol Integration**：MQTT 主題定義（如 `env/plant/detection/data`、`switch/light`、`operation/command`）作為控制與資料契約；TLS 8883 連線。
- **Failsafe**：感測器讀取失敗或為 0 時 **HandleAbnormal** 依項目關燈／關馬達並寫 error log；主迴圈不推送無效資料；**ForceStop** 離開前強制關閉繼電器；後端門檻判斷產生 **operation/command** 與 OneSignal 警報，詳見 [FAILSAFE_AND_LOGIC.md](./FAILSAFE_AND_LOGIC.md)。
- **Exception Handling**：on_message、DataPublisher、DataSubscriber 等外層 try/except → CatchError，僅記錄不 re-raise，單一錯誤不中斷 MQTT 迴圈或程序。
- **Concurrency**：訂閱端 `Connect(False)` → `loop_forever()`（專職收訊）；發佈端 `Connect(True)` → `loop_start()` + 主迴圈；後端 WebClient 以 **threading.Thread** 跑 **loop_forever()**；影像 Pi 與感測器 Pi 分機且各自雙執行緒，確保**影像運算不影響即時硬體監控**，詳見 [FLASK_AND_THREADING.md](./FLASK_AND_THREADING.md)。

### Flask、硬體程式碼與 Failsafe 摘要（對應三份延伸文件）

| 主題 | 摘要 |
|------|------|
| **Flask API 與多執行緒** ([FLASK_AND_THREADING.md](./FLASK_AND_THREADING.md)) | 主站 API（create_app）與 MQTT 應用（create_mqtt_app）分離；硬體／手動拍照經 **MqttClient** 發佈至 MQTT，由 Pi 端訂閱執行。影像辨識結果（原圖、辨識圖、健康度）→ 後端存檔／DB／警報；硬體控制由 **env/plant/detection/data** → 門檻 → **operation/command** → 感測器 Pi。影像 Pi 與感測器 Pi 各以**雙執行緒**分離「訂閱」與「發佈＋運算／採樣」，影像運算不阻塞硬體監控。 |
| **硬體程式碼彙整** ([HARDWARE_CODE_REFERENCE.md](./HARDWARE_CODE_REFERENCE.md)) | 所有 GPIO、馬達、感測器讀取（SPI MCP3008、DHT11）皆在 **sensor/mqtt_for_sensor.py**；初始化為 BCM、OUT、initial=HIGH；異常時 **HandleAbnormal** 依 key 關燈／關馬達並寫 log；**ForceStop** 離開前將兩腳設 HIGH。 |
| **Failsafe 與邏輯** ([FAILSAFE_AND_LOGIC.md](./FAILSAFE_AND_LOGIC.md)) | **邊緣**：讀取 None／0 → HandleAbnormal 關燈或關馬達、不推送。**後端**：門檻判斷（溫溼度、亮度、土壤、水位）產生 operation/command 與 OneSignal 警報，僅自動模式時發送 operation/command。**單一錯誤不崩潰**：on_message、DataPublisher、CollectSensorData 等外層 try/except，CatchError 只記錄不 re-raise。 |
| **程式與功能對照** ([CODE_FUNCTION_MAPPING.md](./CODE_FUNCTION_MAPPING.md)) | 三模組之**主要 Python 檔 ↔ GPIO／Relay／Sensors** 對照表；**初始化流程**（sensor 模組載入時 BCM、SPI、繼電器 initial=HIGH）；**感測器 0／Null → 立即關閉繼電器**之 HandleAbnormal 程式位置（約 219–234 行）；**Threading** 分離影像分析與硬體 I/O；**Long-run 穩定性**（安全預設、無效資料不推送、單一錯誤不崩潰、結束時 ForceStop）與行號索引。 |
| **感測器調度與門檻** ([HARDWARE_SPEC_AND_THRESHOLDS.md](./HARDWARE_SPEC_AND_THRESHOLDS.md)) | **感測器調度對照表**：DHT11、土壤、水位、光照之實際讀取間隔（現為 5 秒）與**建議生產環境數值**（水位 3～5 秒、光照 5～10 秒、土壤 10～20 秒、DHT11 15～30 秒）。**水位**具最高採樣優先權（馬達乾燒保護 Failsafe）。後端門檻（溫溼度、亮度、水位、土壤）參考。 |

詳細程式碼位置與流程請直接參閱上述各份文件。

---

## 📁 專案結構與程式碼位置

| 模組 | 路徑 | 說明 |
|------|------|------|
| **website** | `website/` | 前端 (Vue)、後端 (Flask)、MQTT 客戶端、Docker 與 Nginx 設定 |
| **sensor** | `sensor/` | 感測器與 GPIO 控制腳本 (`mqtt_for_sensor.py`)、MQTT 基底、設定與 init 服務腳本 |
| **image_recognition** | `image_recognition/` | 影像擷取與健康度腳本 (`mqtt_for_image.py`)、MQTT 基底、設定與服務指令說明 |

若需對照實作，可依序查閱：**sensor**（GPIO、感測器、例外處理）→ **image_recognition**（攝影機、雙執行緒）→ **website**（API、MQTT 訂閱／發佈、DB）。

---

## 🔧 硬體清單

### 感測器 (Sensors)

| 元件 | 介面 | 腳位／通道 | 用途 |
|------|------|------------|------|
| **DHT11** | 數位 (單線) | GPIO 4 (BCM) | 環境溫度、濕度 |
| **MCP3008** | SPI | SPI 0, CH0 / CH1 / CH2 | CH0：環境亮度；CH1：土壤濕度；CH2：水位深度 |

### 執行器 (Actuators)

| 元件 | 介面 | 腳位 | 電位語意 |
|------|------|------|----------|
| **燈光繼電器** | GPIO 輸出 | BCM 18 | HIGH：關燈；LOW：開燈 |
| **澆水馬達繼電器** | GPIO 輸出 | BCM 17 | HIGH：關閉；LOW：開啟（可搭配 5 秒時序） |

### 影像與運算

| 元件 | 說明 |
|------|------|
| **USB / CSI 攝影機** | OpenCV `VideoCapture(0)` 擷取，用於監控與植物健康度（綠/棕比例）分析 |

上述腳位與介面在 **SYSTEM_ARCHITECTURE.md**、**HARDWARE_LIFECYCLE.md**、**CRITICAL_CODE_ANALYSIS.md** 與 **HARDWARE_CODE_REFERENCE.md** 中有更細的對應與程式碼引用。**感測器讀取間隔**與**建議生產環境數值**、**水位最高採樣優先權**（馬達乾燒保護）及後端門檻見 **[HARDWARE_SPEC_AND_THRESHOLDS.md](./HARDWARE_SPEC_AND_THRESHOLDS.md)**。

---

## 📄 文件索引

| 文件 | 用途 |
|------|------|
| **README.md**（本檔） | 專案總覽、系統觀點、技術導覽與硬體清單 |
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | 系統全局架構、通訊協定與 MQTT 主題 |
| **[HARDWARE_LIFECYCLE.md](./HARDWARE_LIFECYCLE.md)** | 硬體控制腳本生命週期（初始化、主迴圈、指令觸發） |
| **[CRITICAL_CODE_ANALYSIS.md](./CRITICAL_CODE_ANALYSIS.md)** | GPIO 控制、例外處理、異步／並行實作 |
| **[HARDWARE_CODE_REFERENCE.md](./HARDWARE_CODE_REFERENCE.md)** | GPIO／馬達／感測器讀取程式碼彙整與硬體初始化、異常判定註解 |
| **[FAILSAFE_AND_LOGIC.md](./FAILSAFE_AND_LOGIC.md)** | 感測器異常時的 Failsafe 邏輯（關閉馬達／燈具）、單一錯誤不崩潰設計 |
| **[FLASK_AND_THREADING.md](./FLASK_AND_THREADING.md)** | Flask API 與多執行緒、影像辨識結果傳遞、影像運算與硬體監控分離 |
| **[CODE_FUNCTION_MAPPING.md](./CODE_FUNCTION_MAPPING.md)** | 軟硬體控制邏輯對照（模組化功能表、初始化、異常關閉繼電器、併發、Long-run 穩定性與行號索引） |
| **[HARDWARE_SPEC_AND_THRESHOLDS.md](./HARDWARE_SPEC_AND_THRESHOLDS.md)** | 感測器調度對照表（讀取間隔、建議生產環境數值）、水位最高採樣優先權與馬達乾燒保護、後端門檻參考 |
| **[MODULE_OVERVIEW.md](./MODULE_OVERVIEW.md)** | website / image_recognition / sensor 功能彙整 |

---

## ⚙ 技術棧摘要

| 類別 | 技術 |
|------|------|
| **Edge (Pi)** | Python 3、RPi.GPIO、Adafruit_DHT、Adafruit_MCP3008、OpenCV、paho-mqtt |
| **Backend** | Flask、paho-mqtt、MySQL、uWSGI |
| **Frontend** | Vue.js、SPA |
| **Infrastructure** | Docker Compose、Nginx、Mosquitto (MQTT)、MySQL 5.7 |

---

*本專案強調可讀的架構分層、明確的硬體介面語意與穩健的異常處理，適合作為軟硬體整合與系統設計的參考實例。*
