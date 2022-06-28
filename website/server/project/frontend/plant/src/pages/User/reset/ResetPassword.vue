<template>
  <div class="md-layout md-alignment-center-center">
    <div class="md-layout-item"></div>
    <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
      <form novalidate class="md-layout" @submit.prevent="submitForm">
        <user-card data-background-color='green' md-alignment='right'>
            <template slot='user-header'>
              <h4 class='title'>使用者密碼重置頁面</h4>
              <p class='category'>請輸入長度15以內的新密碼</p>
            </template>
            <template slot='user-content'>
               <md-field>
                  <md-icon>perm_identity</md-icon>
                  <label>Username</label>
                  <md-input v-model="reset.username" type="text" placeholder="使用者名稱" disabled></md-input>
                  <span class="md-error">{{ fielderrorMessage.username }}</span>
                </md-field>
                <md-field md-clearable :class="checkNewPassword">
                  <md-icon>vpn_key</md-icon>
                  <label>Please enter new password</label>
                  <md-input v-model="reset.newPassword" type="password" maxlength="15" placeholder="請輸入新密碼" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.newPassword }}</span>
                </md-field>
                <md-field md-clearable :class="checkNewPasswordAgain">
                  <md-icon>vpn_key</md-icon>
                  <label>Please enter new password again</label>
                  <md-input v-model="reset.newPasswordSec" type="password" maxlength="15" placeholder="請再輸入一次新密碼" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.newPasswordSec }}</span>
                </md-field>
            </template>
            <template slot='user-footer'>
              <md-button type="submit" class="md-primary">
                <span class="md-body-1">送出</span>
              </md-button>
            </template>
          </user-card>
          <md-snackbar :md-position="snackbarPosition" :md-active.sync="showErrorSnackbar">{{ resetMessage }}</md-snackbar>
      </form>
    </div>
    <div class="md-layout-item"></div>
  </div>
</template>

<script>
import axios from 'axios'

import {
  UserCard
} from '@/components'

export default {
  components: {
    UserCard
  },
  data () {
    return {
      reset: {
        newPassword: '',
        newPasswordSec: '',
        username: '',
        token: ''
      },
      invalid: {
        newPassword: false,
        newPasswordSec: false
      },
      response: {
        passwordValidate: false
      },
      fielderrorMessage: {
        newPassword: '',
        newPasswordSec: ''
      },
      errorMessage: '',
      snackbarPosition: 'center',
      showErrorSnackbar: false,
      resetMessage: '',
      whetherPass: false,
      resetResult: false,
      allowReset: false
    }
  },
  created () {
    this.getUsername()
  },
  mounted () {
  },
  computed: {
    checkNewPassword () {
      return {
        'md-invalid': this.invalid.newPassword
      }
    },
    checkNewPasswordAgain () {
      return {
        'md-invalid': this.invalid.newPasswordSec
      }
    }
  },
  watch: {
    'reset.newPassword': function () {
      this.checkNewPasswordField()
    },
    'reset.newPasswordSec': function () {
      this.checkNewPasswordAgainField()
    }
  },
  methods: {
    getUsername () {
      this.reset.token = this.$route.query.id
      if (this.reset.token !== '') {
        axios
          .post('https://plant.serveirc.com/reset/password/username/get', {
            resetToken: this.reset.token
          })
          .then(response => {
            this.reset.username = response.data.username
            this.allowReset = response.data.allowReset
            if (this.allowReset === false) {
              this.reset.username = ''
              alert('錯誤')
              this.$router.push({ path: '/validate/apply/reset/password' })
            }
          })
          .catch(error => {
            this.errorMessage = error
          })
      }
    },
    checkNewPasswordField () {
      var passwordFieldMatch = /^[a-zA-Z0-9]+$/
      if (this.reset.newPassword !== '' && passwordFieldMatch.test(this.reset.newPassword)) {
        this.invalid.newPassword = false
        return true
      } else if (this.reset.newPassword !== '' && !passwordFieldMatch.test(this.reset.newPassword)) {
        this.invalid.newPassword = true
        this.fielderrorMessage.newPassword = '請勿包含特殊字元!!'
        return false
      } else {
        this.invalid.newPassword = true
        this.fielderrorMessage.newPassword = '此欄位不可為空!'
        return false
      }
    },
    checkNewPasswordAgainField () {
      var passwordFieldMatch = /^[a-zA-Z0-9]+$/
      // if (this.reset.newPasswordSec !== '' && passwordFieldMatch.test(this.reset.newPasswordSec)) {
      //   this.invalid.newPassword = false
      //   return true
      // } else if (this.reset.newPasswordSec !== '' && !passwordFieldMatch.test(this.reset.newPasswordSec)) {
      //   this.invalid.newPasswordSec = true
      //   this.fielderrorMessage.newPasswordSec = '請勿包含特殊字元!!'
      //   return false
      // } else {
      //   this.invalid.newPasswordSec = true
      //   this.fielderrorMessage.newPasswordSec = '此欄位不可為空!'
      //   return false
      // }
      if (this.reset.newPasswordSec !== '') {
        if (this.reset.newPasswordSec === this.reset.newPassword && passwordFieldMatch.test(this.reset.newPasswordSec)) {
          this.invalid.newPasswordSec = false
          return true
        } else if (!passwordFieldMatch.test(this.reset.newPassword)) {
          this.invalid.newPasswordSec = true
          this.fielderrorMessage.newPasswordSec = '請勿包含特殊字元!!'
          return false
        } else if (this.reset.newPasswordSec !== this.reset.newPassword) {
          this.invalid.newPasswordSec = true
          this.fielderrorMessage.newPasswordSec = '密碼必須一致!'
          return false
        }
      } else {
        this.invalid.password = true
        this.fielderrorMessage.password = '此欄位不可為空!'
        return false
      }
    },
    checkAllField () {
      if (this.checkNewPasswordField() === true && this.checkNewPasswordAgainField() === true) {
        return true
      } else {
        return false
      }
    },
    handleResponse () {
      if (this.whetherPass === false && this.response.passwordValidate === false) {
        this.fielderrorMessage.newPassword = '密碼不可與之前設置的相同!'
        this.fielderrorMessage.newPasswordSec = '密碼不可與之前設置的相同!'
        this.invalid.newPassword = true
        this.invalid.newPasswordSec = true
      } else if (this.whetherPass === true && this.resetResult === true) {
        this.$router.push({ path: '/validate/reset/password/success' })
      } else if (this.whetherPass === true && this.resetResult === false) {
        this.$router.push({ path: '/validate/reset/password/failure' })
      }
    },
    clearForm () {
      this.invalid.reset.newPassword = false
      this.invalid.reset.newPasswordSec = false
      this.response.passwordValidate = false
      this.errorMessage = ''
      this.whetherPass = false
      this.resetResult = false
      this.reset.username = ''
      this.reset.newPassword = ''
      this.reset.newPasswordSec = ''
    },
    submitForm () {
      if (this.checkAllField() === true) {
        axios
          .post('https://plant.serveirc.com/reset/password/validate', {
            resetUserName: this.reset.username,
            newPassword: this.reset.newPassword
          })
          .then(response => {
            this.whetherPass = response.data.whether_pass
            this.response.passwordValidate = response.data.password_validate
            if (this.whetherPass === true) {
              this.resetResult = response.data.resetResult
            }
            this.handleResponse()
            console.log(response.data)
          })
          .catch(error => {
            this.errorMessage = error
            console.log(this.errorMessage)
          })
      }
    }
  }
}
</script>
