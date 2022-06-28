<template>
  <div class='content'>
    <div class="usernameStyle">Welcome! {{ loginUsername }}</div>
    <div class='md-layout md-gutter'>
      <div class='md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100'>
        <md-card>
          <md-card-header data-background-color='green'>
            <h4 class='title'>檢視異常數據</h4>
            <p class='category'>感測器</p>
          </md-card-header>
          <md-card-content>
            <div class='md-layout'>
              <div class='md-layout-item'>
              </div>
              <div class='md-layout-item'>
              </div>
              <div class='md-layout-item'>
                <md-field>
                  <label for="requestDataQuantity">資料筆數</label>
                  <!-- 選擇資料的筆數 -->
                  <md-select v-model="requestDataQuantity" name="requestDataQuantity"
                    id="requestDataQuantity">
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
           <!-- 掛載指定數量的異常數值，以表單的形式顯示 -->
           <abnormal-data-table :abnormalDataQuantity="requestDataQuantity">
           </abnormal-data-table>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { AbnormalDataTable } from '@/components'

export default {
  components: {
    AbnormalDataTable
  },
  data () {
    return {
      requestDataQuantity: 0,
      loginAuthToken: '',
      loginAllow: '',
      loginUsername: ''
    }
  },
  watch: {
    // 監控數值變化，若客戶端更改資料數量，則將其數量更新到本地儲存
    requestDataQuantity: function () {
      window.localStorage.setItem('requestDataQuantity', this.requestDataQuantity)
    }
  },
  mounted () {
    this.CheckLoginAllow()
  },
  methods: {
    initTableListParameters () {
      const getTableListDataQuantity = window.localStorage.getItem('requestDataQuantity')
      // 若客戶端本地已經儲存資料數量
      if (getTableListDataQuantity > 0) {
        // 將其值賦予給requestDataQuantity的動態變數
        this.requestDataQuantity = getTableListDataQuantity
      } else {
        // 反之，設置requestDataQuantity的動態變數為10
        this.requestDataQuantity = 10
        // 並將requestDataQuantity的值存入客戶端的本地中
        window.localStorage.setItem('requestDataQuantity', this.requestDataQuantity)
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
        // 初始化資料的數量
        this.initTableListParameters()
        this.InitUsername()
      }
    }
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
