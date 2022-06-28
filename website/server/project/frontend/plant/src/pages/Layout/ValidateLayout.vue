<template>
  <div>
      <dashboard-content>
      </dashboard-content>
      <!-- <content-footer v-if='!$route.meta.hideFooter'></content-footer> -->
  </div>
</template>

<script>
// import ContentFooter from './ContentFooter.vue'
import DashboardContent from './Content.vue'

export default {
  components: {
    DashboardContent
    // ContentFooter
  },
  data () {
    return {
    }
  }
}
</script>
<style>
  .main-panel{
    width: auto;
    height: auto;
    background-position:center center;
    /* background-repeat:no-repeat; */
    /* background-size: 1200px 1000px; */
  }
</style>
