<template>
  <div class='content'>
    <div class="usernameStyle">Welcome! {{ loginUsername }}</div>
    <div class='md-layout'>
      <div class='md-layout-item'></div>
      <div class='md-layout-item'>
          <md-card>
            <md-card-header data-background-color='green'>
              <h4 class='title'>繼電器控制</h4>
              <p class='category'>自動/手動</p>
            </md-card-header>
            <md-card-content>
              <div>
                <md-switch v-model="autoControlSwtich" @change='SendAutoControl' class="md-primary">自動控制({{ autoControlSwtichStatus }})</md-switch>
              </div>
              <div>
                <md-switch v-model="manuallyControlLight" @change='SendManuallyControlLight' class="md-primary">手動控制燈光({{ manuallyControlLightStatus }})</md-switch>
                <md-switch v-model="manuallyControlMotor" @change='SendManuallyControlMotor' class="md-primary">手動控制馬達({{ manuallyControlMotorStatus }})</md-switch>
              </div>
              <div>
                <md-button class="md-fab md-primary" @click='SendManuallyTakePicture'>
                  <md-icon>camera</md-icon>
                </md-button>
              </div>
              <div>
                <br/>
                更新時間：{{ this.mode_update_time }}
              </div>
            </md-card-content>
          </md-card>
        </div>
        <div class='md-layout-item'></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  components: {
  },
  data () {
    return {
      autoControlSwtich: false,
      autoControlSwtichStatus: '',
      manuallyControlLight: false,
      manuallyControlLightStatus: '',
      manuallyControlMotor: false,
      manuallyControlMotorStatus: '',
      manuallyTakePicture: false,
      mode_update_time: '',
      temp_update_time: '',
      timer: '',
      errorMessage: '',
      loginAuthToken: '',
      loginAllow: '',
      loginUsername: '',
      successMessage: ''
    }
  },
  watch: {
    autoControlSwtich: function () {
      this.UpdateAutoControlStatus()
    },
    manuallyControlLight: function () {
      this.UpdateManuallyOpenLightStatus()
    },
    manuallyControlMotor: function () {
      this.UpdateManuallyOpenMotorStatus()
    }
  },
  mounted () {
    this.CheckLoginAllow()
  },
  methods: {
    InitTimer () {
      this.timer = setInterval(() => {
        this.UpdateCurrentStatus()
      }, 5000)
    },
    InitRelayStatus () {
      this.UpdateAutoControlStatus()
      this.UpdateManuallyOpenLightStatus()
      this.UpdateManuallyOpenMotorStatus()
    },
    InitUsername () {
      const readLoginUsername = window.localStorage.getItem('loginUsername')
      if (readLoginUsername === '' || readLoginUsername === null) {
        axios
          .post('https://plant.serveirc.com/login/user/name/get', {
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
        this.InitUsername()
        this.ReadCurrentStatus()
        this.InitRelayStatus()
      }
    },
    UpdateAutoControlStatus () {
      if (this.autoControlSwtich === true) {
        this.autoControlSwtichStatus = '開'
        this.manuallyControlLight = false
        this.manuallyControlMotor = false
        this.manuallyControlLightStatus = '關'
        this.manuallyControlMotorStatus = '關'
      } else {
        this.autoControlSwtichStatus = '關'
      }
    },
    UpdateManuallyOpenLightStatus () {
      if (this.manuallyControlLight === true && this.autoControlSwtich === true) {
        this.manuallyControlLightStatus = '開'
        this.autoControlSwtich = false
        this.autoControlSwtichStatus = '關'
      } else if (this.manuallyControlLight === true && this.autoControlSwtich === false) {
        this.manuallyControlLightStatus = '開'
        // this.autoControlSwtich = false
        this.autoControlSwtichStatus = '關'
      } else if (this.manuallyControlLight === false && this.autoControlSwtich === true) {
        this.autoControlSwtichStatus = '開'
      } else if (this.manuallyControlLight === false && this.autoControlSwtich === false) {
        this.manuallyControlLightStatus = '關'
        this.autoControlSwtich = true
        this.autoControlSwtichStatus = '開'
      }
    },
    UpdateManuallyOpenMotorStatus () {
      if (this.manuallyControlMotor === true && this.autoControlSwtich === true) {
        this.manuallyControlMotorStatus = '開'
        this.autoControlSwtich = false
        this.autoControlSwtichStatus = '關'
      } else if (this.manuallyControlMotor === true && this.autoControlSwtich === false) {
        this.autoControlSwtichStatus = '關'
      } else if (this.manuallyControlMotor === false && this.autoControlSwtich === true) {
        this.autoControlSwtichStatus = '開'
      } else if (this.manuallyControlMotor === false && this.autoControlSwtich === false) {
        this.manuallyControlMotorStatus = '關'
        this.autoControlSwtich = true
        this.autoControlSwtichStatus = '開'
      }
    },
    ReadCurrentStatus () {
      axios
        .get('https://plant.serveirc.com/relay/read/control/mode')
        .then(response => {
          this.autoControlSwtich = response.data.auto_control_status
          this.manuallyControlLight = response.data.manually_light_control
          this.manuallyControlMotor = response.data.manually_motor_control
          this.mode_update_time = response.data.switch_mode_date
        })
        .catch(error => {
          this.errorMessage = error
        })
    },
    UpdateCurrentStatus () {
      axios
        .get('https://plant.serveirc.com/relay/read/control/mode')
        .then(response => {
          this.temp_update_time = response.data.switch_mode_date
          if (this.temp_update_time !== this.mode_update_time) {
            this.autoControlSwtich = response.data.auto_control_status
            this.manuallyControlLight = response.data.manually_light_control
            this.manuallyControlMotor = response.data.manually_motor_control
            this.mode_update_time = response.data.switch_mode_date
          }
        })
        .catch(error => {
          this.errorMessage = error
        })
    },
    SendAutoControl () {
      axios
        .post('https://plant.serveirc.com/relay/auto/control/switch', {
          mode: this.autoControlSwtich
        })
        .then(response => {
            this.successMessage = response.data.auto_control_switch
        })
        .catch(error => {
            this.errorMessage = error
        })
    },
    SendManuallyControlLight () {
      axios
        .post('https://plant.serveirc.com/relay/manually/open/light', {
          mode: this.manuallyControlLight
        })
        .then(response => {
            this.successMessage = response.data.light_status
        })
        .catch(error => {
          this.errorMessage = error
        })
    },
    SendManuallyControlMotor () {
      axios
        .post('https://plant.serveirc.com/relay/manually/open/watering', {
          mode: this.manuallyControlMotor
        })
        .then(response => {
            this.successMessage = response.data.watering_status
        })
        .catch(error => {
          this.errorMessage = error
        })
    },
    SendManuallyTakePicture () {
      axios
        .get('https://plant.serveirc.com/manually/take/picture')
        .then(response => {
          this.manuallyTakePicture = response.data.manually_take_picture
          if (this.manuallyTakePicture !== null && this.manuallyTakePicture === true) {
            this.$router.push({
              path: '/user/dashboard'
            })
          } else {
            alert('發生未知的錯誤!')
          }
        })
        .catch(error => {
          this.errorMessage = error
        })
    }
  }
}
</script>
<style lang="scss" scoped>
  .usernameStyle {
      font-size: 20px;
      text-align: right;
    };
  .md-card {
      width: 360px;
      height: 340px;
      // margin: 4px;
      display: inline-block;
      vertical-align: center;
    }
  .submit_btn {
      vertical-align: center;
      align-items: center;
  }
</style>
