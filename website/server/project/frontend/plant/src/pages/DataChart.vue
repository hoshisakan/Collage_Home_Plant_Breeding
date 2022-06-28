<template>
  <div class="content">
    <div class="usernameStyle">Welcome! {{ loginUsername }}</div>
    <div class="md-layout">
      <user-card data-background-color='green' md-alignment='right'>
        <template slot="user-header">
          <h4 class='title'>圖表分析</h4>
          <p class='category'>綜合分析資料</p>
        </template>
        <template slot='user-content'>
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
                          <md-option value="20">20</md-option>
                          <md-option value="25">25</md-option>
                          <md-option value="30">30</md-option>
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
        </template>
      </user-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

import {
// NavTabsCard,
  BarChart,
  UserCard
} from '@/components'

export default {
  components: {
    // NavTabsCard,
    BarChart,
    UserCard
  },
  data () {
    return {
      // 指定筆數的感測器數值
      averageChartData: [],
      timer: '',
      // 綜合圖表的顏色
      averageChartColor: ['#FFFF00', '#8B4513', '#1e90ff', '#32cd32'],
      // 綜合圖表的高度
      averageChartHeight: 0,
      // 圖表的標題
      ChartTitle: '植物生長狀態',
      // 綜合圖表的副標題
      averageChartSubTitle: '環境亮度/土壤濕度/水位高度/植物健康度',
      // 綜合圖表資料的筆數
      averageDataQuantity: 0,
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
    averageChartHeight: function () {
      window.localStorage.setItem('averageChartHeight', this.averageChartHeight)
    }
  },
  methods: {
    // 設置計時器每秒抓取資料
    initTimer () {
      this.timer = setInterval(() => {
        this.GetSpecificQuantityAverageData()
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
      this.GetSpecificQuantityAverageData()
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
    // 當綜合圖表資料筆數更改時，讓其高度跟著更改
    ChangeAverageChartHeight (dataQuantity) {
      if (dataQuantity > 0) {
        if (dataQuantity >= 5 && dataQuantity < 10) {
          this.averageChartHeight = 800
        } else if (dataQuantity >= 10 && dataQuantity < 15) {
          this.averageChartHeight = 1800
        } else if (dataQuantity >= 15 && dataQuantity < 19) {
          this.averageChartHeight = 2000
        } else if (dataQuantity >= 20 && dataQuantity < 25) {
          this.averageChartHeight = 2500
        } else if (dataQuantity >= 25 && dataQuantity < 31) {
          this.averageChartHeight = 4000
        }
      }
    },
    // 向後端請求綜合圖表的資料
    GetSpecificQuantityAverageData () {
      // 以POST的方式向後端請求該圖表的資料
      axios
        .post('https://hoshi-plant.serveirc.com/chart/data/average', {
          // 資料筆數
          data_limit: this.averageDataQuantity
          // 資料排序方式
        })
        .then(response => {
          // 若成功從後端獲取圖表的資料，則將其儲存至averageChartData的動態變數中
          this.averageChartData = response.data
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
