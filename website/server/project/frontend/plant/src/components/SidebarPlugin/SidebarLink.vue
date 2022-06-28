<template>
  <li class='md-list-item'>
    <!-- 路由連結 -->
    <router-link
      class='md-list-item-router md-list-item-container md-button-clean'
      v-bind='$attrs'
    >
      <div class='md-list-item-content md-ripple'>
        <slot>
          <!-- 側邊欄各清單的圖標 -->
          <md-icon>{{ link.icon }}</md-icon>
          <!-- 側邊欄各清單的名稱 -->
          <p>{{ link.name }}</p>
        </slot>
      </div>
    </router-link>
  </li>
</template>
<script>
export default {
  inject: {
    autoClose: {
      default: true
    }
  },
  props: {
    // 接收父組件傳遞的參數
    link: {
      type: [String, Object],
      default: () => {
        return {
          name: '',
          path: '',
          icon: ''
        }
      }
    }
  }
}
</script>
<style></style>
