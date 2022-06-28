<template>
  <div class='content'>
    <!-- <md-button type="button" class="md-primary" @click=userLogoutConfirm>登出</md-button> -->
  </div>
</template>

<script>
export default {
  data () {
    return {
    }
  },
  created () {
    this.userLogoutConfirm()
  },
  methods: {
    userLogoutConfirm () {
      var confirmLogoutRequest = confirm('確定要登出?')
      if (confirmLogoutRequest === true) {
        this.$router.push({ path: '/validate/logout' })
      } else {
        window.history.back()
      }
    }
  }
}
</script>
