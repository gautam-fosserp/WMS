<template>
  <div class="mx-auto max-w-md px-4 pb-6 pt-5 text-slate-900">
    <button
      class="mb-4 inline-flex items-center gap-1.5 rounded-full py-1.5 pr-3 text-sm font-medium text-blue-600 transition active:opacity-60"
      @click="$router.back()"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
      Back
    </button>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-3" aria-label="Loading">
      <div class="animate-pulse rounded-2xl border border-slate-200 bg-white p-4">
        <div class="mb-2 h-5 w-44 rounded bg-slate-200"></div>
        <div class="h-3 w-28 rounded bg-slate-100"></div>
      </div>
      <div class="animate-pulse rounded-2xl border border-slate-200 bg-white p-4">
        <div class="mb-2 h-4 w-36 rounded bg-slate-200"></div>
        <div class="mb-4 h-3 w-24 rounded bg-slate-100"></div>
        <div class="grid grid-cols-2 gap-3">
          <div class="h-14 rounded-xl bg-slate-100"></div>
          <div class="h-14 rounded-xl bg-slate-100"></div>
        </div>
      </div>
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

    <div v-else-if="po">
      <!-- PO summary -->
      <div class="mb-4 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /><path d="M3.3 7.5L12 12.5l8.7-5M12 22V12.5" /></svg>
        </span>
        <div class="min-w-0">
          <div class="truncate font-mono text-base font-semibold">{{ po.name }}</div>
          <div class="truncate text-sm text-slate-600">{{ po.supplier_name || po.supplier }}</div>
        </div>
      </div>

      <div
        v-if="!po.settings.default_rejected_warehouse"
        class="mb-4 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800"
      >
        <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
        <span>No Default Rejected Warehouse is set. Damaged qty cannot be entered.</span>
      </div>

      <div
        v-for="line in lines"
        :key="line.po_detail"
        class="mb-3 overflow-hidden rounded-2xl border bg-white shadow-sm"
        :class="lineError(line) ? 'border-red-300' : 'border-slate-200'"
      >
        <div class="p-4">
          <div class="font-semibold leading-snug">{{ line.item_name || line.item_code }}</div>
          <div
            v-if="line.item_name && line.item_name !== line.item_code"
            class="mt-0.5 font-mono text-xs text-slate-500"
          >{{ line.item_code }}</div>

          <!-- Quantity summary -->
          <div class="mt-3 grid grid-cols-3 gap-2 text-center">
            <div class="rounded-lg bg-slate-50 py-2">
              <div class="text-base font-semibold text-slate-800">{{ line.ordered_qty }}</div>
              <div class="text-xs text-slate-500">Ordered</div>
            </div>
            <div class="rounded-lg bg-slate-50 py-2">
              <div class="text-base font-semibold text-slate-800">{{ line.received_qty }}</div>
              <div class="text-xs text-slate-500">Received</div>
            </div>
            <div class="rounded-lg bg-blue-50 py-2">
              <div class="text-base font-bold text-blue-700">{{ line.pending_qty }}</div>
              <div class="text-xs font-medium text-blue-600">Pending</div>
            </div>
          </div>

          <!-- Inputs -->
          <div class="mt-4 grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">Received qty</label>
              <input
                v-model.number="line.input_received"
                type="number"
                inputmode="numeric"
                min="0"
                :max="line.pending_qty"
                class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-lg font-semibold focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-600">Damaged qty</label>
              <input
                v-model.number="line.input_damaged"
                type="number"
                inputmode="numeric"
                min="0"
                :max="line.input_received || 0"
                :disabled="!po.settings.default_rejected_warehouse"
                class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-lg font-semibold focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
              />
            </div>
          </div>

          <div
            v-if="shortQty(line) > 0"
            class="mt-3 inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
            {{ shortQty(line) }} short vs PO
          </div>
        </div>

        <!-- Short reason block, shown only when short and capture is enabled -->
        <div
          v-if="shortQty(line) > 0 && po.settings.capture_short_receipt_reason"
          class="border-t border-amber-100 bg-amber-50/40 p-4"
        >
          <label class="mb-1 block text-xs font-medium text-slate-600">
            Short reason <span class="text-red-500">*</span>
          </label>
          <select
            v-model="line.input_short_reason"
            class="mb-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
            <option value="">Select a reason</option>
            <option>Supplier Short Shipped</option>
            <option>Lost in Transit</option>
            <option>Backordered</option>
            <option>Cancelled by Supplier</option>
            <option>Other</option>
          </select>

          <label class="mb-1 block text-xs font-medium text-slate-600">Notes (optional)</label>
          <textarea
            v-model="line.input_short_notes"
            rows="2"
            class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            placeholder="e.g. Supplier said only 90 in stock"
          ></textarea>
        </div>

        <div
          v-if="lineError(line)"
          class="flex items-center gap-1.5 border-t border-red-100 bg-red-50 px-4 py-2 text-xs font-medium text-red-600"
        >
          <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
          {{ lineError(line) }}
        </div>
      </div>

      <!-- Submit -->
      <div class="sticky bottom-0 -mx-4 mt-5 border-t border-slate-200 bg-white/95 px-4 pb-3 pt-3 backdrop-blur">
        <button
          class="w-full rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
          :disabled="submitting || !hasAnyInput || !!globalError"
          @click="submit"
        >
          {{ submitting ? 'Submitting…' : 'Create Receipt' }}
        </button>

        <div v-if="globalError" class="mt-2.5 text-center text-sm text-red-600">{{ globalError }}</div>
        <div
          v-if="successMsg"
          class="mt-3 flex items-center justify-center gap-2 rounded-xl bg-emerald-50 py-3 text-sm font-semibold text-emerald-700"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
          {{ successMsg }}
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
        class="fixed inset-x-4 bottom-28 z-50 mx-auto flex max-w-md items-start gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg"
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

const route = useRoute()
const router = useRouter()

const po = ref(null)
const lines = ref([])
const loading = ref(true)
const errorMsg = ref('')
const submitting = ref(false)
const successMsg = ref('')

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
  errorMsg.value = ''
  try {
    const data = await call('wms.api.receiving.get_purchase_order_details', {
      po_name: route.params.poName,
    })
    po.value = data
    lines.value = (data.lines || []).map(l => ({
      ...l,
      input_received: l.pending_qty,
      input_damaged: 0,
      input_short_reason: l.existing_short_reason || '',
      input_short_notes: l.existing_short_notes || '',
    }))
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load PO'
  } finally {
    loading.value = false
  }
}

const hasAnyInput = computed(() =>
  lines.value.some(l => (l.input_received || 0) > 0)
)

const globalError = computed(() => {
  for (const line of lines.value) {
    if (lineError(line)) return 'Fix line errors before submitting.'
  }
  return ''
})

function shortQty(line) {
  const rec = Number(line.input_received || 0)
  if (rec <= 0) return 0
  return Math.max(0, line.pending_qty - rec)
}

function lineError(line) {
  const rec = Number(line.input_received || 0)
  const dmg = Number(line.input_damaged || 0)
  if (rec < 0 || dmg < 0) return 'Qty cannot be negative.'
  if (dmg > rec) return 'Damaged qty cannot exceed received qty.'
  if (rec > line.pending_qty) return `Exceeds pending qty (${line.pending_qty}).`

  const sq = shortQty(line)
  if (
    sq > 0 &&
    po.value?.settings?.capture_short_receipt_reason &&
    !line.input_short_reason
  ) {
    return 'Short reason is required.'
  }
  return ''
}

async function submit() {
  if (globalError.value) return
  submitting.value = true
  successMsg.value = ''
  try {
    const payload = {
      po_name: po.value.name,
      lines: lines.value
        .filter(l => (l.input_received || 0) > 0)
        .map(l => ({
          po_detail: l.po_detail,
          received_qty: Number(l.input_received),
          damaged_qty: Number(l.input_damaged || 0),
          short_reason: l.input_short_reason || '',
          short_notes: l.input_short_notes || '',
        })),
    }
    const res = await call('wms.api.receiving.create_purchase_receipt', { payload })
    successMsg.value = res.message
    redirectTimer = setTimeout(() => router.push({ name: 'TaskList' }), 1500)
  } catch (e) {
    showToast(e.message || 'Failed to create receipt')
  } finally {
    submitting.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  clearTimeout(redirectTimer)
})
</script>