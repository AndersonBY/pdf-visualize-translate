/**
 * @Author: Bi Ying
 * @Date:   2024-07-22 22:59:16
 * @Last Modified by:   Bi Ying
 * @Last Modified time: 2024-07-23 15:04:33
 */
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import '@icon-park/vue-next/styles/index.css';


const app = createApp(App)
app.use(Antd)
app.mount('#app')
