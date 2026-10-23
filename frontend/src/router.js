import { createRouter, createWebHistory } from 'vue-router'
import { call } from 'frappe-ui'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import TaskList from './pages/TaskList.vue'
import ConfirmPutaway from './pages/ConfirmPutaway.vue'
import ExceptionsList from './pages/ExceptionsList.vue'
import ReceivingList from './pages/ReceivingList.vue'
import ReceivingForm from './pages/ReceivingForm.vue'
import BinList from './pages/BinList.vue'
import BinDetail from './pages/BinDetail.vue'
import CompletedPutaways from './pages/CompletedPutaways.vue'
import PickTaskList from './pages/PickTaskList.vue'
import ConfirmPick from './pages/ConfirmPick.vue'
import PendingPicks from './pages/PendingPicks.vue'
import PackingList from './pages/PackingList.vue'
import PackingStation from './pages/PackingStation.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.DEV ? '/' : '/wms-mobile'),
  routes: [
    // Home
    { path: '/', name: 'Dashboard', component: Dashboard },
    { path: '/login', name: 'Login', component: Login },
    // Putaway
    { path: '/putaway', name: 'TaskList', component: TaskList },
    { path: '/task/:taskName', name: 'ConfirmPutaway', component: ConfirmPutaway, props: true },

    // Receiving
    { path: '/receiving', name: 'ReceivingList', component: ReceivingList },
    { path: '/receiving/:poName', name: 'ReceivingForm', component: ReceivingForm, props: true },

    // Bins
    { path: '/bins', name: 'BinList', component: BinList },
    { path: '/bin/:binName', name: 'BinDetail', component: BinDetail, props: true },

    // Picking — /pending BEFORE /:taskName so it isn't shadowed
    { path: '/picks', name: 'PickTaskList', component: PickTaskList },
    { path: '/picks/pending', name: 'PendingPicks', component: PendingPicks },
    { path: '/picks/:taskName', name: 'ConfirmPick', component: ConfirmPick, props: true },

    // Packing
    { path: '/packing', name: 'PackingList', component: PackingList },
    { path: '/packing/:dnName', name: 'PackingStation', component: PackingStation, props: true },

    // Supervisor
    {
      path: '/completed-putaways',
      name: 'CompletedPutaways',
      component: CompletedPutaways,
      meta: { requiresSupervisor: true },
    },
    {
      path: '/exceptions',
      name: 'ExceptionsList',
      component: ExceptionsList,
      meta: { requiresSupervisor: true },
    },
  ],
})

let cachedUserInfo = null

router.beforeEach(async (to) => {
  if (to.meta.requiresSupervisor) {
    if (!cachedUserInfo) {
      cachedUserInfo = await call('wms.api.api.get_current_user_info')
    }
    if (!cachedUserInfo.is_supervisor) {
      alert('You need supervisor access to view this page.')
      return { name: 'Dashboard' }  // was: TaskList
    }
  }
})

export default router