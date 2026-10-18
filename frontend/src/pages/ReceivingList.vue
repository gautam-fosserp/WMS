<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-5">
      <h1 class="text-2xl font-bold tracking-tight">Receive Stock</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        <template v-if="loading">Loading purchase orders…</template>
        <template v-else-if="pos.length">
          {{ pos.length }} open {{ pos.length === 1 ? 'order' : 'orders' }}
        </template>
        <template v-else>Nothing to receive</template>
      </p>
    </header>

    <!-- Scan / search bar -->
    <section class="mb-6 rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <label for="po-search" class="mb-2 block text-sm font-medium text-slate-600">
        Scan PO barcode or search
      </label>
      <div class="flex gap-2">
        <div class="relative flex-1">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input
            id="po-search"
            v-model="search"
            type="text"
            class="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-3 font-mono text-sm shadow-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            placeholder="PO number or supplier"
            @keyup.enter="loadPOs"
          />
        </div>
        <button
          class="flex w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm transition active:scale-95 active:bg-blue-700"
          title="Scan"
          aria-label="Scan with camera"
          @click="startCamera"
        >
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 012-2h2M16 4h2a2 2 0 012 2v2M20 16v2a2 2 0 01-2 2h-2M8 20H6a2 2 0 01-2-2v-2" /><path d="M4 12h16" /></svg>
        </button>
      </div>

      <div v-if="cameraActive" class="mt-3">
        <div id="scanner-region" class="overflow-hidden rounded-xl bg-slate-900"></div>
        <button
          class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600"
          @click="stopCamera"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          Stop camera
        </button>
      </div>
    </section>

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
          <div class="h-4 w-40 rounded bg-slate-200"></div>
          <div class="h-5 w-20 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-2 h-3 w-28 rounded bg-slate-100"></div>
        <div class="h-3 w-20 rounded bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="pos.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-slate-500">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No open purchase orders.</p>
      <p class="mt-1 text-sm text-slate-500">Try a different PO number or supplier name.</p>
    </div>

    <!-- Purchase order list -->
    <div
      v-for="po in pos"
      :key="po.name"
      class="mb-3 flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition active:scale-[0.99] active:bg-slate-50"
      role="button"
      tabindex="0"
      @click="openPO(po)"
      @keydown.enter="openPO(po)"
    >
      <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-50 text-base font-semibold text-blue-600">
        {{ initial(po) }}
      </span>

      <div class="min-w-0 flex-1">
        <div class="truncate font-mono text-[15px] font-semibold">{{ po.name }}</div>
        <div class="mt-0.5 truncate text-sm text-slate-600">{{ po.supplier_name || po.supplier }}</div>
        <div class="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span class="inline-flex items-center gap-1 text-xs text-slate-500">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
            {{ formatDate(po.transaction_date) }}
          </span>
          <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="statusClass(po.status)">
            {{ po.status }}
          </span>
        </div>
      </div>

      <svg class="h-5 w-5 shrink-0 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6" /></svg>
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
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { Html5Qrcode } from 'html5-qrcode'

const router = useRouter()
const pos = ref([])
const loading = ref(true)
const errorMsg = ref('')
const search = ref('')
const cameraActive = ref(false)
let scanner = null

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

async function loadPOs() {
  loading.value = true
  errorMsg.value = ''
  try {
    pos.value = await call('wms.api.receiving.get_open_purchase_orders', {
      search: search.value || null,
    })
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load purchase orders'
    console.error('loadPOs error:', e)
  } finally {
    loading.value = false
  }
}

function openPO(po) {
  router.push({ name: 'ReceivingForm', params: { poName: po.name } })
}

async function startCamera() {
  cameraActive.value = true
  await new Promise(r => setTimeout(r, 50))
  scanner = new Html5Qrcode('scanner-region')
  try {
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      (decoded) => {
        search.value = decoded
        stopCamera()
        loadPOs()
      },
      () => {}
    )
  } catch (err) {
    console.error('Camera error:', err)
    showToast("Couldn't access the camera. Enter the PO number instead.")
    cameraActive.value = false
  }
}

async function stopCamera() {
  if (scanner) {
    try { await scanner.stop(); await scanner.clear() } catch (e) {}
  }
  cameraActive.value = false
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString()
}

// Display-only helpers (styling, no business logic)
function initial(po) {
  const label = po.supplier_name || po.supplier || '?'
  return label.trim().charAt(0).toUpperCase()
}

function statusClass(status) {
  switch (status) {
    case 'To Receive and Bill':
      return 'bg-amber-50 text-amber-700'
    case 'To Receive':
      return 'bg-blue-50 text-blue-700'
    case 'To Bill':
      return 'bg-violet-50 text-violet-700'
    default:
      return 'bg-slate-100 text-slate-600'
  }
}

onMounted(loadPOs)
onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  if (cameraActive.value) stopCamera()
})
</script>