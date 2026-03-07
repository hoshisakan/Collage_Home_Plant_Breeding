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

以下三份文件為本專案在 **系統架構**、**硬體生命週期** 與 **關鍵程式行為** 上的核心說明，並對應 **BIOS／嵌入式系統** 常見的設計關注點。

| 文件 | 對應概念 | 核心內容簡述 |
|------|----------|----------------|
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | **Layered Architecture**、**Protocol Integration** | 系統全局架構、MQTT 主題與資料流向、Raspberry Pi GPIO 與感測器／執行器對應、Flask 與 MQTT 的整合方式 |
| **[HARDWARE_LIFECYCLE.md](./HARDWARE_LIFECYCLE.md)** | **Initialization**、**Main Loop**、**Fail-Safe** | 硬體控制腳本的程式生命週期：GPIO 與 SPI 初始化順序、主迴圈週期（感測 5s／影像 10s）、收到網頁指令時的電位改寫與異常時強制關閉繼電器 |
| **[CRITICAL_CODE_ANALYSIS.md](./CRITICAL_CODE_ANALYSIS.md)** | **Resource / Concurrency**、**Exception Handling** | GPIO 高低電位實作、感測器讀取防呆（None / 0 檢查、HandleAbnormal）、訂閱／發佈雙執行緒設計（loop_forever vs loop_start）以降低 **Race Condition** 風險、OpenCV 與感測器讀取的異步執行方式 |

### 技術要點條列

- **Initialization**：BCM 腳位、OUT 模式、`initial=GPIO.HIGH` 安全預設；SPI (MCP3008) 與 DHT11 讀取時機。
- **Protocol Integration**：MQTT 主題定義（如 `env/plant/detection/data`、`switch/light`、`operation/command`）作為控制與資料契約；TLS 8883 連線。
- **Exception Handling**：感測器回傳 `None` 或 0 時不推送、觸發 HandleAbnormal 關閉燈／馬達並寫 log；on_message 與主迴圈外層 try/except 避免單點錯誤導致程序崩潰。
- **Concurrency**：訂閱端 `Connect(False)` → `loop_forever()`（單一執行緒專職收訊）；發佈端 `Connect(True)` → `loop_start()` + 主迴圈（感測或影像），兩者分離以減少共用狀態競爭。

詳細程式碼位置與流程請直接參閱上述三份文件。

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

上述腳位與介面在 **SYSTEM_ARCHITECTURE.md**、**HARDWARE_LIFECYCLE.md** 與 **CRITICAL_CODE_ANALYSIS.md** 中有更細的對應與程式碼引用。

---

## 📄 文件索引

| 文件 | 用途 |
|------|------|
| **README.md**（本檔） | 專案總覽、系統觀點、技術導覽與硬體清單 |
| **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** | 系統全局架構、通訊協定與 MQTT 主題 |
| **[HARDWARE_LIFECYCLE.md](./HARDWARE_LIFECYCLE.md)** | 硬體控制腳本生命週期（初始化、主迴圈、指令觸發） |
| **[CRITICAL_CODE_ANALYSIS.md](./CRITICAL_CODE_ANALYSIS.md)** | GPIO 控制、例外處理、異步／並行實作 |
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
