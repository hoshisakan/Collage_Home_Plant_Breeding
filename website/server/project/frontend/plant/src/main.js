import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'
import './registerServiceWorker'
import routes from './router/index'
import store from './store'
// Plugins
import GlobalComponents from './globalComponents'
import GlobalDirectives from './globalDirectives'
// MaterialDashboard plugin
import MaterialDashboard from './material-dashboard'
import Chartist from 'chartist'

// Vue.config.productionTip = false;

const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes,
})

Vue.prototype.$Chartist = Chartist

Vue.use(VueRouter)
Vue.use(MaterialDashboard)
Vue.use(GlobalComponents)
Vue.use(GlobalDirectives)

new Vue({
    el: '#app',
    render: (h) => h(App),
    router,
    data: {
        Chartist: Chartist,
    },
})
