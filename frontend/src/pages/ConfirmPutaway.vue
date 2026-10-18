<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Full-page success overlay -->
    <div
      v-if="successMsg"
      class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white p-6"
    >
      <span class="mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg class="h-10 w-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
      </span>
      <div class="max-w-xs text-center text-xl font-semibold text-emerald-700">
        {{ successMsg }}
      </div>
      <router-link
        v-if="task?.target_bin && !isExceptionSuccess"
        :to="{ name: 'BinDetail', params: { binName: task.target_bin } }"
        class="mt-6 inline-flex items-center gap-1 rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700"
      >
        View bin {{ task.target_bin }}
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </router-link>
      <div class="mt-4 text-sm text-slate-500">Returning to task list…</div>
    </div>

    <button
      class="mb-4 inline-flex items-center gap-1.5 rounded-full py-1.5 pr-3 text-sm font-medium text-blue-600 transition active:opacity-60"
      @click="goBack"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
      Back
    </button>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-3" aria-label="Loading">
      <div class="animate-pulse rounded-2xl border border-slate-200 bg-white p-4">
        <div class="mb-3 h-4 w-40 rounded bg-slate-200"></div>
        <div class="h-6 w-20 rounded bg-slate-100"></div>
      </div>
      <div class="h-40 animate-pulse rounded-2xl bg-slate-200"></div>
      <div class="h-14 animate-pulse rounded-xl bg-slate-100"></div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Error -->
    <div
      v-else-if="errorMsg"
      class="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      role="alert"
    >
      <svg class="mt-0.5 h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
      <span>{{ errorMsg }}</span>
    </div>

    <div v-else-if="task" class="mb-6">
      <!-- Task summary -->
      <div class="mb-4 flex items-start justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="min-w-0 break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
        <span class="shrink-0 rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-blue-700">
          Qty: {{ task.qty }}
        </span>
      </div>

      <!-- Go to bin -->
      <div class="rounded-2xl bg-slate-900 px-4 py-6 text-center text-white shadow-md">
        <div class="inline-flex items-center gap-1.5 text-sm text-slate-300">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
          Go to bin
        </div>
        <div class="mt-2 break-all font-mono text-3xl font-bold tracking-tight">{{ task.target_bin || 'Not assigned' }}</div>

        <div v-if="binInfo" class="mt-4">
          <div class="flex items-baseline justify-center gap-1.5 text-sm text-slate-300">
            <span>Bin capacity:</span>
            <span :class="willExceedCapacity ? 'font-semibold text-red-300' : 'font-semibold text-white'">
              {{ binInfo.qty_in_bin }} / {{ binInfo.max_capacity || '∞' }}
            </span>
          </div>

          <div
            v-if="binInfo.max_capacity"
            class="mx-auto mt-2 h-1.5 w-full max-w-[220px] overflow-hidden rounded-full bg-white/15"
          >
            <div
              class="h-full rounded-full transition-all"
              :class="willExceedCapacity ? 'bg-red-400' : 'bg-blue-400'"
              :style="{ width: Math.min(100, Math.round((binInfo.qty_in_bin / binInfo.max_capacity) * 100)) + '%' }"
            ></div>
          </div>

          <div
            v-if="willExceedCapacity"
            class="mt-3 flex items-start justify-center gap-2 rounded-lg bg-red-500/20 px-3 py-2 text-left text-sm text-red-200"
          >
            <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
            <span>Adding {{ task.qty }} will exceed capacity (room for {{ binInfo.remaining }} only)</span>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="task && !task.target_bin"
      class="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
    >
      <svg class="mt-0.5 h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
      <span>This task has no bin assigned yet.</span>
    </div>

    <div v-else-if="task">
      <!-- Camera scanner -->
      <div v-if="cameraActive" class="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
        <div id="scanner-region" class="overflow-hidden rounded-xl bg-slate-900"></div>
        <button class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600" @click="stopCamera">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          Stop camera / enter manually
        </button>
      </div>

      <button
        v-else
        class="mb-4 flex w-full items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 py-3.5 font-semibold text-blue-700 transition active:scale-[0.99] active:bg-blue-100"
        @click="startCamera"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 012-2h2M16 4h2a2 2 0 012 2v2M20 16v2a2 2 0 01-2 2h-2M8 20H6a2 2 0 01-2-2v-2" /><path d="M4 12h16" /></svg>
        Scan Bin Barcode
      </button>

      <!-- Manual entry fallback -->
      <div class="mb-4">
        <label class="mb-1 block text-sm font-medium text-slate-600">Enter/scan bin ID</label>
        <div class="relative">
          <input
            v-model="scanResult"
            type="text"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
            class="w-full rounded-xl border bg-white p-3 pr-11 font-mono text-lg focus:outline-none focus:ring-2"
            :class="scanResult && scanResult !== task.target_bin
              ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
              : scanResult && scanResult === task.target_bin
                ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-200'
                : 'border-slate-300 focus:border-blue-500 focus:ring-blue-200'"
            placeholder="e.g. A1-R1-S1-B01"
            @keyup.enter="confirm"
          />
          <svg
            v-if="scanResult && scanResult === task.target_bin"
            class="absolute right-3 top-1/2 h-6 w-6 -translate-y-1/2 text-emerald-500"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M5 13l4 4L19 7" /></svg>
        </div>
      </div>

      <div
        v-if="scanResult && scanResult !== task.target_bin"
        class="mb-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      >
        <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
        <span>Wrong bin! Expected <span class="font-mono font-semibold">{{ task.target_bin }}</span></span>
      </div>

      <button
        class="w-full rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
        :disabled="scanResult !== task.target_bin || confirming || willExceedCapacity"
        @click="confirm"
      >
        {{ confirming ? 'Confirming…' : 'Confirm Putaway' }}
      </button>
    </div>

    <!-- Report issue -->
    <div v-if="task" class="mt-6 text-center">
      <button
        class="inline-flex items-center gap-1.5 text-sm font-medium text-red-600 underline-offset-2 hover:underline"
        @click="showExceptionForm = true"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
        Can't complete this task? Report an issue
      </button>
    </div>

    <div v-if="showExceptionForm" class="mt-4 rounded-2xl border border-red-100 bg-red-50/50 p-4">
      <label class="mb-1 block text-sm font-medium text-slate-700">What's wrong?</label>
      <select
        v-model="exceptionReason"
        class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
      >
        <option disabled value="">Select a reason</option>
        <option>Bin Full</option>
        <option>Bin Damaged or Missing</option>
        <option>Wrong Item on Task</option>
        <option>Item Damaged</option>
        <option>Other</option>
      </select>

      <textarea
        v-model="exceptionNotes"
        class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        rows="2"
        placeholder="Optional notes"
      ></textarea>

      <div class="flex gap-2">
        <button
          class="flex-1 rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-medium text-slate-700 transition active:bg-slate-100"
          @click="showExceptionForm = false"
        >
          Cancel
        </button>
        <button
          class="flex-1 rounded-xl bg-red-600 py-2.5 text-sm font-semibold text-white transition active:bg-red-700 disabled:bg-slate-300 disabled:text-slate-500"
          :disabled="!exceptionReason || reportingException"
          @click="submitException"
        >
          {{ reportingException ? 'Submitting…' : 'Submit' }}
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { Html5Qrcode } from 'html5-qrcode'

const route = useRoute()
const router = useRouter()

const task = ref(null)
const binInfo = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const scanResult = ref('')
const confirming = ref(false)
const successMsg = ref('')
const isExceptionSuccess = ref(false)
const cameraActive = ref(false)
const showExceptionForm = ref(false)
const exceptionReason = ref('')
const exceptionNotes = ref('')
const reportingException = ref(false)

let scanner = null
let redirectTimer = null

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

const willExceedCapacity = computed(() => {
  if (!binInfo.value || binInfo.value.remaining === null || binInfo.value.remaining === undefined) return false
  return task.value.qty > binInfo.value.remaining
})

function goBack() {
  if (window.history.length > 1 && window.history.state?.back) {
    router.back()
  } else {
    router.push({ name: 'TaskList' })
  }
}

async function loadTask() {
  loading.value = true
  errorMsg.value = ''
  try {
    const tasks = await call('wms.api.api.get_pending_tasks')
    task.value = tasks.find(t => t.name === route.params.taskName)

    if (!task.value) {
      errorMsg.value = 'Task not found. It may have been completed or cancelled.'
      return
    }

    if (task.value.target_bin) {
      binInfo.value = await call('wms.api.putaway.get_bin_capacity_info', {
        bin_name: task.value.target_bin,
      })
    }
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load task'
  } finally {
    loading.value = false
  }
}

async function startCamera() {
  cameraActive.value = true
  await new Promise(resolve => setTimeout(resolve, 50))

  scanner = new Html5Qrcode('scanner-region')
  try {
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      (decodedText) => {
        scanResult.value = decodedText
        stopCamera()
      },
      () => { }
    )
  } catch (err) {
    console.error('Camera start failed:', err)
    showToast('Could not access camera. Enter the bin ID manually.')
    cameraActive.value = false
  }
}

async function stopCamera() {
  if (scanner) {
    try {
      await scanner.stop()
      await scanner.clear()
    } catch (e) {}
  }
  cameraActive.value = false
}

async function confirm() {
  if (scanResult.value !== task.value.target_bin) return
  if (willExceedCapacity.value) return
  confirming.value = true
  try {
    const res = await call('wms.api.putaway.confirm_putaway', {
      task_name: task.value.name,
      scanned_bin_id: scanResult.value,
    })
    isExceptionSuccess.value = false
    successMsg.value = res.message
    redirectTimer = setTimeout(() => router.push({ name: 'TaskList' }), 2200)
  } catch (e) {
    showToast(e.message || 'Failed to confirm putaway')
  } finally {
    confirming.value = false
  }
}

async function submitException() {
  reportingException.value = true
  try {
    const res = await call('wms.api.putaway.report_exception', {
      task_name: task.value.name,
      exception_reason: exceptionReason.value,
      exception_notes: exceptionNotes.value,
    })
    showExceptionForm.value = false
    isExceptionSuccess.value = true
    successMsg.value = res.message
    redirectTimer = setTimeout(() => router.push({ name: 'TaskList' }), 2200)
  } catch (e) {
    showToast(e.message || 'Failed to report issue')
  } finally {
    reportingException.value = false
  }
}

onMounted(loadTask)

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  clearTimeout(redirectTimer)
  if (cameraActive.value) stopCamera()
})
</script>