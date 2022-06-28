<template>
    <md-card>
        <md-card-header :data-background-color="dataBackgroundColor">
            <slot name="image-header"></slot>
        </md-card-header>

        <md-card-content>
            <slot name="image-content"></slot>
        </md-card-content>

        <md-card-actions md-alignment="left">
            <slot name="image-footer"></slot>
        </md-card-actions>
    </md-card>
</template>
<script>
export default {
    name: 'image-card',
    props: {
        dataBackgroundColor: {
            type: String,
            default: '',
        },
    },
}
</script>
<style scoped></style>
