<template>
  <md-toolbar md-elevation='0' class='md-transparent'>
    <div class='md-toolbar-row'>
      <div class='md-toolbar-section-start'>
        <h3 class='md-title'>{{ $route.name }}</h3>
      </div>
      <div class='md-toolbar-section-end'>
        <md-button
          class='md-just-icon md-simple md-toolbar-toggle'
          :class='{ toggled: $sidebar.showSidebar }'
          @click='toggleSidebar'
        >
          <span class='icon-bar'></span>
          <span class='icon-bar'></span>
          <span class='icon-bar'></span>
        </md-button>

        <div class='md-collapse'>
          <md-list>
            <md-list-item href='/user/dashboard'>
              <i class='material-icons'>dashboard</i>
            </md-list-item>
<!-- 
            <md-list-item href='/user/chart'>
              <i class='material-icons'>table_chart</i>
            </md-list-item> -->

            <md-list-item href='/user/table'>
              <i class='material-icons'>content_paste</i>
            </md-list-item>

            <md-list-item href='/user/control'>
              <i class='material-icons'>toggle_on</i>
            </md-list-item>

            <li class='md-list-item'>
              <div class='md-list-item-content'>
                 <drop-down>
                    <md-button
                      slot='title'
                      class='md-button md-just-icon md-simple'
                      data-toggle='dropdown'
                    >
                      <md-icon>account_box</md-icon>
                    </md-button>
                    <ul class='dropdown-menu dropdown-menu-right'>
                      <li><a href='/validate/logout'>登出</a></li>
                    </ul>
                 </drop-down>
               </div>
            </li>
          </md-list>
        </div>
      </div>
    </div>
  </md-toolbar>
</template>

<script>
export default {
  data () {
    return {
    }
  },
  methods: {
    toggleSidebar () {
      this.$sidebar.displaySidebar(!this.$sidebar.showSidebar)
    }
  }
}
</script>

<style lang='css'></style>
