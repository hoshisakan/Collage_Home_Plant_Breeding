<template>
  <div>
    <md-table v-model='abnormalData'>
      <md-table-row slot='md-table-row' slot-scope='{ item }' md-selecttable='single'>
        <md-table-cell md-label='Detection Date'>{{ item.d_created_date }}</md-table-cell>
        <md-table-cell md-label='Environment Brightness'>{{ item.d_light }}</md-table-cell>
        <md-table-cell md-label='Soil Moisture'>{{ item.d_soil }}</md-table-cell>
        <md-table-cell md-label='Water Level'>{{ item.d_water_level }}</md-table-cell>
        <md-table-cell md-label='Environment Temperature'>{{ item.d_dht11_t }}</md-table-cell>
        <md-table-cell md-label='Environment Humidity'>{{ item.d_dht11_h }}</md-table-cell>
      </md-table-row>
    </md-table>
  </div>
</template>

<script>
// 引入axios
import axios from 'axios'

export default {
  name: 'abnormal-data-table',
  props: {
    // 接收父組件傳遞過來的值，若無傳遞預設值為5
    abnormalDataQuantity: {
      required: true,
      default: 5
    }
  },
  data () {
    return {
      // 儲存異常的感測器資料
      abnormalData: [],
      // 計時器
      timer: '',
      // 儲存錯誤訊息
      errorMessage: ''
    }
  },
  mounted () {
    this.getAbnormalData()
    // 載入頁面且動態變數已經初始化完時執行每秒抓取資料的函式
    this.initTimer()
  },
  methods: {
    initTimer () {
      // 設置計時器每秒抓取資料
      this.timer = setInterval(() => {
        // 抓取感測器的異常數據
        this.getAbnormalData()
      }, 1000)
    },
    getAbnormalData () {
      // 以POST的方式向後端請求異常的數據
      axios
        .post('https://hoshi-plant.serveirc.com/abnormal/data/table', {
          data_limit: this.abnormalDataQuantity
        })
        .then(response => {
          // 儲存獲取的異常數據
          this.abnormalData = response.data
        })
        .catch(error => {
          // 儲存錯誤訊息
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
