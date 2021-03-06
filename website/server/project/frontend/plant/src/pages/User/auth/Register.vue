<template>
    <div class="md-layout">
        <div class="md-layout-item"></div>
        <div class="md-layout-item md-medium-size-50 md-small-size-50 md-xsmall-size-100">
            <form novalidate class="md-layout" @submit.prevent="submitForm">
                <user-card data-background-color="green" md-alignment="right">
                    <template slot="user-header">
                        <h4 class="title">使用者註冊頁面</h4>
                        <p class="category">請先註冊以訪問使用者頁面</p>
                    </template>
                    <template slot="user-content">
                        <md-field md-clearable :class="checkUsername">
                            <md-icon>perm_identity</md-icon>
                            <label>Username</label>
                            <md-input
                                v-model="register.username"
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
                                v-model="register.password"
                                type="password"
                                maxlength="15"
                                placeholder="使用者密碼"
                                autofocus
                            ></md-input>
                            <span class="md-error">{{ fielderrorMessage.password }}</span>
                        </md-field>
                        <md-field md-clearable :class="checkEmail">
                            <md-icon>mail</md-icon>
                            <label>Email</label>
                            <md-input
                                v-model="register.email"
                                type="email"
                                maxlength="30"
                                placeholder="使用者電郵"
                                autocomplete="email"
                                autofocus
                            ></md-input>
                            <span class="md-error">{{ fielderrorMessage.email }}</span>
                        </md-field>
                    </template>
                    <template slot="user-footer">
                        <md-button type="submit" class="md-primary">
                            <span class="md-body-1">創建帳戶</span>
                        </md-button>
                    </template>
                </user-card>
                <md-snackbar :md-position="snackbarPosition" :md-active.sync="showSnackbar">{{
                    snackbarMessage
                }}</md-snackbar>
                <md-snackbar :md-position="snackbarPosition" :md-active.sync="showErrorSnackbar">{{
                    registerMessage
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
            register: {
                username: '',
                email: '',
                password: ''
            },
            invalid: {
                username: false,
                email: false,
                password: false,
            },
            response: {
                username: false,
                email: false,
                password: false,
                items: ''
            },
            checkUsername: false,
            checkEmail: false,
            snackbarPosition: 'center',
            showSnackbar: false,
            snackbarMessage: '',
            fielderrorMessage: {
                username: '',
                email: '',
                password: '',
            },
            showErrorSnackbar: false,
            registerMessage: '',
            registerResult: '',
            registerStatus: '',
            errorMessage: '',
            sendAllow: false,
        }
    },
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
        checkEmail() {
            return {
                'md-invalid': this.invalid.email,
            }
        },
    },
    watch: {
        'register.username': function () {
            this.checkUsernameField()
        },
        'register.password': function () {
            this.checkPasswordField()
        },
        'register.email': function () {
            this.checkEmailField()
        },
    },
    methods: {
        checkUsernameField() {
            var userNameFieldMatch = /^[a-zA-Z0-9]+$/
            if (this.register.username !== '' && userNameFieldMatch.test(this.register.username)) {
                this.invalid.username = false
                return true
            } else if (this.register.username !== '' && !userNameFieldMatch.test(this.register.username)) {
                this.fielderrorMessage.username = '請勿包含特殊字元!'
                this.invalid.username = true
            } else {
                this.fielderrorMessage.username = '此欄位不可為空!'
                this.invalid.username = true
                return false
            }
        },
        checkPasswordField() {
            var passwordFieldMatch = /^[a-zA-Z0-9]+$/
            if (this.register.password !== '' && passwordFieldMatch.test(this.register.password)) {
                this.invalid.password = false
                return true
            } else if (this.register.password !== '' && !passwordFieldMatch.test(this.register.password)) {
                this.fielderrorMessage.password = '請勿包含特殊字元!!'
                this.invalid.password = true
            } else {
                this.fielderrorMessage.password = '此欄位不可為空!'
                this.invalid.password = true
                return false
            }
        },
        checkEmailField() {
            /* eslint-disable */
            var emailFieldMatch = /^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z]+$/
            if (this.register.email !== '' && emailFieldMatch.test(this.register.email)) {
                this.invalid.email = false
                return true
            } else if (this.register.email !== '' && !emailFieldMatch.test(this.register.email)) {
                this.invalid.email = true
                this.fielderrorMessage.email = 'email格式錯誤!!'
            } else {
                this.invalid.email = true
                this.fielderrorMessage.email = '此欄位不可為空!'
                return false
            }
        },
        checkAllField() {
            if (
                this.checkUsernameField() === true &&
                this.checkPasswordField() === true &&
                this.checkEmailField() === true
            ) {
                return true
            } else {
                return false
            }
        },
        clearForm(mode) {
            this.register.username = ''
            this.register.password = ''
            this.register.email = ''
            if (mode === true) {
                this.invalid.username = false
                this.invalid.password = false
                this.invalid.email = false
                this.response.username = false
                this.response.password = false
                this.response.email = false
            }
        },
        handleUserFieldAbnormal() {
            if (this.response.username === false) {
                this.fielderrorMessage.username = '使用者名稱已經存在!'
                this.invalid.username = true
            } else {
                this.invalid.username = false
            }
        },
        handleEmailFieldAbnormal() {
            if (this.response.email === false) {
                this.fielderrorMessage.email = '該電子郵件已經註冊過!'
                this.invalid.email = true
            } else {
                this.invalid.email = false
            }
        },
        handleResponse() {
            if (this.response.username === false || this.response.email === false || this.registerStatus === false) {
                this.handleUserFieldAbnormal()
                this.handleEmailFieldAbnormal()
                this.registerMessage = '註冊失敗. . .'
                this.showErrorSnackbar = true
            } else {
                this.clearForm(true)
                this.$router.push({ path: '/validate/register/success' })
            }
        },
        submitForm() {
            if (this.checkAllField() === true) {
                this.snackbarMessage = '註冊表單提交成功!'
                this.showSnackbar = true
                axios
                    .post('https://hoshi-plant.serveirc.com/register/user/confrim', {
                        username: this.register.username,
                        password: this.register.password,
                        email: this.register.email,
                    })
                    .then((response) => {
                        this.response.items = response.data.query_res
                        this.response.username = this.response.items.form_username
                        this.response.email = this.response.items.form_email
                        this.registerStatus = this.response.items.register_status
                        this.handleResponse()
                    })
                    .catch((error) => {
                        this.errorMessage = error
                        alert(this.errorMessage)
                    })
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
@import '~vue-material/src/theme/engine';
</style>
