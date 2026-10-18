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
        <div class="mb-2 h-4 w-40 rounded bg-slate-200"></div>
        <div class="mb-2 h-6 w-20 rounded bg-slate-100"></div>
        <div class="h-3 w-52 rounded bg-slate-100"></div>
      </div>
      <div class="h-32 animate-pulse rounded-2xl bg-slate-200"></div>
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

    <div v-else-if="task">
      <!-- Task summary -->
      <div class="mb-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
            <span class="shrink-0 rounded-full bg-emerald-50 px-3 py-1 text-sm font-bold text-emerald-700">
              Pick {{ task.qty }}
            </span>
          </div>
        </div>
        <div
          v-if="task.customer || task.delivery_note"
          class="space-y-1 border-t border-slate-100 bg-slate-50/60 px-4 py-2.5 text-xs text-slate-500"
        >
          <div v-if="task.customer" class="flex items-center gap-1.5">
            <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0116 0" /></svg>
            <span class="min-w-0 break-words">Customer: {{ task.customer }}</span>
          </div>
          <div v-if="task.delivery_note" class="flex items-center gap-1.5">
            <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" /><path d="M14 3v5h5" /></svg>
            <span class="min-w-0 break-all font-mono">DN: {{ task.delivery_note }}</span>
          </div>
        </div>
      </div>

      <!-- Go to bin -->
      <div class="mb-6 rounded-2xl bg-slate-900 px-4 py-6 text-center text-white shadow-md">
        <div class="inline-flex items-center gap-1.5 text-sm text-slate-300">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
          Go to bin
        </div>
        <div class="mt-2 break-all font-mono text-3xl font-bold tracking-tight">
          {{ task.bin_info?.bin_id || '—' }}
        </div>
        <div v-if="task.bin_info" class="mt-4 grid grid-cols-2 gap-2 text-center">
          <div class="rounded-lg bg-white/10 py-2">
            <div class="text-lg font-semibold">{{ task.bin_info.qty_in_bin }}</div>
            <div class="text-xs text-slate-300">On hand</div>
          </div>
          <div class="rounded-lg bg-white/10 py-2">
            <div class="text-lg font-semibold">{{ task.bin_info.available }}</div>
            <div class="text-xs text-slate-300">Available</div>
          </div>
        </div>
      </div>

      <!-- BIN SCAN -->
      <div v-if="cameraActiveFor === 'bin'" class="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
        <div id="scanner-region" class="overflow-hidden rounded-xl bg-slate-900"></div>
        <button class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600" @click="stopCamera">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          Stop camera / enter manually
        </button>
      </div>
      <button
        v-else-if="!scanBin"
        class="mb-3 flex w-full items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 py-3.5 font-semibold text-blue-700 transition active:scale-[0.99] active:bg-blue-100"
        @click="startCamera('bin')"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 012-2h2M16 4h2a2 2 0 012 2v2M20 16v2a2 2 0 01-2 2h-2M8 20H6a2 2 0 01-2-2v-2" /><path d="M4 12h16" /></svg>
        Scan Bin Barcode
      </button>

      <div class="mb-4">
        <label class="mb-1 block text-sm font-medium text-slate-600">Bin ID</label>
        <div class="relative">
          <input
            v-model="scanBin"
            type="text"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
            class="w-full rounded-xl border bg-white p-3 pr-11 font-mono text-lg focus:outline-none focus:ring-2"
            :class="scanBin && task.bin_info && scanBin !== task.bin_info.bin_id
              ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
              : scanBin && task.bin_info && scanBin === task.bin_info.bin_id
                ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-200'
                : 'border-slate-300 focus:border-blue-500 focus:ring-blue-200'"
            placeholder="e.g. A1-R1-S1-B01"
          />
          <svg
            v-if="scanBin && task.bin_info && scanBin === task.bin_info.bin_id"
            class="absolute right-3 top-1/2 h-6 w-6 -translate-y-1/2 text-emerald-500"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M5 13l4 4L19 7" /></svg>
        </div>
      </div>

      <div
        v-if="scanBin && task.bin_info && scanBin !== task.bin_info.bin_id"
        class="mb-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      >
        <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
        <span>Wrong bin! Expected <span class="font-mono font-semibold">{{ task.bin_info.bin_id }}</span></span>
      </div>

      <!-- ITEM SCAN (conditional) -->
      <template v-if="task.require_item_scan_on_pick">
        <div v-if="cameraActiveFor === 'item'" class="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <div id="scanner-region-item" class="overflow-hidden rounded-xl bg-slate-900"></div>
          <button class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600" @click="stopCamera">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
            Stop camera / enter manually
          </button>
        </div>
        <button
          v-else-if="!scanItem"
          class="mb-3 flex w-full items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 py-3.5 font-semibold text-blue-700 transition active:scale-[0.99] active:bg-blue-100"
          @click="startCamera('item')"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 012-2h2M16 4h2a2 2 0 012 2v2M20 16v2a2 2 0 01-2 2h-2M8 20H6a2 2 0 01-2-2v-2" /><path d="M4 12h16" /></svg>
          Scan Item Barcode
        </button>

        <div class="mb-4">
          <label class="mb-1 block text-sm font-medium text-slate-600">Item Code</label>
          <div class="relative">
            <input
              v-model="scanItem"
              type="text"
              autocomplete="off"
              autocapitalize="off"
              spellcheck="false"
              class="w-full rounded-xl border bg-white p-3 pr-11 font-mono text-lg focus:outline-none focus:ring-2"
              :class="scanItem && scanItem !== task.item_code
                ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
                : scanItem && scanItem === task.item_code
                  ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-200'
                  : 'border-slate-300 focus:border-blue-500 focus:ring-blue-200'"
              placeholder="Item barcode"
            />
            <svg
              v-if="scanItem && scanItem === task.item_code"
              class="absolute right-3 top-1/2 h-6 w-6 -translate-y-1/2 text-emerald-500"
              viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
            ><path d="M5 13l4 4L19 7" /></svg>
          </div>
        </div>

        <div
          v-if="scanItem && scanItem !== task.item_code"
          class="mb-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
          <span>Wrong item! Expected <span class="font-mono font-semibold">{{ task.item_code }}</span></span>
        </div>
      </template>

      <!-- PICKED QTY -->
      <div class="mb-5">
        <label class="mb-1 block text-sm font-medium text-slate-600">Picked qty</label>
        <input
          v-model.number="pickedQty"
          type="number"
          inputmode="numeric"
          min="1"
          :max="task.qty"
          class="w-full rounded-xl border border-slate-300 bg-white p-3 text-2xl font-bold focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
        <div
          v-if="pickedQty < task.qty"
          class="mt-2 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700"
        >
          <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
          <span>Short pick — {{ task.qty - pickedQty }} will be flagged for supervisor.</span>
        </div>
      </div>

      <button
        class="w-full rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
        :disabled="!canConfirm || confirming"
        @click="confirm"
      >
        {{ confirming ? 'Confirming…' : 'Confirm Pick' }}
      </button>

      <!-- Report Issue -->
      <div class="mt-6 text-center">
        <button
          class="inline-flex items-center gap-1.5 text-sm font-medium text-red-600 underline-offset-2 hover:underline"
          @click="showIssueForm = true"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
          Can't complete this pick? Report an issue
        </button>
      </div>

      <div v-if="showIssueForm" class="mt-4 rounded-2xl border border-red-100 bg-red-50/50 p-4">
        <label class="mb-1 block text-sm font-medium text-slate-700">What's wrong?</label>
        <select
          v-model="issueReason"
          class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          <option disabled value="">Select a reason</option>
          <option>Bin Empty</option>
          <option>Wrong Item</option>
          <option>Item Damaged</option>
          <option>Other</option>
        </select>

        <textarea
          v-model="issueNotes"
          class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          rows="2"
          placeholder="Optional notes"
        ></textarea>

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-medium text-slate-700 transition active:bg-slate-100"
            @click="showIssueForm = false"
          >
            Cancel
          </button>
          <button
            class="flex-1 rounded-xl bg-red-600 py-2.5 text-sm font-semibold text-white transition active:bg-red-700 disabled:bg-slate-300 disabled:text-slate-500"
            :disabled="!issueReason || reportingIssue"
            @click="submitIssue"
          >
            {{ reportingIssue ? 'Submitting…' : 'Submit' }}
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
        class="fixed inset-x-4 bottom-6 z-[70] mx-auto flex max-w-md items-start gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg"
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
const loading = ref(true)
const errorMsg = ref('')
const confirming = ref(false)
const successMsg = ref('')
const cameraActiveFor = ref(null)
const scanBin = ref('')
const scanItem = ref('')
const pickedQty = ref(0)

const showIssueForm = ref(false)
const issueReason = ref('')
const issueNotes = ref('')
const reportingIssue = ref(false)

let scanner = null

const toast = reactive({ show: false, message: '', type: 'error' })
let toastTimer = null
let redirectTimer = null

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

async function load() {
  loading.value = true
  try {
    const data = await call('wms.api.picking.get_pick_task_details', {
      task_name: route.params.taskName,
    })
    task.value = data
    pickedQty.value = data.qty
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load pick task'
  } finally {
    loading.value = false
  }
}

const canConfirm = computed(() => {
  if (!task.value) return false
  if (!scanBin.value || scanBin.value !== task.value.bin_info?.bin_id) return false
  if (task.value.require_item_scan_on_pick) {
    if (!scanItem.value || scanItem.value !== task.value.item_code) return false
  }
  if (!pickedQty.value || pickedQty.value <= 0) return false
  if (pickedQty.value > task.value.qty) return false
  return true
})

async function startCamera(target) {
  cameraActiveFor.value = target
  await new Promise(r => setTimeout(r, 50))
  const regionId = target === 'bin' ? 'scanner-region' : 'scanner-region-item'
  scanner = new Html5Qrcode(regionId)
  try {
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      (decoded) => {
        if (target === 'bin') scanBin.value = decoded
        else scanItem.value = decoded
        stopCamera()
      },
      () => {}
    )
  } catch (err) {
    console.error('Camera error:', err)
    showToast("Couldn't access the camera. Enter the code manually.")
    cameraActiveFor.value = null
  }
}

async function stopCamera() {
  if (scanner) {
    try { await scanner.stop(); await scanner.clear() } catch (e) {}
  }
  cameraActiveFor.value = null
}

function goBack() {
  if (window.history.length > 1 && window.history.state?.back) {
    router.back()
  } else {
    router.push({ name: 'PickTaskList' })
  }
}

async function confirm() {
  if (!canConfirm.value) return
  confirming.value = true
  successMsg.value = ''
  try {
    const res = await call('wms.api.picking.confirm_pick', {
      task_name: task.value.name,
      scanned_bin_id: scanBin.value,
      picked_qty: pickedQty.value,
      scanned_item_code: scanItem.value || null,
    })
    successMsg.value = res.message
    redirectTimer = setTimeout(() => router.push({ name: 'PickTaskList' }), 2200)
  } catch (e) {
    showToast(e.message || 'Failed to confirm pick')
  } finally {
    confirming.value = false
  }
}

async function submitIssue() {
  reportingIssue.value = true
  try {
    const res = await call('wms.api.picking.report_pick_exception', {
      task_name: task.value.name,
      reason: issueReason.value,
      notes: issueNotes.value,
    })
    showIssueForm.value = false
    successMsg.value = res.message
    redirectTimer = setTimeout(() => router.push({ name: 'PickTaskList' }), 2200)
  } catch (e) {
    showToast(e.message || 'Failed to report issue')
  } finally {
    reportingIssue.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  clearTimeout(redirectTimer)
  if (cameraActiveFor.value) stopCamera()
})
</script>