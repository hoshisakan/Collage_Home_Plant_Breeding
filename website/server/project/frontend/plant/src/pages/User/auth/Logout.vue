<template>
    <div class="md-layout">
        <md-empty-state class="md-accent" md-rounded md-icon="login" md-label="" md-description="">
            <h2 class="message">即將登出</h2>
            <h3 class="message">重新導向登入頁面 {{ this.count }}</h3>
        </md-empty-state>
    </div>
</template>

<script>
export default {
    name: 'logout-page',
    data() {
        return {
            count: '',
            timer: '',
        }
    },
    created() {
        this.logOut()
    },
    mounted() {
        // this.logOut()
    },
    methods: {
        resetLocalStorageState() {
            // window.localStorage.setItem('loginAuthToken', '')
            // window.localStorage.setItem('loginUsername', '')
            // window.localStorage.removeItem('loginAuthToken')
            // window.localStorage.removeItem('loginUsername')
            window.localStorage.clear()
        },
        logOut() {
            const TIME_COUNT = 1
            this.resetLocalStorageState()
            if (!this.timer) {
                this.count = TIME_COUNT
                this.timer = setInterval(() => {
                    if (this.count > 0 && this.count <= TIME_COUNT) {
                        this.count--
                    } else {
                        clearInterval(this.timer)
                        this.timer = null
                        this.$router.push({ path: '/validate/login' })
                    }
                }, 1000)
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
h3.message {
    text-align: center;
    color: #000000;
}
</style>
