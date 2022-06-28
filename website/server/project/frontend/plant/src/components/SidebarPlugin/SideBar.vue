<template>
  <div
    class='sidebar'
    :data-color='sidebarItemColor'
    :data-image='sidebarBackgroundImage'
    :style='sidebarStyle'
  >
    <div class='logo'>
      <!-- 網站的圖標按下後會導向根目錄 -->
      <a href='/' class='simple-text logo-mini'>
        <div class='logo-img'>
          <img :src='imgLogo' alt='' />
        </div>
      </a>

      <!-- 顯示在圖標旁的標題名稱，按下後會導向根目錄 -->
      <a
        href='/'
        target='_blank'
        class='simple-text logo-normal'
      >
        {{ title }}
      </a>
    </div>
    <div class='sidebar-wrapper'>
      <md-list class='nav'>
        <!-- 載入側邊欄的連結路由與對應的名稱 -->
        <slot>
          <sidebar-link
            v-for='(link, index) in sidebarLinks'
            :key='link.name + index'
            :to='link.path'
            :link='link'
          >
          </sidebar-link>
        </slot>
      </md-list>
    </div>
  </div>
</template>
<script>
import SidebarLink from './SidebarLink.vue'

export default {
  components: {
    SidebarLink
  },
  props: {
    // 顯示在圖標旁的標題名稱
    title: {
      type: String,
      default: 'Plant'
    },
    // 側邊欄背景圖
    sidebarBackgroundImage: {
      type: String,
      default: require('@/assets/img/test.jpg')
    },
    // 網站圖標
    imgLogo: {
      type: String,
      default: require('@/assets/img/nature.png')
    },
    sidebarItemColor: {
      type: String,
      default: 'green'
    },
    sidebarLinks: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    sidebarStyle () {
      return {
        backgroundImage: `url(${this.sidebarBackgroundImage})`
      }
    }
  }
}
</script>
<style>
@media screen and (min-width: 991px) {
  .nav-mobile-menu {
    display: none
  }
}
</style>
