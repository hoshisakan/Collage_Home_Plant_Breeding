<template>
  <div class="content">
    <div class="usernameStyle">Welcome! {{ loginUsername }}</div>
    <div class="md-layout">
      <div class='md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100'>
          <nav-tabs-card>
            <template slot='content'>
              <span class='md-nav-tabs-title'>圖表分析:</span>
              <md-tabs class='md-success' md-alignment='left'>
                <!-- 顯示所有的資料 -->
                <md-tab id='tab-home' md-label='綜合分析' md-icon='home'>
                  <div class='md-layout'>
                    <div class="md-layout-item">
                    </div>
                    <div class="md-layout-item">
                    </div>
                    <div class="md-layout-item">
                      <md-field>
                        <label for="averageDataQuantity">資料筆數</label>
                        <!-- 選擇資料的筆數 -->
                        <md-select v-model="averageDataQuantity" name="averageDataQuantity"
                            id="averageDataQuantity" @md-selected="GetSpecificQuantityAverageData">
                          <md-option value="5">5</md-option>
                          <md-option value="10">10</md-option>
                          <md-option value="15">15</md-option>
                        </md-select>
                      </md-field>
                    </div>
                  </div>
                  <!-- 以橫條圖顯示感測器的環境環境亮度與土壤濕度，以及剩餘水量 -->
                  <bar-chart
                    :chartTitle='ChartTitle'
                    :chartSubTitle='averageChartSubTitle'
                    :chartData='averageChartData'
                    :chartColor='averageChartColor'
                    :chartHeight='averageChartHeight'
                  >
                  </bar-chart>
                </md-tab>

                <!-- 僅顯示環境亮度 -->
                <md-tab id='tab-pages' md-label='環境亮度' md-icon='brightness_high'>
                  <div class='md-layout'>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                      <md-field>
                        <label for="brightnessDataQuantity">資料筆數</label>
                        <md-select v-model="brightnessDataQuantity" name="brightnessDataQuantity"
                          id="brightnessDataQuantity" @md-selected="GetSpecificQuantityBrightnessData">
                          <md-option value="5">5</md-option>
                          <md-option value="10">10</md-option>
                          <md-option value="15">15</md-option>
                        </md-select>
                      </md-field>
                    </div>
                  </div>
                  <bar-chart
                    :chartTitle='ChartTitle'
                    :chartSubTitle='brightnessChartSubTitle'
                    :chartData='brightnessChartData'
                    :chartColor='brightnessChartColor'
                    :chartHeight='brightnessChartHeight'
                    >
                  </bar-chart>
                </md-tab>

                <!-- 僅顯示土壤濕度 -->
                <md-tab id='tab-post1' md-label='土壤濕度' md-icon='eco'>
                  <div class='md-layout'>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                      <md-field>
                        <label for="soilMoistureDataQuantity">資料筆數</label>
                        <md-select v-model="soilMoistureDataQuantity" name="soilMoistureDataQuantity"
                          id="soilMoistureDataQuantity" @md-selected="GetSpecificQuantitySoilMoistureChartData">
                          <md-option value="5">5</md-option>
                          <md-option value="10">10</md-option>
                          <md-option value="15">15</md-option>
                        </md-select>
                      </md-field>
                    </div>
                  </div>
                  <bar-chart
                    :chartTitle='ChartTitle'
                    :chartSubTitle='soilMoistureChartSubTitle'
                    :chartData='soilMoistureChartData'
                    :chartColor='soilMoistureChartColor'
                    :chartHeight='soilMoistureChartHeight'
                  >
                  </bar-chart>
                </md-tab>

                <!-- 僅顯示水位深度 -->
                <md-tab id='tab-posts2' md-label='水位偵測' md-icon='grain'>
                  <div class='md-layout'>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                    </div>
                    <div class='md-layout-item'>
                      <md-field>
                        <label for="waterLevelDataQuantity">資料筆數</label>
                        <md-select v-model="waterLevelDataQuantity" name="waterLevelDataQuantity"
                          id="waterLevelDataQuantity" @md-selected="GetSpecificQuantityWaterLevelData">
                          <md-option value="5">5</md-option>
                          <md-option value="10">10</md-option>
                          <md-option value="15">15</md-option>
                        </md-select>
                      </md-field>
                    </div>
                  </div>
                  <bar-chart
                    :chartTitle='ChartTitle'
                    :chartSubTitle='waterLevelChartSubTitle'
                    :chartData='waterLevelChartData'
                    :chartColor='waterLevelChartColor'
                    :chartHeight='waterLevelChartHeight'
                  >
                  </bar-chart>
                </md-tab>
              </md-tabs>
            </template>
          </nav-tabs-card>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

import {
  NavTabsCard,
  BarChart
} from '@/components'

export default {
  components: {
    NavTabsCard,
    BarChart
  },
  data () {
    return {
      // 指定筆數的土壤濕度數值
      soilMoistureChartData: [],
      // 指定筆數的環境亮度數值
      brightnessChartData: [],
      // 指定筆數的水位深度數值
      waterLevelChartData: [],
      // 指定筆數的感測器數值
      averageChartData: [],
      timer: '',
      // 綜合圖表的顏色
      averageChartColor: ['#FFFF00', '#8B4513', '#1e90ff', '#32cd32'],
      // 環境亮度圖表的顏色
      brightnessChartColor: ['#FFFF00'],
      // 土壤濕度圖表的顏色
      soilMoistureChartColor: ['#8B4513'],
      // 水位深度圖表的顏色
      waterLevelChartColor: ['#1e90ff'],
      // 綜合圖表的高度
      averageChartHeight: 0,
      // 環境亮度的高度
      brightnessChartHeight: 0,
      // 土壤濕度的高度
      soilMoistureChartHeight: 0,
      // 水位深度的高度
      waterLevelChartHeight: 0,
      // 圖表的標題
      ChartTitle: '植物生長環境',
      // 綜合圖表的副標題
      averageChartSubTitle: '日照偵測/土壤水分偵測/水位偵測(數值愈高，水位愈低)/植物健康度',
      // 環境亮度圖表的副標題
      brightnessChartSubTitle: '日照偵測',
      // 土壤濕度圖表的副標題
      soilMoistureChartSubTitle: '土壤水分偵測',
      // 水位深度圖表的副標題
      waterLevelChartSubTitle: '水位偵測(數值愈高，水位愈低)',
      // 綜合圖表資料的筆數
      averageDataQuantity: 0,
      // 環境亮度圖表資料的筆數
      brightnessDataQuantity: 0,
      // 土壤濕度圖表資料的筆數
      soilMoistureDataQuantity: 0,
      // 水位深度圖表資料的筆數
      waterLevelDataQuantity: 0,
      // 儲存錯誤訊息
      errorMessage: '',
      loginAuthToken: '',
      loginAllow: '',
      loginUsername: ''
    }
  },
  mounted () {
    this.CheckLoginAllow()
  },
  // 監控資料筆數的改變，當使用者改變資料筆數時
  watch: {
    averageDataQuantity: function (dataQuantity) {
      window.localStorage.setItem('averageDataQuantity', this.averageDataQuantity)
      this.ChangeAverageChartHeight(dataQuantity)
    },
    brightnessDataQuantity: function (dataQuantity) {
      window.localStorage.setItem('brightnessDataQuantity', this.brightnessDataQuantity)
      this.ChangeBrightnessChartHeight(dataQuantity)
    },
    soilMoistureDataQuantity: function (dataQuantity) {
      window.localStorage.setItem('soilMoistureDataQuantity', this.soilMoistureDataQuantity)
      this.ChangeSoilMoistureChartHeight(dataQuantity)
    },
    waterLevelDataQuantity: function (dataQuantity) {
      window.localStorage.setItem('waterLevelDataQuantity', this.waterLevelDataQuantity)
      this.ChangeWaterLevelChartHeight(dataQuantity)
    },
    averageChartHeight: function () {
      window.localStorage.setItem('averageChartHeight', this.averageChartHeight)
    },
    brightnessChartHeight: function () {
      window.localStorage.setItem('brightnessChartHeight', this.brightnessChartHeight)
    },
    soilMoistureChartHeight: function () {
      window.localStorage.setItem('soilMoistureChartHeight', this.soilMoistureChartHeight)
    },
    waterLevelChartHeight: function () {
      window.localStorage.setItem('waterLevelChartHeight', this.waterLevelChartHeight)
    }
  },
  methods: {
    getAllData () {
      this.GetSpecificQuantityAverageData()
      this.GetSpecificQuantityBrightnessData()
      this.GetSpecificQuantitySoilMoistureChartData()
      this.GetSpecificQuantityWaterLevelData()
    },
    // 設置計時器每秒抓取資料
    initTimer () {
      this.timer = setInterval(() => {
        this.getAllData()
      }, 1000)
    },
    CheckLoginAllow () {
      const readLoginStatus = window.localStorage.getItem('loginAuthToken')
      if (readLoginStatus === '' || readLoginStatus === null) {
        this.loginAuthToken = ''
        this.loginAllow = false
        window.localStorage.setItem('loginAuthToken', this.loginAuthToken)
        if (this.loginAllow === false) {
          this.$router.push({ path: '/validate/login' })
        }
      } else if (readLoginStatus !== '') {
        this.loginAuthToken = readLoginStatus
        this.loginAllow = true
        // 初始化圖表的資料數量與其高度
        this.initChartParameters()
        // 載入頁面且動態變數已經初始化完時執行每秒抓取資料的函式
        this.initTimer()
        this.InitUsername()
      }
    },
    InitUsername () {
      const readLoginUsername = window.localStorage.getItem('loginUsername')
      if (readLoginUsername === '' || readLoginUsername === null) {
        axios
          .post('https://hoshi-plant.serveirc.com/login/user/name/get', {
            authToken: this.loginAuthToken
          })
          .then(response => {
            this.loginUsername = response.data.username
            window.localStorage.setItem('loginUsername', this.loginUsername)
          })
          .catch(error => {
            this.errorMessage = error
          })
      } else {
        this.loginUsername = readLoginUsername
      }
    },
    // 初始化圖表的資料筆數與其高度
    initChartParameters () {
      this.initAverageDataQuantity()
      this.initAverageChartHeight()
      this.initBrightnessDataQuantity()
      this.initBrightnessChartHeight()
      this.initSoilMoistureDataQuantity()
      this.initSoilMoistureChartHeight()
      this.initWaterLvelDataQuantity()
      this.initWaterLevelChartHeight()
    },
    // 初始化綜合圖表的資料筆數
    initAverageDataQuantity () {
      // 取得客戶端本地儲存物件綜合圖表的資料筆數
      const getAverageDataQuantity = window.localStorage.getItem('averageDataQuantity')
      // 若客戶端非首次載入頁面或未手動清除本地儲存物件
      if (getAverageDataQuantity > 0) {
        // 從客戶端本地儲存物件獲取資料筆數並賦予給averageDataQuantity的動態變數
        this.averageDataQuantity = getAverageDataQuantity
      // 客戶端首次載入此頁面時，則賦予綜合圖表的資料筆數為5
      } else {
        // 設資料筆數的初始值為5
        this.averageDataQuantity = 5
        // 初始化本地儲存物件，並將資料筆數儲存至客戶端的本地存儲
        window.localStorage.setItem('averageDataQuantity', this.averageDataQuantity)
      }
    },
    // 初始化環境亮度圖表的資料筆數
    initBrightnessDataQuantity () {
      // 取得客戶端本地儲存物件環境亮度圖表的資料筆數
      const getBrightnessDataQuantity = window.localStorage.getItem('brightnessDataQuantity')
      // 若客戶端非首次載入頁面或未手動清除本地儲存物件
      if (getBrightnessDataQuantity > 0) {
        // 從客戶端本地儲存物件獲取資料筆數並賦予給brightnessDataQuantity的動態變數
        this.brightnessDataQuantity = getBrightnessDataQuantity
      } else {
        // 設資料筆數的初始值為5
        this.brightnessDataQuantity = 5
        // 初始化本地儲存物件，並將資料筆數儲存至客戶端的本地存儲
        window.localStorage.setItem('brightnessDataQuantity', this.brightnessDataQuantity)
      }
    },
    // 初始化土壤濕度圖表的資料筆數
    initSoilMoistureDataQuantity () {
      // 取得客戶端本地儲存物件土壤濕度的資料筆數
      const getSoilMoistureDataQuantity = window.localStorage.getItem('soilMoistureDataQuantity')
      // 若客戶端非首次載入頁面或未手動清除本地儲存物件
      if (getSoilMoistureDataQuantity > 0) {
        // 從客戶端本地儲存物件獲取資料筆數並賦予給soilMoistureDataQuantity的動態變數
        this.soilMoistureDataQuantity = getSoilMoistureDataQuantity
      // 客戶端首次載入此頁面時，則賦予土壤濕度的資料筆數為5
      } else {
        // 設資料筆數的初始值為5
        this.soilMoistureDataQuantity = 5
        // 初始化本地儲存物件，並將資料筆數儲存至客戶端的本地存儲
        window.localStorage.setItem('soilMoistureDataQuantity', this.soilMoistureDataQuantity)
      }
    },
    // 初始化水位深度圖表的資料筆數
    initWaterLvelDataQuantity () {
      // 取得客戶端本地儲存物件水位深度的資料筆數
      const getWaterLevelDataQuantity = window.localStorage.getItem('waterLevelDataQuantity')
      if (getWaterLevelDataQuantity > 0) {
        // 從客戶端本地儲存物件獲取資料筆數並賦予給waterLevelDataQuantity的動態變數
        this.waterLevelDataQuantity = getWaterLevelDataQuantity
      } else {
        // 設資料筆數的初始值為5
        this.waterLevelDataQuantity = 5
        // 初始化本地儲存物件，並將資料筆數儲存至客戶端的本地存儲
        window.localStorage.setItem('waterLevelDataQuantity', this.waterLevelDataQuantity5)
      }
    },
    // 初始化綜合圖表的高度
    initAverageChartHeight () {
      const getAverageChartHeight = window.localStorage.getItem('averageChartHeight')
      if (getAverageChartHeight > 0) {
        this.averageChartHeight = getAverageChartHeight
      } else {
        this.averageChartHeight = 800
        window.localStorage.setItem('averageChartHeight', this.averageChartHeight)
      }
    },
    // 初始化環境亮度圖表的高度
    initBrightnessChartHeight () {
      const getBrightnessChartHeight = window.localStorage.getItem('brightnessChartHeight')
      if (getBrightnessChartHeight > 0) {
        this.brightnessChartHeight = getBrightnessChartHeight
      } else {
        this.brightnessChartHeight = 300
        window.localStorage.setItem('brightnessChartHeight', this.brightnessChartHeight)
      }
    },
    // 初始化土壤濕度圖表的高度
    initSoilMoistureChartHeight () {
      const getSoilMoistureChartHeight = window.localStorage.getItem('soilMoistureChartHeight')
      if (getSoilMoistureChartHeight > 0) {
        this.soilMoistureChartHeight = getSoilMoistureChartHeight
      } else {
        this.soilMoistureChartHeight = 600
        window.localStorage.setItem('soilMoistureChartHeight', this.soilMoistureChartHeight)
      }
    },
    // 初始化水位深度圖表的高度
    initWaterLevelChartHeight () {
      const getWaterLevelChartHeight = window.localStorage.getItem('waterLevelChartHeight')
      if (getWaterLevelChartHeight > 0) {
        this.waterLevelChartHeight = getWaterLevelChartHeight
      } else {
        this.waterLevelChartHeight = 600
        window.localStorage.setItem('waterLevelChartHeight', this.waterLevelChartHeight)
      }
    },
    // 當綜合圖表資料筆數更改時，讓其高度跟著更改
    ChangeAverageChartHeight (dataQuantity) {
      if (dataQuantity > 0) {
        if (dataQuantity >= 5 && dataQuantity < 10) {
          this.averageChartHeight = 800
        } else if (dataQuantity >= 10 && dataQuantity < 15) {
          this.averageChartHeight = 1400
        } else if (dataQuantity >= 15) {
          this.averageChartHeight = 2000
        }
      }
    },
    // 向後端請求綜合圖表的資料
    GetSpecificQuantityAverageData () {
      // 以POST的方式向後端請求該圖表的資料
      axios
        .post('https://hoshi-plant.serveirc.com/chart/data/average', {
          // 資料筆數
          data_limit: this.averageDataQuantity,
          // 資料排序方式
          data_sort: this.averageChartDataSort
        })
        .then(response => {
          // 若成功從後端獲取圖表的資料，則將其儲存至averageChartData的動態變數中
          this.averageChartData = response.data
        })
        .catch(error => {
          // 反之，則將錯誤訊息寫入errorMessage的動態變數中
          this.errorMessage = error
        })
    },
    // 當環境亮度圖表資料筆數更改時，讓其高度跟著更改
    ChangeBrightnessChartHeight (dataQuantity) {
      if (dataQuantity > 0) {
        if (dataQuantity >= 5 && dataQuantity < 10) {
          this.brightnessChartHeight = 300
        } else if (dataQuantity >= 10 && dataQuantity < 15) {
          this.brightnessChartHeight = 500
        } else if (dataQuantity >= 15) {
          this.brightnessChartHeight = 700
        }
      }
    },
    // 向後端請求環境亮度圖表的資料
    GetSpecificQuantityBrightnessData () {
      // 以POST的方式向後端請求該圖表的資料
      axios
        .post('https://hoshi-plant.serveirc.com/chart/data/brightness', {
          // 資料筆數
          data_limit: this.brightnessDataQuantity,
          // 資料排序方式
          data_sort: this.brightnesChartDataSort
        })
        .then(response => {
          // 若成功從後端獲取圖表的資料，則將其儲存至brightnessChartData的動態變數中
          this.brightnessChartData = response.data
        })
        .catch(error => {
          // 反之，則將錯誤訊息寫入errorMessage的動態變數中
          this.errorMessage = error
        })
    },
    // 當土壤濕度圖表資料筆數更改時，讓其高度跟著更改
    ChangeSoilMoistureChartHeight (dataQuantity) {
      if (dataQuantity > 0) {
        if (dataQuantity >= 5 && dataQuantity < 10) {
          this.soilMoistureChartHeight = 300
        } else if (dataQuantity >= 10 && dataQuantity < 15) {
          this.soilMoistureChartHeight = 500
        } else if (dataQuantity >= 15) {
          this.soilMoistureChartHeight = 700
        }
      }
    },
    // 向後端請求土壤濕度圖表的資料
    GetSpecificQuantitySoilMoistureChartData () {
      // 以POST的方式向後端請求該圖表的資料
      axios
        .post('https://hoshi-plant.serveirc.com/chart/data/soil_humidity', {
          // 資料筆數
          data_limit: this.soilMoistureDataQuantity,
          // 資料排序方式
          data_sort: this.soilMoistureChartDataSort
        })
        .then(response => {
          // 若成功從後端獲取圖表的資料，則將其儲存至soilMoistureChartData的動態變數中
          this.soilMoistureChartData = response.data
        })
        .catch(error => {
          // 反之，則將錯誤訊息寫入errorMessage的動態變數中
          this.errorMessage = error
        })
    },
    // 當水位深度圖表資料筆數更改時，讓其高度跟著更改
    ChangeWaterLevelChartHeight (dataQuantity) {
      if (dataQuantity > 0) {
        if (dataQuantity >= 5 && dataQuantity < 10) {
          this.waterLevelChartHeight = 300
        } else if (dataQuantity >= 10 && dataQuantity < 15) {
          this.waterLevelChartHeight = 500
        } else if (dataQuantity >= 15) {
          this.waterLevelChartHeight = 700
        }
      }
    },
    // 向後端請求水位深度圖表的資料
    GetSpecificQuantityWaterLevelData () {
      // 以POST的方式向後端請求該圖表的資料
      axios
        .post('https://hoshi-plant.serveirc.com/chart/data/water_level', {
          // 資料筆數
          data_limit: this.waterLevelDataQuantity,
          // 資料排序方式
          data_sort: this.waterLevelChartDataSort
        })
        .then(response => {
          // 若成功從後端獲取圖表的資料，則將其儲存至waterLevelChartData的動態變數中
          this.waterLevelChartData = response.data
        })
        .catch(error => {
          // 反之，則將錯誤訊息寫入errorMessage的動態變數中
          this.errorMessage = error
        })
    }
  },
  // 銷毀頁面前清除計時器，即是切換頁面或關閉頁面的時候會被執行
  beforeDestroy () {
    clearInterval(this.timer)
  }
}
</script>
<style lang="scss" scoped>
  .usernameStyle {
    font-size: 20px;
    text-align: right;
  };
  @import "node_modules/vue-material/dist/theme/engine";
</style>
