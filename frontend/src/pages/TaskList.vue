<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-5">
      <h1 class="text-2xl font-bold tracking-tight">Open Putaway Tasks</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        <template v-if="loading">Checking for tasks…</template>
        <template v-else-if="tasks.length">
          {{ tasks.length }} {{ tasks.length === 1 ? 'task' : 'tasks' }} waiting
        </template>
        <template v-else>You're all caught up</template>
      </p>
    </header>

    <!-- Error -->
    <div
      v-if="errorMsg"
      class="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      role="alert"
    >
      <svg class="mt-0.5 h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
      <span>{{ errorMsg }}</span>
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="loading" class="space-y-3" aria-label="Loading">
      <div
        v-for="n in 3"
        :key="n"
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-4"
      >
        <div class="mb-3 flex items-center justify-between">
          <div class="h-4 w-32 rounded bg-slate-200"></div>
          <div class="h-5 w-14 rounded-full bg-slate-100"></div>
        </div>
        <div class="h-3 w-24 rounded bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading...</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="tasks.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No open tasks</p>
      <p class="mt-1 text-sm text-slate-500">New putaway tasks will show up here.</p>
    </div>

    <!-- Task list -->
    <div
      v-for="task in tasks"
      :key="task.name"
      class="mb-3 overflow-hidden rounded-xl border bg-white shadow-sm"
      :class="task.target_bin ? 'border-slate-200' : 'border-red-200'"
    >
      <div
        class="flex items-stretch"
        :class="task.target_bin ? 'cursor-pointer transition active:bg-slate-50' : ''"
        :role="task.target_bin ? 'button' : null"
        :tabindex="task.target_bin ? 0 : null"
        @click="task.target_bin ? goToTask(task) : null"
        @keydown.enter="task.target_bin ? goToTask(task) : null"
      >
        <!-- Status accent -->
        <div class="w-1.5 shrink-0" :class="task.target_bin ? 'bg-emerald-500' : 'bg-red-400'"></div>

        <div class="min-w-0 flex-1 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
            <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              Qty: {{ task.qty }}
            </span>
          </div>

          <div class="mt-3 flex items-center gap-2 text-sm text-slate-500">
            <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
            <span>Target Bin:</span>
            <span
              v-if="task.target_bin"
              class="rounded-md bg-emerald-50 px-2 py-0.5 font-mono text-sm font-medium text-emerald-700"
            >{{ task.target_bin }}</span>
            <span v-else class="rounded-md bg-red-50 px-2 py-0.5 text-sm font-medium text-red-600">Not assigned</span>
          </div>
        </div>

        <div v-if="task.target_bin" class="flex items-center pr-3 text-slate-300">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6" /></svg>
        </div>
      </div>

      <div v-if="!task.target_bin" class="border-t border-red-100 bg-red-50/40 px-4 py-2.5 pl-5">
        <button
          class="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 disabled:text-slate-400"
          :disabled="retryingTask === task.name"
          @click="retryTask(task)"
        >
          <svg
            class="h-4 w-4"
            :class="retryingTask === task.name ? 'animate-spin' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M21 12a9 9 0 11-3-6.7L21 8" /><path d="M21 3v5h-5" /></svg>
          {{ retryingTask === task.name ? 'Retrying...' : 'Retry bin assignment' }}
        </button>
      </div>
    </div>

    <!-- Toast -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-2 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-2 opacity-0"
    >
      <div
        v-if="toast.show"
        class="fixed inset-x-4 bottom-24 z-50 mx-auto flex max-w-md items-start gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg"
        :class="toast.type === 'error' ? 'bg-red-600' : 'bg-emerald-600'"
        role="alert"
        @click="hideToast"
      >
        <svg
          v-if="toast.type === 'success'"
          class="mt-0.5 h-5 w-5 shrink-0"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        ><circle cx="12" cy="12" r="9" /><path d="M8 12.5l3 3 5-6" /></svg>
        <svg
          v-else
          class="mt-0.5 h-5 w-5 shrink-0"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        ><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
        <span class="min-w-0 break-words">{{ toast.message }}</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'

const tasks = ref([])
const loading = ref(true)
const errorMsg = ref('')
const retryingTask = ref('')
const router = useRouter()

const toast = reactive({ show: false, message: '', type: 'error' })
let toastTimer = null

function showToast(message, type = 'error') {
  clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.show = true
  toastTimer = setTimeout(hideToast, 4000)
}

function hideToast() {
  clearTimeout(toastTimer)
  toast.show = false
}

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
      showToast('Bin assigned', 'success')
      await loadTasks()
    } else {
      showToast(res.message || 'Could not assign a bin')
    }
  } catch (e) {
    showToast(e.message || 'Retry failed')
  } finally {
    retryingTask.value = ''
  }
}

function goToTask(task) {
  router.push({ name: 'ConfirmPutaway', params: { taskName: task.name } })
}

onMounted(loadTasks)
onBeforeUnmount(() => clearTimeout(toastTimer))
</script>