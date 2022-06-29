<template>
    <div class="md-layout">
        <div class="md-layout-item"></div>
        <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
            <form novalidate class="md-layout" @submit.prevent="submitForm">
                <user-card data-background-color="green" md-alignment="right">
                    <template slot="user-header">
                        <h4 class="title">使用者登入頁面</h4>
                        <p class="category">請先登入以訪問使用者頁面</p>
                    </template>
                    <template slot="user-content">
                        <md-field md-clearable :class="checkUsername">
                            <md-icon>perm_identity</md-icon>
                            <label>Username</label>
                            <md-input
                                v-model="login.username"
                                type="text"
                                maxlength="10"
                                placeholder="使用者名稱"
                                autofocus
                            ></md-input>
                            <span class="md-error">{{ fielderrorMessage.username }}</span>
                        </md-field>
                        <md-field md-clearable :class="checkPassword">
                            <md-icon>vpn_key</md-icon>
                            <label>Password</label>
                            <md-input
                                v-model="login.password"
                                type="password"
                                maxlength="15"
                                placeholder="使用者密碼"
                                autofocus
                            ></md-input>
                            <span class="md-error">{{ fielderrorMessage.password }}</span>
                        </md-field>
                        <!-- <div id="linkBody">
                            <div class="forgetPassword">
                                <a href="/validate/apply/reset/password" class="simple-text logo-mini">忘記密碼?</a>
                            </div>
                        </div> -->
                    </template>
                    <template slot="user-footer">
                        <!-- <md-button type="button" class="md-primary" @click="jumpRegisterPage">
                <span class="md-body-1">註冊</span>
              </md-button> -->
                        <button type="button" class="register-btn" @click="jumpRegisterPage">註冊</button>
                        <button type="submit" class="login-btn">登入</button>
                        <!-- <md-button type="submit" class="md-primary">
                <span class="md-body-1">登入</span>
              </md-button> -->
                    </template>
                </user-card>
                <md-snackbar :md-position="snackbarPosition" :md-active.sync="showErrorSnackbar">{{
                    loginMessage
                }}</md-snackbar>
            </form>
        </div>
        <div class="md-layout-item"></div>
    </div>
</template>

<script>
import axios from 'axios'

import { UserCard } from '@/components'

export default {
    components: {
        UserCard,
    },
    data() {
        return {
            login: {
                username: '',
                password: '',
            },
            invalid: {
                username: false,
                password: false,
            },
            fielderrorMessage: {
                username: '',
                password: '',
            },
            response: {
                username_validate: '',
                password_validate: '',
            },
            loginAuthToken: '',
            loginAllow: false,
            loginMessage: '',
            snackbarPosition: 'center',
            showErrorSnackbar: false,
        }
    },
    mounted() {},
    computed: {
        checkUsername() {
            return {
                'md-invalid': this.invalid.username,
            }
        },
        checkPassword() {
            return {
                'md-invalid': this.invalid.password,
            }
        },
    },
    watch: {
        'login.username': function () {
            this.checkUsernameField()
        },
        'login.password': function () {
            this.checkPasswordField()
        },
    },
    methods: {
        checkUsernameField() {
            var userNameFieldMatch = /^[a-zA-Z0-9]+$/
            if (this.login.username !== '' && userNameFieldMatch.test(this.login.username)) {
                this.invalid.username = false
                return true
            } else if (this.login.username !== '' && !userNameFieldMatch.test(this.login.username)) {
                this.fielderrorMessage.username = '請勿包含特殊字元!'
                this.invalid.username = true
                return false
            } else {
                this.fielderrorMessage.username = '此欄位不可為空!'
                this.invalid.username = true
                return false
            }
            // if (this.login.username !== '') {
            //   this.invalid.username = false
            //   return true
            // } else {
            //   this.fielderrorMessage.username = '此欄位不可為空!'
            //   this.invalid.username = true
            //   return false
            // }
        },
        checkPasswordField() {
            var passwordFieldMatch = /^[a-zA-Z0-9]+$/
            if (this.login.password !== '' && passwordFieldMatch.test(this.login.password)) {
                this.invalid.password = false
                return true
            } else if (this.login.password !== '' && !passwordFieldMatch.test(this.login.password)) {
                this.fielderrorMessage.password = '請勿包含特殊字元!!'
                this.invalid.password = true
                return false
            } else {
                this.fielderrorMessage.password = '此欄位不可為空!'
                this.invalid.password = true
                return false
            }
        },
        checkAllField() {
            if (this.checkUsernameField() === true && this.checkPasswordField() === true) {
                return true
            } else {
                return false
            }
        },
        handleResponse() {
            if (this.response.username_validate === true && this.response.password_validate === true) {
                if (this.loginAllow === true) {
                    this.clearForm(true)
                    // console.log(this.loginAuthToken)
                    this.InitLoginStatus()
                    this.$router.push({ path: '/user/dashboard' })
                } else {
                    this.loginMessage = '請先至註冊信箱啟用帳戶'
                    this.showErrorSnackbar = true
                }
            } else if (this.response.username_validate === false) {
                this.fielderrorMessage.username = '不存在的使用者名稱!'
                this.invalid.username = true
            } else if (this.response.username_validate === true && this.response.password_validate === false) {
                this.fielderrorMessage.password = '密碼錯誤!'
                this.invalid.password = true
            }
        },
        clearForm(mode) {
            this.login.username = ''
            this.login.password = ''
            if (mode === true) {
                this.invalid.username = false
                this.invalid.password = false
            }
        },
        submitForm() {
            if (this.checkAllField() === true) {
                axios
                    .post('https://hoshi-plant.serveirc.com/login/user/validate', {
                        username: this.login.username,
                        password: this.login.password,
                    })
                    .then((response) => {
                        // alert(response.data)
                        this.response.username_validate = response.data.username_validate
                        this.response.password_validate = response.data.password_validate
                        this.loginAllow = response.data.login_allow
                        this.loginAuthToken = response.data.login_token
                        this.handleResponse()
                    })
                    .catch((error) => {
                        this.errorMessage = error
                        // alert(error)
                    })
            }
        },
        jumpRegisterPage() {
            this.$router.push({ path: '/validate/register' })
        },
        InitLoginStatus() {
            const readLoginStatus = window.localStorage.getItem('loginAuthToken')
            if (readLoginStatus === '' || readLoginStatus === null) {
                window.localStorage.setItem('loginAuthToken', this.loginAuthToken)
            } else {
                this.loginAuthToken = readLoginStatus
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.md-layout {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-content: center;
    flex-wrap: wrap;
}

.forgetPassword {
    text-align: right;
}
.loginAccount {
    text-align: left;
    float: left;
}
.loginButton {
    text-align: right;
}
button.login-btn {
    font-size: 16px;
    color: #ffffff;
    background-color: #1e90ff;
    width: 90px;
    height: 45px;
}
button.register-btn {
    font-size: 16px;
    color: #ffffff;
    background-color: #ff0000;
    width: 90px;
    height: 45px;
}
//   @import "~vue-material/src/theme/engine";
//   @include md-register-theme("default", (
//   primary: md-get-palette-color(red, A200), // The primary color of your application
//   accent: md-get-palette-color(red, A200), // The accent or secondary color
//   ));
//   @import "~vue-material/src/components/MdButton/theme"; // Apply the Button
</style>
