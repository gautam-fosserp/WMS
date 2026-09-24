<template>
  <div class="p-4 max-w-md mx-auto">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-xl font-bold">Exceptions</h1>
      <router-link :to="{ name: 'TaskList' }" class="text-sm text-blue-600">
        Open Tasks →
      </router-link>
    </div>

    <div v-if="errorMsg" class="text-red-500 mb-4">{{ errorMsg }}</div>
    <div v-else-if="loading" class="text-gray-500">Loading...</div>
    <div v-else-if="tasks.length === 0" class="text-gray-500">No exceptions 🎉</div>

    <div
      v-for="task in tasks"
      :key="task.name"
      class="border border-red-200 bg-red-50 rounded-lg p-4 mb-3"
    >
      <div class="font-semibold">{{ task.item_code }}</div>
      <div class="text-sm text-gray-600">Qty: {{ task.qty }} · {{ task.warehouse }}</div>

      <div class="mt-2 text-sm">
        <span class="font-medium text-red-600">{{ task.exception_reason }}</span>
      </div>
      <div v-if="task.exception_notes" class="text-sm text-gray-600 mt-1">
        "{{ task.exception_notes }}"
      </div>
      <div class="text-xs text-gray-400 mt-1">
        Reported by {{ task.exception_reported_by }} · {{ formatTime(task.exception_reported_at) }}
      </div>

      <div class="flex gap-2 mt-3">
        <button
          class="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm disabled:bg-gray-300"
          :disabled="resolvingTask === task.name"
          @click="resolve(task, true)"
        >
          {{ resolvingTask === task.name ? 'Working...' : '🔁 Reassign new bin' }}
        </button>
        <button
          class="flex-1 bg-gray-200 py-2 rounded-lg text-sm disabled:bg-gray-100"
          :disabled="resolvingTask === task.name"
          @click="resolve(task, false)"
        >
          Reopen manually
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const tasks = ref([])
const loading = ref(true)
const errorMsg = ref('')
const resolvingTask = ref('')

async function loadExceptions() {
  loading.value = true
  errorMsg.value = ''
  try {
    tasks.value = await call('wms.api.putaway.get_exception_tasks')
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load exceptions'
    console.error('loadExceptions error:', e)
  } finally {
    loading.value = false
  }
}

async function resolve(task, reassignNewBin) {
  resolvingTask.value = task.name
  try {
    const res = await call('wms.api.putaway.resolve_exception', {
      task_name: task.name,
      reassign_new_bin: reassignNewBin,
    })
    if (res.success) {
      await loadExceptions()
    } else {
      alert(res.message)
    }
  } catch (e) {
    alert(e.message || 'Failed to resolve exception')
  } finally {
    resolvingTask.value = ''
  }
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(dt.replace(' ', 'T')).toLocaleString()
}

onMounted(loadExceptions)
</script>