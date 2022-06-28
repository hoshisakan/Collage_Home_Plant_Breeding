import Vue from 'vue'
import VueRouter from 'vue-router'
import VueMaterial from 'vue-material'
import 'vue-material/dist/vue-material.min.css'
import 'vue-material/dist/theme/default.css'
import Login from '@/pages/User/auth/Login.vue'
import Logout from '@/pages/User/auth/Logout.vue'
import Register from '@/pages/User/auth/Register.vue'
import ApplyResetPassword from '@/pages/User/reset/ApplyResetPassword.vue'
import RegisterSuccess from '@/pages/User/auth/RegisterSuccess.vue'
import RegisterFailure from '@/pages/User/auth/RegisterFailure.vue'
import ResetPassword from '@/pages/User/reset/ResetPassword.vue'
import ValidateResetPasswordFailure from '@/pages/User/reset/ValidateInvalid.vue'
import ValidateResetPasswordSuccess from '@/pages/User/reset/ResetPasswordSuccess.vue'
import MobileLogout from '@/pages/UserLogout.vue'
/*
引入網站版面的頁面
*/
import DashboardLayout from '@/pages/Layout/DashboardLayout.vue'
import ValidateLayout from '@/pages/Layout/ValidateLayout.vue'
/*
引入網站儀錶板的頁面
*/
import Dashboard from '@/pages/Dashboard.vue'
/*
引入網站檢測異常的頁面
*/
import TableList from '@/pages/TableList.vue'
/*
引入網站資料分析的頁面
*/
import DataChart from '@/pages/DataChart.vue'
import ControlInterface from '@/pages/ControlInterface.vue'

Vue.use(VueRouter)
Vue.use(VueMaterial)

const routes = [
    {
        /*
       將網站根目錄導向/user/dashboard的路由
      */
        path: '/',
        //   redirect: '/user/dashboard'
        //     path: "/",
        redirect: '/user/dashboard',
        // component: Dashboard,
    },
    {
        path: '/user',
        /*
       讓父目錄下所有的子目錄套用此版面
      */
        component: DashboardLayout,
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: Dashboard,
            },
            {
                path: 'chart',
                name: 'DataChart',
                component: DataChart,
            },
            {
                path: 'table',
                name: 'Table List',
                component: TableList,
            },
            {
                path: 'control',
                name: 'ControlInterface',
                component: ControlInterface,
            },
            {
                path: 'register',
                name: 'Register',
                component: Register,
            },
            {
                path: 'mobile-logout',
                name: 'MobileLogout',
                component: MobileLogout,
            },
        ],
    },
    {
        path: '/validate',
        component: ValidateLayout,
        children: [
            {
                path: 'login',
                name: 'Login',
                component: Login,
            },
            {
                path: 'logout',
                name: 'Logout',
                component: Logout,
            },
            {
                path: 'register',
                name: 'Register',
                component: Register,
            },
            {
                path: 'register/success',
                name: 'Register Success',
                component: RegisterSuccess,
            },
            {
                path: 'register/failure',
                name: 'Register Failure',
                component: RegisterFailure,
            },
            {
                path: 'apply/reset/password',
                name: 'Apply Reset Password',
                component: ApplyResetPassword,
            },
            {
                path: 'reset/password',
                name: 'Reset Password',
                component: ResetPassword,
            },
            {
                path: 'reset/password/failure',
                name: 'Validate Reset Password Failure',
                component: ValidateResetPasswordFailure,
            },
            {
                path: 'reset/password/success',
                name: 'Validate Reset Password Success',
                component: ValidateResetPasswordSuccess,
            },
        ],
    },
]

export default routes
