/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'



const app = createApp(App)

import axios from "axios";
registerPlugins(app)

axios.defaults.withCredentials = true;
const env = process.env.NODE_ENV;
if (env === "development") {
  axios.defaults.baseURL = 'http://127.0.0.1:8066'
} else {
  axios.defaults.baseURL = ''
}


app.mount('#app')
