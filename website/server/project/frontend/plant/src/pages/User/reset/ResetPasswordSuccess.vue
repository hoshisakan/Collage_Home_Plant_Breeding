<template>
  <div id='main'>
    <md-empty-state
      class="md-primary"
      md-rounded
      md-icon="verified_user"
      md-label=""
      md-description="">
      <h2 class="message">密碼修改成功!</h2>
      <h3 h3 class="message">即將為您轉跳至登入頁面 {{ this.count }}</h3>
    </md-empty-state>
  </div>
</template>

<script>
export default {
  data () {
    return {
      count: '',
      timer: ''
    }
  },
  created () {
    this.jumpLoginPage()
  },
  mounted () {
    // this.jumpLoginPage()
  },
  methods: {
    setMessage () {

    },
    jumpLoginPage () {
      const TIME_COUNT = 3
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
    }
  }
}
</script>
<style lang="scss" scoped>
  h2.message {
    text-align: center;
    color: #000000;
  }
  h3.message {
    text-align: center;
    color: #000000;
  }
</style>
