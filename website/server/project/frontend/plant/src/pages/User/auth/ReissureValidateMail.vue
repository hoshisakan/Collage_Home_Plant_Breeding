<template>
  <div class="md-layout md-alignment-center-center">
    <div class="md-layout-item"></div>
    <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
      <form novalidate class="md-layout" @submit.prevent="submitForm">
        <user-card data-background-color='green' md-alignment='right'>
            <template slot='user-header'>
              <h4 class='title'>註冊驗證信補發申請</h4>
              <p class='category'>請輸入使用者名稱與註冊信箱</p>
            </template>
            <template slot='user-content'>
                <md-field md-clearable :class="checkUsername">
                  <md-icon>perm_identity</md-icon>
                  <label>Username</label>
                  <md-input v-model="reissure.username" type="text" maxlength="10" placeholder="使用者名稱" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.username }}</span>
                </md-field>
                <md-field md-clearable :class="checkEmail">
                  <md-icon>mail</md-icon>
                  <label>Email</label>
                  <md-input v-model="reissure.email" type="email" maxlength="30" placeholder="使用者電郵" autocomplete="email" autofocus></md-input>
                  <span class="md-error">{{ fielderrorMessage.email }}</span>
                </md-field>
            </template>
            <template slot='user-footer'>
              <md-button type="submit" class="md-primary">
                <span class="md-body-1">提交申請</span>
              </md-button>
            </template>
          </user-card>
          <md-snackbar :md-position="snackbarPosition" :md-active.sync="showSnackbar">{{ reissureMessage }}</md-snackbar>
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
      reissure: {
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
      errorMessage: '',
      showSnackbar: false,
      snackbarPosition: 'center',
      reissureMessage: ''
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
    'reissure.username': function () {
      this.checkUsernameField()
    },
    'reissure.email': function () {
      this.checkEmailField()
    }
  },
  methods: {
    clearForm (mode) {
      this.response.username = false
      this.response.email = false
      this.whetherPass = false
      this.whetherSendSuccess = false
      this.invalid.username = false
      this.invalid.email = false
      this.reissure.username = ''
      this.reissure.email = ''
    },
    checkUsernameField () {
      var userNameFieldMatch = /^[a-zA-Z0-9]+$/
      if (this.reissure.username !== '' && userNameFieldMatch.test(this.reissure.username)) {
        this.invalid.username = false
        return true
      } else if (this.reissure.username !== '' && !userNameFieldMatch.test(this.reissure.username)) {
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
      if (this.reissure.email !== '' && emailFieldMatch.test(this.reissure.email)) {
        this.invalid.email = false
        return true
      } else if (this.reissure.email !== '' && !emailFieldMatch.test(this.reissure.email)) {
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
      if (this.whetherPass === true && this.whetherSendSuccess === true) {
        this.reissureMessage = '補發驗證信已經寄出，請至郵箱確認'
        this.showSnackbar = true
        this.clearForm()
      }
    },
    submitForm () {
      if (this.checkAllField() === true) {
        axios
          .post('https://hoshi-plant.serveirc.com/register/mail/send/again',{
            username: this.reissure.username,
            email: this.reissure.email
          })
          .then(response => {
            this.response.username = response.data.username_validate
            this.response.email = response.data.email_validate
            this.whetherPass = response.data.whether_pass
            if (this.whetherPass === true) {
              this.whetherSendSuccess = response.data.sendSuccess
            }
            // console.log(this.response.username)
            // console.log(this.response.email)
            // console.log(this.whetherPass)
            // console.log(this.whetherSendSuccess)
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
