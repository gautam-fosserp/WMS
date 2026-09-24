<template>
  <div class="p-4 max-w-md mx-auto">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-xl font-bold">Open Putaway Tasks</h1>
      <router-link v-if="isSupervisor" :to="{ name: 'ExceptionsList' }" class="text-sm text-red-500">
        ⚠ Exceptions
      </router-link>
    </div>

    <div v-if="errorMsg" class="text-red-500 mb-4">{{ errorMsg }}</div>
    <div v-else-if="loading" class="text-gray-500">Loading...</div>
    <div v-else-if="tasks.length === 0" class="text-gray-500">No open tasks 🎉</div>

    <div v-for="task in tasks" :key="task.name" class="border rounded-lg p-4 mb-3 shadow-sm">
      <div class="cursor-pointer active:bg-gray-100 -m-4 p-4 mb-0 rounded-t-lg"
        @click="task.target_bin ? goToTask(task) : null">
        <div class="font-semibold">{{ task.item_code }}</div>
        <div class="text-sm text-gray-600">Qty: {{ task.qty }}</div>
        <div class="text-sm text-gray-600">
          Target Bin:
          <span v-if="task.target_bin" class="font-mono">{{ task.target_bin }}</span>
          <span v-else class="text-red-500">Not assigned</span>
        </div>
      </div>

      <button v-if="!task.target_bin" class="mt-3 text-sm text-blue-600 font-medium disabled:text-gray-400"
        :disabled="retryingTask === task.name" @click="retryTask(task)">
        {{ retryingTask === task.name ? 'Retrying...' : '🔄 Retry bin assignment' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'

const tasks = ref([])
const loading = ref(true)
const errorMsg = ref('')
const retryingTask = ref('')
const router = useRouter()

async function loadTasks() {
  loading.value = true
  errorMsg.value = ''
  try {
    tasks.value = await call('wms.api.api.get_pending_tasks')
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load tasks'
    console.error('loadTasks error:', e)
  } finally {
    loading.value = false
  }
}

async function retryTask(task) {
  retryingTask.value = task.name
  try {
    const res = await call('wms.api.putaway.retry_bin_suggestion', {
      task_name: task.name,
    })
    if (res.success) {
      await loadTasks()
    } else {
      alert(res.message)
    }
  } catch (e) {
    alert(e.message || 'Retry failed')
  } finally {
    retryingTask.value = ''
  }
}

function goToTask(task) {
  router.push({ name: 'ConfirmPutaway', params: { taskName: task.name } })
}

const isSupervisor = ref(false)

async function loadUserInfo() {
  const info = await call('wms.api.api.get_current_user_info')
  isSupervisor.value = info.is_supervisor
}

onMounted(() => {
  loadTasks()
  loadUserInfo()
})
</script>