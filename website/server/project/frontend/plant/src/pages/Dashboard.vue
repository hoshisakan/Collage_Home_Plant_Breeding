<template>
    <div class="content">
        <div class="usernameStyle">Welcome! {{ loginUsername }}</div>
        <div class="md-layout">
            <!-- 顯示植物的健康度 -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="green">
                    <template slot="header">
                        <md-icon>filter_vintage</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">植物健康狀態</p>
                        <h3 class="title">
                            <!-- 植物健康度的數值 -->
                            {{ plant_health_value }}
                            <small>%</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <!-- 若植物生長情況良好，則顯示花朵的圖標 -->
                            <div v-if="plant_health_check">
                                <md-icon>filter_vintage</md-icon>
                            </div>
                            <!-- 反之，則顯示警告的圖標 -->
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                                <!-- 植物生長情況 -->
                            </div>
                            {{ plant_health_status }}
                            <div>
                                <md-icon>update</md-icon>
                                <!-- 感測器的偵測時間 -->
                                {{ plant_health_data_update_date }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>

            <!-- 顯示環境的亮度 -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="orange">
                    <template slot="header">
                        <md-icon>wb_sunny</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">環境亮度</p>
                        <h3 class="title">
                            <!-- 環境亮度的數值 -->
                            {{ brightness }}
                            <small>%</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <div v-if="brightness_sensor_check">
                                <md-icon>brightness_high</md-icon>
                            </div>
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                            </div>
                            <!-- 環境亮度的狀態 -->
                            {{ brightness_sensor_status }}
                            <div>
                                <md-icon>update</md-icon>
                                <!-- 感測器的偵測時間 -->
                                {{ detection_time }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>

            <!-- 顯示土壤的濕度 -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="blue">
                    <template slot="header">
                        <md-icon>eco</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">土壤濕度</p>
                        <h3 class="title">
                            <!-- 土壤濕度的數值 -->
                            {{ soil_moisture }}
                            <small>%</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <div v-if="soil_moisture_sensor_check">
                                <md-icon>eco</md-icon>
                            </div>
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                            </div>
                            <!-- 土壤水分的狀態 -->
                            {{ soil_moisture_sensor_status }}
                            <div>
                                <md-icon>update</md-icon>
                                <!-- 感測器的偵測時間 -->
                                {{ detection_time }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>

            <!-- 顯示水位深度(剩餘水量) -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="purple">
                    <template slot="header">
                        <md-icon>grain</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">水位偵測</p>
                        <h3 class="title">
                            <!-- 水位深度的數值 -->
                            {{ water_level }}
                            <small>%</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <div v-if="water_level_check">
                                <md-icon>grain</md-icon>
                            </div>
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                            </div>
                            <!-- 剩餘水量的狀態 -->
                            {{ water_level_status }}
                            <div>
                                <md-icon>update</md-icon>
                                {{ detection_time }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>

            <!-- 顯示環境的溫度 -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="red">
                    <template slot="header">
                        <md-icon>flare</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">環境溫度</p>
                        <h3 class="title">
                            <!-- 環境溫度的數值 -->
                            {{ temperature }}
                            <small>℃</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <div v-if="temperature_sensor_check">
                                <md-icon>flare</md-icon>
                            </div>
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                            </div>
                            <!-- 環境溫度的狀態 -->
                            {{ temperature_sensor_status }}
                            <div>
                                <md-icon>update</md-icon>
                                <!-- 感測器的偵測時間 -->
                                {{ detection_time }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>

            <!-- 顯示環境的濕度 -->
            <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
                <stats-card data-background-color="blue">
                    <template slot="header">
                        <md-icon>grid_on</md-icon>
                    </template>

                    <template slot="content">
                        <p class="category">環境濕度</p>
                        <h3 class="title">
                            <!-- 環境濕度的數值 -->
                            {{ humidity }}
                            <small>%RH</small>
                        </h3>
                    </template>

                    <template slot="footer">
                        <div class="stats">
                            <div v-if="humidity_sensor_check">
                                <md-icon>grid_on</md-icon>
                            </div>
                            <div v-else>
                                <md-icon class="text-danger">warning</md-icon>
                            </div>
                            <!-- 環境濕度的狀態 -->
                            {{ humidity_sensor_status }}
                            <div>
                                <!-- 感測器的偵測時間 -->
                                <md-icon>update</md-icon>
                                {{ detection_time }}
                            </div>
                        </div>
                    </template>
                </stats-card>
            </div>
        </div>

        <div class="md-layout md-alignment-center">
            <!-- 顯示原圖 -->
            <div class="md-layout-item">
                <image-card data-background-color="orange">
                    <template slot="image-header">
                        <h4 class="title">原圖</h4>
                        <p class="category">植物生長情況</p>
                    </template>
                    <template slot="image-content">
                        <!-- 掛載原圖，若無則顯示Empty -->
                        <img :src="latest_image_stream" alt="Empty" />
                    </template>
                    <!-- <template slot="image-footer">
                        <div class="stats">
                            <div>
                                <md-icon>update</md-icon>
                                原圖建立的時間
                                {{ latest_image_stream_date }}
                            </div>
                        </div>
                    </template> -->
                </image-card>
            </div>
            <!-- 顯示影像辨識的圖像 -->
            <div class="md-layout-item">
                <image-card data-background-color="orange">
                    <template slot="image-header">
                        <h4 class="title">辨識圖像</h4>
                        <p class="category">健康度顯示</p>
                    </template>
                    <template slot="image-content">
                        <!-- 掛載辨識圖像，若無則顯示Empty -->
                        <img :src="latest_anatomy_image_stream" alt="Empty" />
                    </template>
                    <!-- <template slot="image-footer">
                        <div class="stats">
                            <div>
                                <md-icon>update</md-icon>
                                辨識圖像建立的時間
                                {{ latest_anatomy_image_stream_date }}
                            </div>
                        </div>
                    </template> -->
                </image-card>
            </div>
        </div>
    </div>
</template>

<script>
// 引入axios
import axios from 'axios'

import { StatsCard, ImageCard } from '@/components'

export default {
    components: {
        StatsCard,
        ImageCard,
    },
    data() {
        return {
            // 儲存感測器所有的數值
            detection_items: [],
            // 儲存感測器的環境溫度的數值
            temperature: 0,
            // 儲存感測器的環境濕度的數值
            humidity: 0,
            // 儲存感測器的環境亮度的數值
            brightness: 0,
            // 儲存感測器的土壤濕度的數值
            soil_moisture: 0,
            // 儲存感測器的水位深度(剩餘水量)的數值
            water_level: 0,
            // 儲存感測器的偵測時間
            detection_time: '',
            // 計時器
            timer: '',
            // 儲存環境亮度的狀態
            brightness_sensor_status: '',
            // 儲存環境濕度的狀態
            humidity_sensor_status: '',
            // 儲存環境溫度的狀態
            temperature_sensor_status: '',
            // 儲存土壤濕度的狀態
            soil_moisture_sensor_status: '',
            // 儲存水位深度(剩餘水量)的狀態
            water_level_status: '',
            // 儲存環境濕度數值的檢查結果
            humidity_sensor_check: false,
            // 儲存環境亮度數值的檢查結果
            brightness_sensor_check: false,
            // 儲存土壤濕度數值的檢查結果
            soil_moisture_sensor_check: false,
            // 儲存環境溫度數值的檢查結果
            temperature_sensor_check: false,
            // 儲存水位深度數值的檢查結果
            water_level_check: false,
            // 儲存原圖像
            latest_image_stream: '',
            // 儲存原圖像建立的日期
            latest_image_stream_date: '',
            // 儲存辨識圖像
            latest_anatomy_image_stream: '',
            // 儲存辨識圖像建立的日期
            latest_anatomy_image_stream_date: '',
            // 儲存錯誤訊息
            errorMessage: '',
            // 儲存植物健康度的所有資料
            plant_health_items: '',
            // 儲存植物健康度的數值
            plant_health_value: '',
            // 儲存植物健康度的辨識時間
            plant_health_data_update_date: '',
            // 儲存植物的健康狀態
            plant_health_status: '',
            // 儲存植物健康度的檢查結果
            plant_health_check: false,
            loginAuthToken: '',
            loginAllow: '',
            loginUsername: '',
        }
    },
    mounted() {
        // 載入頁面且動態變數已經初始化完時執行每秒抓取資料的函式
        this.CheckLoginAllow()
        // this.LoginTimeOutCheck()
    },
    // 監控感測器所有數值與植物健康度的數值其變化，只要資料更新就會執行
    watch: {
        // 監控環境溫度的數值
        temperature: function (latestData) {
            // 檢查並更新環境溫度的狀態
            this.CheckTemperature(latestData)
        },
        // 監控環境濕度的數值
        humidity: function (latestData) {
            // 檢查並更新環境濕度的狀態
            this.CheckEnvironmentHumidity(latestData)
        },
        // 監控環境亮度的數值
        brightness: function (latestData) {
            // 檢查並更新環境亮度的狀態
            this.CheckBrightness(latestData)
        },
        // 監控土壤濕度的數值
        soil_moisture: function (latestData) {
            // 檢查並更新土壤濕度的狀態
            this.CheckSoilMoisture(latestData)
        },
        // 監控水位深度的數值
        water_level: function (latestData) {
            // 檢查並更新水位深度的狀態
            this.CheckWaterLevel(latestData)
        },
        // 監控植物健康度的數值
        plant_health_value: function (latestData) {
            // 檢查並更新植物的健康狀態
            this.CheckPlantHealth(latestData)
        },
    },
    methods: {
        CheckLoginAllow() {
            const readLoginStatus = window.localStorage.getItem('loginAuthToken')
            if (readLoginStatus === '' || readLoginStatus === null) {
                this.loginAuthToken = ''
                this.loginAllow = false
                window.localStorage.setItem('loginAuthToken', this.loginAuthToken)
                // alert('test')
                if (this.loginAllow === false) {
                    this.$router.push({ path: '/validate/login' })
                }
            } else if (readLoginStatus !== '') {
                this.loginAuthToken = readLoginStatus
                this.loginAllow = true
                this.InitTimer()
                this.InitUsername()
            }
        },
        InitUsername() {
            const readLoginUsername = window.localStorage.getItem('loginUsername')
            if (readLoginUsername === '' || readLoginUsername === null) {
                axios
                    .post('https://hoshi-plant.serveirc.com/login/user/name/get', {
                        authToken: this.loginAuthToken,
                    })
                    .then((response) => {
                        this.loginUsername = response.data.username
                        window.localStorage.setItem('loginUsername', this.loginUsername)
                    })
                    .catch((error) => {
                        this.errorMessage = error
                        alert(this.errorMessage)
                    })
            } else {
                this.loginUsername = readLoginUsername
            }
        },
        // LoginTimeOutCheck () {
        //   this.timer = setInterval(() => {
        //     const readLoginUsername = window.localStorage.getItem('loginUsername')
        //     console.log(readLoginUsername)
        //     console.log(this.loginUsername)
        //     if (this.loginUsername === '') {
        //       alert('登入逾時!')
        //       this.$router.push({ path: '/validate/logout' })
        //     }
        //   }, 10000)
        // },
        GetAllData() {
            // 抓取感測器的所有數值
            this.GetDetectionValue()
            // 抓取植物健康度的所有資料
            this.GetPlantHealthData()
            // 抓取原圖
            this.GetMonitorImageStream(true)
            // // 抓取原圖的創建時間
            // this.GetMonitorImageStream(false)
            // 抓取影像辨識圖像
            this.GetAnatomyMonitorImageStream(true)
            // // 抓取影像辨識圖像的創建時間
            // this.GetAnatomyMonitorImageStream(false)
        },
        // 設置計時器每秒抓取資料與圖像
        InitTimer() {
            this.GetAllData()
            this.timer = setInterval(() => {
                this.GetAllData()
            }, 1000)
        },
        // 抓取感測器的所有數值
        GetDetectionValue() {
            // 以GET的方式向後端請求感測器的所有資料
            axios
                .get('https://hoshi-plant.serveirc.com/env/data')
                .then((response) => {
                    // 儲存感測器所有的資料
                    this.detection_items = response.data
                    //console.log(this.detection_items)
                    this.temperature = this.detection_items.d_dht11_t
                    this.humidity = this.detection_items.d_dht11_h
                    this.water_level = this.detection_items.d_water_level
                    this.brightness = this.detection_items.d_light
                    this.soil_moisture = this.detection_items.d_soil
                    this.detection_time = this.detection_items.d_created_date
                })
                .catch((error) => {
                    this.errorMessage = 'env value error is:' + error
                    // alert(this.errorMessage)
                })
        },
        // 抓取植物健康度的所有資料
        GetPlantHealthData() {
            // 以GET的方式向後端請求植物健康度的所有資料
            axios
                .get('https://hoshi-plant.serveirc.com/env/plant/health/data')
                .then((response) => {
                    // 儲存植物健康度所有的資料
                    this.plant_health_items = response.data
                    this.plant_health_value = this.plant_health_items.health_status
                    this.plant_health_data_update_date = this.plant_health_items.data_created_date
                })
                .catch((error) => {
                    this.errorMessage = error
                })
        },
        // 抓取原圖與其創建的時間
        GetMonitorImageStream(excMode) {
            // 以POST的方式向後端請求植物的原圖與其創建時間，True是請求圖像，False是請求圖像的創建時間
            axios
                .post('https://hoshi-plant.serveirc.com/env/data/image', {
                    mode: excMode,
                })
                .then((response) => {
                    if (excMode === true) {
                        // 以POST的方式向後端請求植物的原圖
                        this.latest_image_stream = 'data:image/png;base64,' + response.data
                        // 以POST的方式向後端請求植物原圖的創建時間
                    } else {
                        this.latest_image_stream_date = response.data
                    }
                })
                .catch((error) => {
                    this.errorMessage = error
                })
        },
        // 抓取影像辨識圖像與其創建的時間
        GetAnatomyMonitorImageStream(excMode) {
            // 以POST的方式向後端請求植物的辨識圖像與其創建時間，True是請求辨識圖像，False是請求辨識圖像的創建時間
            axios
                .post('https://hoshi-plant.serveirc.com/env/data/image/anatomy/plant', {
                    mode: excMode,
                })
                .then((response) => {
                    // 以POST的方式向後端請求植物的辨識圖像
                    if (excMode === true) {
                        this.latest_anatomy_image_stream = 'data:image/png;base64,' + response.data
                        // 以POST的方式向後端請求植物辨識圖像的創建時間
                    } else {
                        this.latest_anatomy_image_stream_date = response.data
                    }
                })
                .catch((error) => {
                    this.errorMessage = error
                })
        },
        // 檢查並更新環境溫度的狀態
        CheckTemperature(temperature) {
            if (temperature > 0) {
                // 若環境溫度數值過高或過低
                if (temperature < 16 || temperature > 30) {
                    // 若環境溫度數值過高
                    if (temperature < 16) {
                        // 更新狀態與檢查結果
                        this.temperature_sensor_status = '環境溫度過低'
                        this.temperature_sensor_check = false
                        // 若環境溫度數值過低
                    } else {
                        // 更新狀態與檢查結果
                        this.temperature_sensor_status = '環境溫度過高'
                        this.temperature_sensor_check = false
                    }
                    // 若環境溫度數值適中
                } else {
                    // 更新狀態與檢查結果
                    this.temperature_sensor_status = '環境溫度適中'
                    this.temperature_sensor_check = true
                }
                // 若環境溫度數值等於零
            } else {
                // 更新狀態與檢查結果
                this.temperature_sensor_status = '環境溫度感測器異常'
                this.temperature_sensor_check = false
            }
        },
        // 檢查並更新環境濕度的狀態
        CheckEnvironmentHumidity(humidity) {
            if (humidity > 0) {
                // 若環境濕度數值適中
                if (humidity >= 45 && humidity <= 65) {
                    // 更新狀態與檢查結果
                    this.humidity_sensor_status = '環境濕度適中'
                    this.humidity_sensor_check = true
                    // 若環境濕度數值過高
                } else if (humidity > 65) {
                    this.humidity_sensor_status = '環境濕度過高'
                    this.humidity_sensor_check = false
                    // 若環境濕度數值過低
                } else if (humidity < 45) {
                    this.humidity_sensor_status = '環境濕度過低'
                    this.humidity_sensor_check = false
                }
                // 若環境濕度數值等於零
            } else {
                // 更新狀態與檢查結果
                this.humidity_sensor_status = '環境濕度感測器異常'
                this.humidity_sensor_check = false
            }
        },
        // 檢查並更新水位深度的狀態
        CheckWaterLevel(waterLevel) {
            if (waterLevel > 0) {
                // 若剩餘水量不足
                if (waterLevel > 700) {
                    // 更新狀態與檢查結果
                    this.water_level_status = '水量過低'
                    this.water_level_check = false
                    // 若剩餘水量足夠
                } else if (waterLevel < 700) {
                    this.water_level_status = '水量充足'
                    this.water_level_check = true
                }
                // 若剩餘水量數值等於零
            } else {
                // 更新狀態與檢查結果
                this.water_level_status = '水位深度感測器異常'
                this.water_level_check = false
            }
        },
        // 檢查並更新環境亮度的狀態
        CheckBrightness(brightness) {
            if (brightness > 0) {
                // 若環境亮度不足
                if (brightness <= 51) {
                    this.brightness_sensor_status = '日照光線不足'
                    this.brightness_sensor_check = false
                    // 若環境亮度充足
                } else {
                    this.brightness_sensor_status = '日照光線充足'
                    this.brightness_sensor_check = true
                }
                // 若環境亮度數值等於零
            } else {
                // 更新狀態與檢查結果
                this.brightness_sensor_status = '光感測器異常'
                this.brightness_sensor_check = false
            }
        },
        // 檢查並更新土壤濕度的狀態
        CheckSoilMoisture(soilMoisture) {
            if (soilMoisture > 0) {
                // 若土壤水分不足
                if (soilMoisture < 31) {
                    // 更新狀態與檢查結果
                    this.soil_moisture_sensor_status = '土壤水分不足'
                    this.soil_moisture_sensor_check = false
                    // 若土壤水分充足
                } else {
                    this.soil_moisture_sensor_status = '土壤水分充足'
                    this.soil_moisture_sensor_check = true
                }
                // 若土壤濕度數值等於零
            } else if (soilMoisture <= 0) {
                // 更新狀態與檢查結果
                this.soil_moisture_sensor_status = '土壤濕度感測器異常'
                this.soil_moisture_sensor_check = false
            }
        },
        // 檢查並更新植物的健康狀態
        CheckPlantHealth(plantHealthValue) {
            if (plantHealthValue > 0) {
                // 若植物生長良好
                if (plantHealthValue > 40) {
                    // 更新狀態與檢查結果
                    this.plant_health_status = '植物生長良好'
                    this.plant_health_check = true
                    // 若植物生長情況不良
                } else {
                    // 更新狀態與檢查結果
                    this.plant_health_status = '植物生長不良'
                    this.plant_health_check = false
                }
            }
        },
    },
    // 銷毀頁面前清除計時器，即是切換頁面或關閉頁面的時候會被執行
    beforeDestroy() {
        clearInterval(this.timer)
    },
}
</script>
<style lang="scss" scoped>
    .usernameStyle {
        font-size: 20px;
        text-align: right;
    }
    @import "node_modules/vue-material/dist/theme/engine";
</style>
