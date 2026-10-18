<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-4">
      <h1 class="text-2xl font-bold tracking-tight">Completed Putaways</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        <template v-if="loading">Loading history…</template>
        <template v-else-if="tasks.length">
          {{ tasks.length }} completed {{ tasks.length === 1 ? 'putaway' : 'putaways' }}
        </template>
        <template v-else>Nothing completed yet</template>
      </p>
    </header>

    <!-- Info note -->
    <div class="mb-5 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">
      <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
      <p>
        Reverse a completed putaway only if the receipt will be cancelled or
        the putaway was wrong. Reversing decrements the bin quantity and keeps
        an audit trail.
      </p>
    </div>

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
        <div class="mb-2 h-3 w-36 rounded bg-slate-100"></div>
        <div class="mb-3 flex items-center justify-between">
          <div class="h-4 w-32 rounded bg-slate-200"></div>
          <div class="h-5 w-14 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-4 h-3 w-44 rounded bg-slate-100"></div>
        <div class="h-10 rounded-lg bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="tasks.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-slate-500">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No completed putaways.</p>
      <p class="mt-1 text-sm text-slate-500">Finished putaways will appear here.</p>
    </div>

    <!-- Task list -->
    <div
      v-for="task in tasks"
      :key="task.name"
      class="mb-3 flex overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <div class="w-1.5 shrink-0 bg-emerald-500"></div>

      <div class="min-w-0 flex-1 p-4">
        <div class="truncate font-mono text-xs text-slate-400">{{ task.name }}</div>

        <div class="mt-1 flex items-start justify-between gap-3">
          <div class="min-w-0 break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
          <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
            Qty: {{ task.qty }}
          </span>
        </div>

        <div class="mt-3 flex items-center gap-2 text-sm text-slate-500">
          <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
          <span>Bin:</span>
          <span class="rounded-md bg-emerald-50 px-2 py-0.5 font-mono text-sm font-medium text-emerald-700">{{ task.target_bin }}</span>
        </div>

        <div class="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
          Completed {{ formatTime(task.completed_at) }}
        </div>

        <button
          class="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 py-2.5 text-sm font-semibold text-red-600 transition active:scale-[0.99] active:bg-red-100 disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
          :disabled="reversingTask === task.name"
          @click="openReverseDialog(task)"
        >
          <svg v-if="reversingTask !== task.name" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 14L4 9l5-5" /><path d="M4 9h10a6 6 0 010 12h-3" /></svg>
          <svg v-else class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-6.2-8.6" /></svg>
          {{ reversingTask === task.name ? 'Reversing…' : 'Reverse putaway' }}
        </button>
      </div>
    </div>

    <!-- Reverse dialog -->
    <div
      v-if="showDialog"
      class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-4 sm:items-center"
      @click.self="closeDialog"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
        <div class="mb-4 flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 14L4 9l5-5" /><path d="M4 9h10a6 6 0 010 12h-3" /></svg>
          </span>
          <div class="min-w-0">
            <h2 class="text-lg font-bold leading-tight">Reverse putaway</h2>
            <p class="mt-1 text-sm text-slate-600">
              {{ dialogTask.item_code }} · {{ dialogTask.qty }} unit(s) from
              <span class="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs font-medium">{{ dialogTask.target_bin }}</span>
            </p>
          </div>
        </div>

        <label class="mb-1 block text-xs font-medium text-slate-600">Reason <span class="text-red-500">*</span></label>
        <select
          v-model="dialogReason"
          class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          <option value="">Select a reason</option>
          <option>PR Cancelled</option>
          <option>Wrong Item</option>
          <option>Wrong Bin</option>
          <option>Data Entry Error</option>
          <option>Other</option>
        </select>

        <label class="mb-1 block text-xs font-medium text-slate-600">Notes (optional)</label>
        <textarea
          v-model="dialogNotes"
          rows="2"
          class="mb-4 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        ></textarea>

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-medium text-slate-700 transition active:bg-slate-100"
            @click="closeDialog"
          >
            Cancel
          </button>
          <button
            class="flex-1 rounded-xl bg-red-600 py-2.5 text-sm font-semibold text-white shadow-sm transition active:bg-red-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
            :disabled="!dialogReason || reversingTask"
            @click="confirmReverse"
          >
            {{ reversingTask ? 'Working…' : 'Reverse' }}
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
        class="fixed inset-x-4 bottom-24 z-[70] mx-auto flex max-w-md items-start gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg"
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
const reversingTask = ref('')

const showDialog = ref(false)
const dialogTask = ref({})
const dialogReason = ref('')
const dialogNotes = ref('')

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
    tasks.value = await call('wms.api.putaway.get_completed_putaways')
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load completed putaways'
  } finally {
    loading.value = false
  }
}

function openReverseDialog(task) {
  dialogTask.value = task
  dialogReason.value = ''
  dialogNotes.value = ''
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  dialogTask.value = {}
  dialogReason.value = ''
  dialogNotes.value = ''
}

async function confirmReverse() {
  if (!dialogReason.value) return
  reversingTask.value = dialogTask.value.name
  try {
    const res = await call('wms.api.putaway.reverse_putaway', {
      task_name: dialogTask.value.name,
      reason: dialogReason.value,
      notes: dialogNotes.value,
    })
    closeDialog()
    showToast(res?.message || 'Putaway reversed', 'success')
    await loadTasks()
  } catch (e) {
    showToast(e.message || 'Failed to reverse putaway')
  } finally {
    reversingTask.value = ''
  }
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(String(dt).replace(' ', 'T')).toLocaleString()
}

onMounted(loadTasks)
onBeforeUnmount(() => clearTimeout(toastTimer))
</script>