<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-5">
      <h1 class="text-2xl font-bold tracking-tight">Bins</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        <template v-if="loading">Loading bins…</template>
        <template v-else-if="bins.length">
          {{ bins.length }} {{ bins.length === 1 ? 'bin' : 'bins' }}
        </template>
        <template v-else>No bins to show</template>
      </p>
    </header>

    <!-- Search + scan -->
    <section class="mb-4">
      <div class="flex gap-2">
        <div class="relative flex-1">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input
            v-model="search"
            type="text"
            aria-label="Search bins"
            class="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-3 font-mono text-sm shadow-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            placeholder="Bin ID or item code"
            @keyup.enter="loadBins"
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

      <div v-if="cameraActive" class="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
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

    <!-- Status chips -->
    <div class="-mx-4 mb-5 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <button
        v-for="opt in statusOptions"
        :key="opt.value"
        class="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1.5 text-[13px] font-medium transition active:scale-95"
        :class="status === opt.value
          ? 'border-blue-600 bg-blue-600 text-white shadow-sm'
          : 'border-slate-300 bg-white text-slate-700'"
        @click="status = opt.value; loadBins()"
      >
        <span
          v-if="opt.value"
          class="h-2 w-2 rounded-full"
          :class="status === opt.value ? 'bg-white' : dotClass(opt.value)"
        ></span>
        {{ opt.label }}
      </button>
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
        v-for="n in 4"
        :key="n"
        class="animate-pulse rounded-xl border border-slate-200 bg-white p-4"
      >
        <div class="mb-3 flex items-center justify-between">
          <div class="h-4 w-28 rounded bg-slate-200"></div>
          <div class="h-5 w-16 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-3 h-3 w-36 rounded bg-slate-100"></div>
        <div class="h-2 w-full rounded-full bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="bins.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-slate-500">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /><path d="M3.3 7.5L12 12.5l8.7-5M12 22V12.5" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No bins match.</p>
      <p class="mt-1 text-sm text-slate-500">Try a different bin ID, item code or status.</p>
    </div>

    <!-- Bin list -->
    <div
      v-for="bin in bins"
      :key="bin.name"
      class="mb-3 flex cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition active:scale-[0.99] active:bg-slate-50"
      role="button"
      tabindex="0"
      @click="openBin(bin)"
      @keydown.enter="openBin(bin)"
    >
      <!-- Status accent -->
      <div class="w-1.5 shrink-0" :class="accentClass(bin.status)"></div>

      <div class="min-w-0 flex-1 p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="truncate font-mono text-base font-semibold">{{ bin.bin_id }}</div>
            <div class="mt-0.5 truncate text-xs text-slate-500">
              {{ bin.warehouse }}
              <span v-if="bin.bin_type"> · {{ bin.bin_type }}</span>
            </div>
          </div>
          <span
            class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
            :class="{
              'bg-green-100 text-green-800': bin.status === 'Vacant',
              'bg-blue-100 text-blue-800': bin.status === 'Occupied',
              'bg-red-100 text-red-800': bin.status === 'Blocked',
            }"
          >
            <span class="h-1.5 w-1.5 rounded-full" :class="dotClass(bin.status)"></span>
            {{ bin.status }}
          </span>
        </div>

        <div v-if="bin.current_item" class="mt-3 border-t border-slate-100 pt-3">
          <div class="flex items-baseline justify-between gap-3">
            <div class="min-w-0 truncate text-sm font-medium text-slate-800">{{ bin.current_item }}</div>
            <div class="shrink-0 text-xs text-slate-500">
              Qty: <span class="font-semibold text-slate-700">{{ bin.qty_in_bin }}</span><span v-if="bin.max_capacity"> / {{ bin.max_capacity }}</span>
            </div>
          </div>
          <div
            v-if="bin.max_capacity"
            class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100"
          >
            <div
              class="h-full rounded-full transition-all"
              :class="fillPct(bin) >= 90 ? 'bg-amber-500' : 'bg-blue-500'"
              :style="{ width: fillPct(bin) + '%' }"
            ></div>
          </div>
        </div>
        <div v-else class="mt-3 border-t border-slate-100 pt-3 text-sm italic text-slate-400">Empty</div>
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
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { Html5Qrcode } from 'html5-qrcode'

const router = useRouter()
const bins = ref([])
const loading = ref(true)
const errorMsg = ref('')
const search = ref('')
const status = ref('')
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

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Vacant', value: 'Vacant' },
  { label: 'Occupied', value: 'Occupied' },
  { label: 'Blocked', value: 'Blocked' },
]

async function loadBins() {
  loading.value = true
  errorMsg.value = ''
  try {
    bins.value = await call('wms.api.putaway.get_bins', {
      search: search.value || null,
      status: status.value || null,
    })
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load bins'
  } finally {
    loading.value = false
  }
}

function openBin(bin) {
  router.push({ name: 'BinDetail', params: { binName: bin.name } })
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
        loadBins()
      },
      () => {}
    )
  } catch (err) {
    console.error('Camera error:', err)
    showToast("Couldn't access the camera. Enter a bin ID or item code instead.")
    cameraActive.value = false
  }
}

async function stopCamera() {
  if (scanner) {
    try { await scanner.stop(); await scanner.clear() } catch (e) {}
  }
  cameraActive.value = false
}

// Display-only helpers (styling, no business logic)
function accentClass(s) {
  if (s === 'Vacant') return 'bg-green-500'
  if (s === 'Occupied') return 'bg-blue-500'
  if (s === 'Blocked') return 'bg-red-500'
  return 'bg-slate-300'
}

function dotClass(s) {
  if (s === 'Vacant') return 'bg-green-500'
  if (s === 'Occupied') return 'bg-blue-500'
  if (s === 'Blocked') return 'bg-red-500'
  return 'bg-slate-400'
}

function fillPct(bin) {
  const max = Number(bin.max_capacity || 0)
  if (!max) return 0
  return Math.min(100, Math.round((Number(bin.qty_in_bin || 0) / max) * 100))
}

onMounted(loadBins)
onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  if (cameraActive.value) stopCamera()
})
</script>