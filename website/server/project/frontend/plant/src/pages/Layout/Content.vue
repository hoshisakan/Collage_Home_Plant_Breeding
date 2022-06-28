<template>
  <!-- 控制元件與組件進入與離開的時間 -->
  <transition name="fade" mode="out-in">
    <!-- 依據當前的路由切換至指定的頁面 -->
    <router-view></router-view>
  </transition>
</template>
<script>
export default {}
</script>
<style>
/* 切換頁面時渲染分頁的時間 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter,
.fade-leave-to
 {
  opacity: 0;
}
</style>
