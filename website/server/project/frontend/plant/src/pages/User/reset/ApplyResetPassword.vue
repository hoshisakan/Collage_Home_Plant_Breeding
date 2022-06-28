<template>
  <div class="md-layout md-alignment-center-center">
    <div class="md-layout-item"></div>
    <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
      <form novalidate class="md-layout" @submit.prevent="submitForm">
        <user-card data-background-color='green' md-alignment='right'>
            <template slot='user-header'>
              <h4 class='title'>使用者帳戶密碼重設申請</h4>
              <p class='category'>請輸入使用者名稱與註冊信箱</p>
            </template>
            <template slot='user-content'>
                <md-field md-clearable :class="checkUsername">
                  <md-icon>perm_identity</md-icon>
                  <label>Username</label>
                  <md-input v-model="reset.username" type="text" maxlength="10" placeholder="使用者名稱" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.username }}</span>
                </md-field>
                <md-field md-clearable :class="checkEmail">
                  <md-icon>mail</md-icon>
                  <label>Email</label>
                  <md-input v-model="reset.email" type="email" maxlength="30" placeholder="使用者電郵" autocomplete="email" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.email }}</span>
                </md-field>
            </template>
            <template slot='user-footer'>
              <md-button type="submit" class="md-primary">
                <span class="md-body-1">送出</span>
              </md-button>
            </template>
          </user-card>
          <md-snackbar :md-position="snackbarPosition" :md-active.sync="showSnackbar">{{ resetMessage }}</md-snackbar>
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
        username: '',
        email: ''
      },
      invalid: {
        username: false,
        email: false
      },
      response: {
        username: false,
        email: false
      },
      fielderrorMessage: {
        username: '',
        email: ''
      },
      whetherPass: false,
      whetherSendSuccess: false,
      resetToken: '',
      errorMessage: '',
      snackbarPosition: 'center',
      showSnackbar: false,
      resetMessage: ''
    }
  },
  computed: {
    checkUsername () {
      return {
        'md-invalid': this.invalid.username
      }
    },
    checkEmail () {
      return {
        'md-invalid': this.invalid.email
      }
    }
  },
  watch: {
    'reset.username': function () {
      this.checkUsernameField()
    },
    'reset.email': function () {
      this.checkEmailField()
    }
  },
  methods: {
    clearForm () {
      this.response.username = false
      this.response.email = false
      this.whetherPass = false
      this.whetherSendSuccess = false
      // this.resetToken = ''
      this.invalid.username = false
      this.invalid.email = false
      this.reset.username = ''
      this.reset.email = ''
    },
    checkUsernameField () {
      var userNameFieldMatch = /^[a-zA-Z0-9]+$/
      if (this.reset.username !== '' && userNameFieldMatch.test(this.reset.username)) {
        this.invalid.username = false
        return true
      } else if (this.reset.username !== '' && !userNameFieldMatch.test(this.reset.username)) {
        this.fielderrorMessage.username = '請勿包含特殊字元!'
        this.invalid.username = true
      } else {
        this.invalid.username = true
        this.fielderrorMessage.username = '此欄位不可為空!'
        return false
      }
    },
    checkEmailField () {
      /* eslint-disable */
      var emailFieldMatch = /^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z]+$/
      if (this.reset.email !== '' && emailFieldMatch.test(this.reset.email)) {
        this.invalid.email = false
        return true
      } else if (this.reset.email !== '' && !emailFieldMatch.test(this.reset.email)) {
        this.invalid.email = true
        this.fielderrorMessage.email = 'email格式錯誤!!'
      } else {
        this.invalid.email = true
        this.fielderrorMessage.email = '此欄位不可為空!'
        return false
      }
    },
    checkAllField () {
      if (this.checkUsernameField() && this.checkEmailField() === true) {
        return true
      } else {
        return false
      }
    },
    handleUserFieldAbnormal () {
      if (this.response.username === false) {
        this.fielderrorMessage.username = '使用者名稱與輸入的電郵不符合!'
        this.invalid.username = true
      } else {
        this.invalid.username = false
      }
    },
    handleEmailFieldAbnormal () {
      if (this.response.email === false) {
        this.fielderrorMessage.email = '註冊信箱與輸入的使用者名稱不符合!'
        this.invalid.email = true
      } else {
        this.invalid.email = false
      }
    },
    handleResponse () {
      if (this.response.username === false || this.response.email === false) {
        this.handleUserFieldAbnormal()
        this.handleEmailFieldAbnormal()
      }
      if (this.whetherPass === true) {
        this.reissureMessage = '輸入正確'
        this.showSnackbar = true
        this.clearForm()
        this.$router.push({ path: '/validate/reset/password', query: { id:this.resetToken} })
      }
    },
    submitForm () {
      if (this.checkAllField() === true) {
        axios
          .post('https://plant.serveirc.com/reset/password/apply',{
            applyUserName: this.reset.username,
            applyUserEmail: this.reset.email
          })
          .then(response => {
            this.response.username = response.data.username_validate
            this.response.email = response.data.email_validate
            this.whetherPass = response.data.whether_pass
            if (this.whetherPass === true) {
              this.resetToken = response.data.token
            }
            console.log(this.response.username)
            console.log(this.response.email)
            console.log(this.whetherPass)
            console.log(this.resetToken)
            this.handleResponse()
          })
          .catch(error => {
            this.errorMessage = error
          })
      }
    }
  }
}
</script>
