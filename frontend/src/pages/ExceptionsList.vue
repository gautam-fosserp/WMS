<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-5">
      <h1 class="text-2xl font-bold tracking-tight">Exceptions</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        <template v-if="loading">Loading exceptions…</template>
        <template v-else-if="tasks.length">
          {{ tasks.length }} {{ tasks.length === 1 ? 'task needs' : 'tasks need' }} attention
        </template>
        <template v-else>Everything is running smoothly</template>
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
        v-for="n in 2"
        :key="n"
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-4"
      >
        <div class="mb-3 flex items-center justify-between">
          <div class="h-4 w-36 rounded bg-slate-200"></div>
          <div class="h-5 w-16 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-3 h-3 w-44 rounded bg-slate-100"></div>
        <div class="mb-4 h-12 rounded-lg bg-slate-100"></div>
        <div class="h-10 rounded-lg bg-slate-100"></div>
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
      <p class="font-semibold text-slate-800">No exceptions</p>
      <p class="mt-1 text-sm text-slate-500">Reported issues will show up here.</p>
    </div>

    <!-- Exception list -->
    <div
      v-for="task in tasks"
      :key="task.name"
      class="mb-3 flex overflow-hidden rounded-xl border border-red-200 bg-white shadow-sm"
    >
      <div class="w-1.5 shrink-0 bg-red-500"></div>

      <div class="min-w-0 flex-1 p-4">
        <!-- Title row -->
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
            <div class="mt-0.5 text-sm text-slate-500">Qty: {{ task.qty }} · {{ task.warehouse }}</div>
          </div>
          <span
            class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold"
            :class="task.task_type === 'Pick' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'"
          >
            {{ task.task_type }}
          </span>
        </div>

        <!-- Reason -->
        <div class="mt-3 rounded-xl bg-red-50 px-3 py-2.5">
          <div class="flex items-center gap-2 text-sm font-semibold text-red-700">
            <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
            {{ task.exception_reason }}
          </div>
          <div v-if="task.exception_notes" class="mt-1 pl-6 text-sm italic text-slate-600">
            "{{ task.exception_notes }}"
          </div>
        </div>

        <!-- Details -->
        <div class="mt-3 space-y-1.5 text-xs text-slate-500">
          <!-- Pick-specific: DN + Customer -->
          <div v-if="task.task_type === 'Pick'">
            DN: <span class="font-mono">{{ task.delivery_note || '—' }}</span> · Customer: {{ task.customer || '—' }}
          </div>

          <!-- Pick-specific: source bin -->
          <div v-if="task.task_type === 'Pick' && task.source_bin" class="flex items-center gap-1.5">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
            Bin: <span class="rounded bg-slate-100 px-1.5 py-0.5 font-mono font-medium text-slate-700">{{ task.source_bin }}</span>
          </div>

          <!-- Putaway-specific: target bin -->
          <div v-if="task.task_type === 'Putaway' && task.target_bin" class="flex items-center gap-1.5">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
            Bin: <span class="rounded bg-slate-100 px-1.5 py-0.5 font-mono font-medium text-slate-700">{{ task.target_bin }}</span>
          </div>

          <div class="flex items-center gap-1.5 text-slate-400">
            <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
            Reported by {{ task.exception_reported_by }} · {{ formatTime(task.exception_reported_at) }}
          </div>
        </div>

        <!-- Actions -->
        <div class="mt-4 flex flex-col gap-2">
          <button
            class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
            :disabled="resolvingTask === task.name"
            @click="resolve(task, true)"
          >
            <svg v-if="resolvingTask !== task.name" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-3-6.7L21 8" /><path d="M21 3v5h-5" /></svg>
            <svg v-else class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-6.2-8.6" /></svg>
            {{ resolvingTask === task.name
              ? 'Working…'
              : task.task_type === 'Pick'
                ? 'Reassign to another bin'
                : 'Reassign new bin' }}
          </button>
          <button
            class="w-full rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-medium text-slate-700 transition active:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
            :disabled="resolvingTask === task.name"
            @click="resolve(task, false)"
          >
            {{ task.task_type === 'Pick' ? 'Reopen same bin' : 'Reopen manually' }}
          </button>
        </div>
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

const tasks = ref([])
const loading = ref(true)
const errorMsg = ref('')
const resolvingTask = ref('')

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
      showToast(res.message || 'Exception resolved', 'success')
      await loadExceptions()
    } else {
      showToast(res.message || 'Could not resolve exception')
    }
  } catch (e) {
    showToast(e.message || 'Failed to resolve exception')
  } finally {
    resolvingTask.value = ''
  }
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(dt.replace(' ', 'T')).toLocaleString()
}

onMounted(loadExceptions)
onBeforeUnmount(() => clearTimeout(toastTimer))
</script>