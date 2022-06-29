<template>
    <div class="wrapper" :class="{ 'nav-open': $sidebar.showSidebar }">
        <!-- 載入側邊欄 -->
        <side-bar :sidebar-item-color="sidebarBackground" :sidebar-background-image="sidebarBackgroundImage">
            <sidebar-link to="/user/dashboard">
                <md-icon>dashboard</md-icon>
                <p>儀錶板</p>
            </sidebar-link>
            <!-- <sidebar-link to='/user/chart'>
        <md-icon>table_chart</md-icon>
        <p>圖表分析</p>
      </sidebar-link> -->
            <sidebar-link to="/user/table">
                <md-icon>content_paste</md-icon>
                <p>異常數據</p>
            </sidebar-link>
            <sidebar-link to="/user/control">
                <md-icon>toggle_on</md-icon>
                <p>繼電器控制</p>
            </sidebar-link>
            <sidebar-link to="/user/mobile-logout">
                <md-icon>account_box</md-icon>
                <p>使用者登出</p>
            </sidebar-link>
        </side-bar>

        <!-- 載入頂端的版面與主要的頁面，以及底部的版面 -->
        <div class="main-panel">
            <top-navbar></top-navbar>
            <dashboard-content> </dashboard-content>
            <content-footer v-if="!$route.meta.hideFooter"></content-footer>
        </div>
    </div>
</template>

<script>
/*
  引入頂端的版面
*/
import TopNavbar from './TopNavbar.vue'
/*
  引入底部的版面
*/
import ContentFooter from './ContentFooter.vue'
/*
  引入主要的內容
*/
import DashboardContent from './Content.vue'

export default {
    components: {
        TopNavbar,
        DashboardContent,
        ContentFooter,
    },
    data() {
        return {
            timer: '',
            alert_enable: false,
            /*
       被選中的側邊攔清單項目之顏色
      */
            sidebarBackground: 'green',
            /*
       側邊欄的背景圖片
      */
            sidebarBackgroundImage: require('@/assets/img/test.jpg'),
        }
    },
    mounted() {
        // this.InitOnce()
    },
    methods: {
        // 初始化OneSignal的通知
        InitOnce() {
            if (this.alert_enable !== true) {
                var OneSignal = window.OneSignal || []
                OneSignal.push(function () {
                    OneSignal.init({
                        appId: 'cc5f345e-09f7-4b47-8f56-1f5509e417ba',
                        autoResubscribe: true,
                        notifyButton: {
                            enable: true,
                        },
                        // allowLocalhostAsSecureOrigin: true
                    })
                    OneSignal.showNativePrompt()
                    OneSignal.showSlidedownPrompt()
                })
            }
            this.alert_enable = true
        },
    },
    beforeDestroy() {
        clearInterval(this.timer)
    },
}
</script>
