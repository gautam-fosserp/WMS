<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Success overlay -->
    <div v-if="successMsg" class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white p-6">
      <span class="mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg class="h-10 w-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
      </span>
      <div class="max-w-xs text-center text-xl font-semibold text-emerald-700">
        {{ successMsg }}
      </div>
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
        <div class="mb-2 h-5 w-48 rounded bg-slate-200"></div>
        <div class="mb-4 h-3 w-28 rounded bg-slate-100"></div>
        <div class="h-2 w-full rounded-full bg-slate-100"></div>
      </div>
      <div class="h-40 animate-pulse rounded-2xl border border-slate-200 bg-white"></div>
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

    <div v-else-if="status">
      <!-- DN header -->
      <div class="mb-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="h-1.5" :class="status.fully_packed ? 'bg-emerald-500' : 'bg-violet-500'"></div>
        <div class="p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="truncate font-mono text-lg font-bold tracking-tight">{{ status.name }}</div>
              <div class="mt-0.5 truncate text-sm text-slate-600">{{ status.customer_name || status.customer }}</div>
            </div>
            <span
              v-if="status.fully_packed"
              class="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800"
            >
              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
              Ready to ship
            </span>
          </div>

          <div class="mt-4">
            <div class="mb-1.5 flex items-center justify-between text-xs">
              <span class="font-medium text-slate-600">Packed {{ status.total_packed }} / {{ status.total_expected }}</span>
              <span class="text-slate-400">{{ packedPct() }}%</span>
            </div>
            <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                class="h-full rounded-full transition-all"
                :class="status.fully_packed ? 'bg-emerald-500' : 'bg-violet-500'"
                :style="{ width: packedPct() + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Current package (with items, or on a not-yet-fully-packed DN) -->
      <div
        v-if="activePackage && !(status.fully_packed && activePackage.items.length === 0)"
        class="mb-4 rounded-2xl border-2 border-blue-500 bg-blue-50/60 p-4"
      >
        <div class="mb-3 flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="truncate font-mono text-sm font-semibold">{{ activePackage.name }}</div>
            <div class="mt-1 inline-flex items-center gap-1.5 text-xs text-slate-600">
              <span class="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
              {{ activePackage.package_type }} · Open
            </div>
          </div>
          <div class="shrink-0 rounded-full bg-white px-3 py-1 text-sm shadow-sm">
            <span class="font-bold">{{ activePackage.total_qty }}</span> unit(s)
          </div>
        </div>

        <div
          v-if="activePackage.items.length === 0"
          class="mb-3 rounded-xl border border-dashed border-blue-200 bg-white/70 py-4 text-center text-xs italic text-slate-500"
        >
          Empty — scan items to add
        </div>
        <div v-else class="mb-3 rounded-xl bg-white px-3 shadow-sm">
          <div
            v-for="(pi, idx) in activePackage.items"
            :key="idx"
            class="flex items-center justify-between gap-3 border-b border-slate-100 py-2.5 text-sm last:border-b-0"
          >
            <span class="min-w-0 truncate">{{ pi.item_code }}</span>
            <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold">{{ pi.qty }}</span>
          </div>
        </div>

        <!-- Scan input -->
        <div class="mb-3">
          <label class="mb-1.5 block text-xs font-medium text-slate-600">Scan item barcode</label>

          <!-- Camera scanner -->
          <div v-if="cameraActive" class="mb-2">
            <div id="scanner-region" class="overflow-hidden rounded-xl bg-slate-900"></div>
            <button class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600" @click="stopCamera">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
              Stop camera / enter manually
            </button>
          </div>
          <button
            v-else
            class="mb-2 flex w-full items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white py-3 text-sm font-semibold text-blue-700 transition active:scale-[0.99] active:bg-blue-50"
            @click="startCamera"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 012-2h2M16 4h2a2 2 0 012 2v2M20 16v2a2 2 0 01-2 2h-2M8 20H6a2 2 0 01-2-2v-2" /><path d="M4 12h16" /></svg>
            Scan Item Barcode
          </button>

          <!-- Manual entry fallback -->
          <input
            v-model="scanItem"
            type="text"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
            class="w-full rounded-xl border border-slate-300 bg-white p-3 font-mono focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            placeholder="Item code"
            @keyup.enter="addItem"
          />
        </div>

        <div class="flex gap-2">
          <button
            class="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
            :disabled="!scanItem || adding"
            @click="addItem"
          >
            <svg v-if="!adding" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
            {{ adding ? 'Adding…' : 'Add item' }}
          </button>
          <button
            class="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-emerald-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
            :disabled="activePackage.items.length === 0 || sealing"
            @click="askSeal"
          >
            <svg v-if="!sealing" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            {{ sealing ? 'Sealing…' : 'Seal package' }}
          </button>
        </div>
      </div>

      <!-- Empty Open package on a fully-packed DN: offer to discard -->
      <div
        v-else-if="activePackage && status.fully_packed && activePackage.items.length === 0"
        class="mb-4 rounded-2xl border-2 border-emerald-500 bg-emerald-50 p-5 text-center"
      >
        <span class="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
        </span>
        <div class="font-semibold text-emerald-900">All items packed</div>
        <div class="mt-1 text-xs text-emerald-700">
          {{ sealedPackages.length }} sealed package(s) · Ready to ship
        </div>
        <div class="mt-3 text-xs text-slate-600">
          Empty package <span class="font-mono">{{ activePackage.name }}</span> is still open.
        </div>
        <button
          class="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-medium text-slate-700 transition active:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
          :disabled="discarding"
          @click="askDiscard"
        >
          <svg v-if="!discarding" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3" /></svg>
          {{ discarding ? 'Discarding…' : 'Discard empty package' }}
        </button>
      </div>

      <!-- Fully packed, no open package -->
      <div
        v-else-if="status.fully_packed"
        class="mb-4 rounded-2xl border-2 border-emerald-500 bg-emerald-50 p-5 text-center"
      >
        <span class="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
        </span>
        <div class="font-semibold text-emerald-900">All items packed</div>
        <div class="mt-1 text-xs text-emerald-700">
          {{ sealedPackages.length }} package(s) · Ready to ship
        </div>
      </div>

      <!-- Start new package (only if not fully packed) -->
      <div v-else class="mb-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5">
        <span class="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-violet-100 text-violet-600">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2" /><path d="M3 12h18M8 8V4h8v4" /></svg>
        </span>
        <div class="mb-3 text-center text-sm text-slate-600">
          No open package. Start one to begin packing.
        </div>
        <button
          class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3.5 font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
          :disabled="starting"
          @click="startNewPackage"
        >
          <svg v-if="!starting" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
          {{ starting ? 'Starting…' : 'Start new package' }}
        </button>
      </div>

      <!-- Remaining items -->
      <section class="mb-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 class="mb-2 text-sm font-semibold text-slate-700">Remaining to pack</h2>
        <div v-if="status.lines.length === 0" class="text-xs italic text-slate-400">—</div>
        <div
          v-for="line in status.lines"
          :key="line.dn_detail"
          class="flex items-center justify-between gap-3 border-b border-slate-100 py-2.5 text-sm last:border-b-0 last:pb-0"
          :class="line.remaining_qty === 0 ? 'text-slate-400' : 'text-slate-800'"
        >
          <span class="flex min-w-0 items-center gap-2">
            <span
              v-if="line.remaining_qty === 0"
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
            >
              <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
            </span>
            <span class="truncate">{{ line.item_code }}</span>
          </span>
          <span class="shrink-0">
            <span class="font-semibold">{{ line.remaining_qty }}</span>
            <span class="text-xs text-slate-500"> / {{ line.expected_qty }}</span>
          </span>
        </div>
      </section>

      <!-- Sealed packages -->
      <section
        v-if="sealedPackages.length > 0"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <h2 class="mb-2 text-sm font-semibold text-slate-700">Sealed packages</h2>
        <div
          v-for="pkg in sealedPackages"
          :key="pkg.name"
          class="flex items-center justify-between gap-3 border-b border-slate-100 py-2.5 last:border-b-0 last:pb-0"
        >
          <span class="flex min-w-0 items-center gap-2">
            <svg class="h-4 w-4 shrink-0 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            <span class="truncate font-mono text-xs">{{ pkg.name }}</span>
          </span>
          <span class="shrink-0 text-xs text-slate-500">{{ pkg.package_type }} · {{ pkg.total_qty }} units</span>
        </div>
      </section>
    </div>

    <!-- Confirm sheet (seal / discard) -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="confirmAction"
        class="fixed inset-0 z-[60] flex items-end justify-center bg-slate-900/50"
        @click.self="confirmAction = null"
      >
        <div
          class="w-full max-w-md rounded-t-2xl bg-white px-5 pb-6 pt-3 shadow-xl"
          role="dialog"
          aria-modal="true"
          :aria-label="confirmCopy.title"
        >
          <div class="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-300"></div>
          <div class="flex items-start gap-3">
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
              :class="confirmAction === 'discard' ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'"
            >
              <svg v-if="confirmAction === 'discard'" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3" /></svg>
              <svg v-else class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            </span>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold">{{ confirmCopy.title }}</h2>
              <p class="mt-1 text-sm text-slate-500">
                <span class="break-all font-mono text-slate-700">{{ activePackage?.name }}</span>
                {{ confirmCopy.body }}
              </p>
            </div>
          </div>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <button
              class="rounded-lg border border-slate-300 bg-white py-3 text-sm font-semibold text-slate-700 transition active:bg-slate-100"
              @click="confirmAction = null"
            >
              Cancel
            </button>
            <button
              class="rounded-lg py-3 text-sm font-semibold text-white transition"
              :class="confirmAction === 'discard' ? 'bg-red-600 active:bg-red-700' : 'bg-emerald-600 active:bg-emerald-700'"
              @click="runConfirmed"
            >
              {{ confirmCopy.label }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

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
import { extractErrorMessage } from '../utils/errors'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { Html5Qrcode } from 'html5-qrcode'

const route = useRoute()
const router = useRouter()

const status = ref(null)
const activePackage = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const scanItem = ref('')
const adding = ref(false)
const sealing = ref(false)
const starting = ref(false)
const discarding = ref(false)
const successMsg = ref('')
const cameraActive = ref(false)
const confirmAction = ref(null) // 'seal' | 'discard' | null

let successTimer = null
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

const confirmCopy = computed(() => {
  if (confirmAction.value === 'discard') {
    return {
      title: 'Discard empty package?',
      body: 'has no items and will be removed.',
      label: 'Discard',
    }
  }
  return {
    title: 'Seal this package?',
    body: "can't be edited until a supervisor unseals it.",
    label: 'Seal',
  }
})

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    status.value = await call('wms.api.packing.get_dn_packing_status', {
      dn_name: route.params.dnName,
    })
    await loadActivePackage()
  } catch (e) {
    errorMsg.value = extractErrorMessage(e, 'Failed to load DN')
  } finally {
    loading.value = false
  }
}

async function loadActivePackage() {
  const open = status.value.packages.find(p => p.status === 'Open')
  if (!open) {
    activePackage.value = null
    return
  }
  activePackage.value = await call('wms.api.packing.get_package_details', {
    package_name: open.name,
  })
}

const sealedPackages = computed(() =>
  status.value ? status.value.packages.filter(p => p.status === 'Sealed') : []
)

function showSuccess(msg) {
  successMsg.value = msg
  if (successTimer) clearTimeout(successTimer)
  successTimer = setTimeout(() => { successMsg.value = '' }, 2200)
}

async function startNewPackage() {
  starting.value = true
  try {
    const res = await call('wms.api.packing.start_package', {
      dn_name: status.value.name,
      package_type: 'Carton',
    })
    await load()
    showSuccess(res.message)
  } catch (e) {
    showToast(extractErrorMessage(e, 'Failed to start package'))
  } finally {
    starting.value = false
  }
}

async function addItem() {
  if (!scanItem.value || !activePackage.value) return
  adding.value = true
  try {
    const res = await call('wms.api.packing.scan_item_to_package', {
      package_name: activePackage.value.name,
      item_code: scanItem.value,
      qty: 1,
    })
    scanItem.value = ''
    await load()
    showSuccess(res.message)
  } catch (e) {
    showToast(extractErrorMessage(e, 'Failed to add item'))
  } finally {
    adding.value = false
  }
}

function askSeal() {
  if (!activePackage.value) return
  confirmAction.value = 'seal'
}

function askDiscard() {
  if (!activePackage.value) return
  confirmAction.value = 'discard'
}

function runConfirmed() {
  const action = confirmAction.value
  confirmAction.value = null
  if (action === 'seal') sealCurrent()
  else if (action === 'discard') discardEmptyPackage()
}

async function sealCurrent() {
  if (!activePackage.value) return
  sealing.value = true
  try {
    const res = await call('wms.api.packing.seal_package', {
      package_name: activePackage.value.name,
    })
    await load()
    showSuccess(res.message)
  } catch (e) {
    showToast(extractErrorMessage(e, 'Failed to seal package'))
  } finally {
    sealing.value = false
  }
}

async function discardEmptyPackage() {
  if (!activePackage.value) return
  discarding.value = true
  try {
    await call('wms.api.packing.delete_package', {
      package_name: activePackage.value.name,
    })
    await load()
    showToast('Package discarded', 'success')
  } catch (e) {
    showToast(extractErrorMessage(e, 'Failed to discard package'))
  } finally {
    discarding.value = false
  }
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
        scanItem.value = decoded
        stopCamera()
        // Auto-add after a short delay so the UI settles
        setTimeout(() => addItem(), 100)
      },
      () => {}
    )
  } catch (err) {
    console.error('Camera error:', err)
    showToast("Couldn't access the camera. Enter the item code instead.")
    cameraActive.value = false
  }
}

async function stopCamera() {
  if (scanner) {
    try { await scanner.stop(); await scanner.clear() } catch (e) {}
  }
  cameraActive.value = false
}

function goBack() {
  if (window.history.length > 1 && window.history.state?.back) {
    router.back()
  } else {
    router.push({ name: 'PackingList' })
  }
}

// Display-only helper (styling, no business logic)
function packedPct() {
  const total = Number(status.value?.total_expected || 0)
  if (!total) return 0
  return Math.min(100, Math.round((Number(status.value.total_packed || 0) / total) * 100))
}

onMounted(load)

onBeforeUnmount(() => {
  if (successTimer) clearTimeout(successTimer)
  clearTimeout(toastTimer)
  if (cameraActive.value) stopCamera()
})
</script>