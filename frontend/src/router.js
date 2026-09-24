import { createRouter, createWebHistory } from 'vue-router'
import { call } from 'frappe-ui'
import TaskList from './pages/TaskList.vue'
import ConfirmPutaway from './pages/ConfirmPutaway.vue'
import ExceptionsList from './pages/ExceptionsList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.DEV ? '/' : '/wms-mobile'),
  routes: [
    { path: '/', name: 'TaskList', component: TaskList },
    { path: '/task/:taskName', name: 'ConfirmPutaway', component: ConfirmPutaway },
    { path: '/exceptions', name: 'ExceptionsList', component: ExceptionsList, meta: { requiresSupervisor: true } },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.requiresSupervisor) {
    const info = await call('wms.api.api.get_current_user_info')
    if (!info.is_supervisor) {
      alert('You need supervisor access to view this page.')
      return { name: 'TaskList' }
    }
  }
})

export default router