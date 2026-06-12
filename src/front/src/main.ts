import './elite-deck.css' 
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'

import App from './App.vue'
import DeckView from './views/DeckView.vue'
import TelemetryView from './views/TelemetryView.vue'
import CombatView from './views/CombatView.vue'

// ── Router ────────────────────────────────────────────────────────
// HashHistory (#/) — fonctionne sans configuration serveur particulière
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/',          component: DeckView,      name: 'deck' },
    { path: '/telemetry', component: TelemetryView, name: 'telemetry' },
    { path: '/combat',    component: CombatView,    name: 'combat' },
  ],
})

// ── Application ───────────────────────────────────────────────────
const app = createApp(App)
app.use(createPinia())  // Pinia doit être installé avant les stores
app.use(router)
app.mount('#app')
