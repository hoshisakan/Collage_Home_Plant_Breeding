<template>
    <md-card>
        <md-card-header :data-background-color="dataBackgroundColor">
          <slot name="user-header"></slot>
        </md-card-header>
        <md-card-content>
          <slot name="user-content"></slot>
        </md-card-content>
        <slot name="user-body"></slot>
        <md-card-actions :md-alignment="mdAlignment">
          <slot name="user-footer"></slot>
        </md-card-actions>
     </md-card>
</template>
<script>
export default {
  name: 'user-card',
  props: {
    dataBackgroundColor: {
      type: String,
      default: ''
    },
    mdAlignment: {
      type: String,
      default: 'left'
    }
  }
}
</script>
