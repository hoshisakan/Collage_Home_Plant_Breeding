<template>
  <div id='main'>
    <md-empty-state
      class="md-accent"
      md-rounded
      md-icon="error"
      md-label=""
      md-description="">
      <h2 class="message">重設密碼連結已失效</h2>
      <h3 class='message'>即將為您轉跳至申請頁面 {{ this.count }}</h3>
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
    this.jumpApplyResetPasswordPage()
  },
  mounted () {
    // this.jumpApplyResetPasswordPage()
  },
  methods: {
    jumpApplyResetPasswordPage () {
      const TIME_COUNT = 3
      if (!this.timer) {
        this.count = TIME_COUNT
        this.timer = setInterval(() => {
          if (this.count > 0 && this.count <= TIME_COUNT) {
            this.count--
          } else {
            clearInterval(this.timer)
            this.timer = null
            this.$router.push({ path: '/validate/apply/reset/password' })
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
