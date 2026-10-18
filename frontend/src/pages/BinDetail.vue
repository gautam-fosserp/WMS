<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <button
      class="mb-4 inline-flex items-center gap-1.5 rounded-full py-1.5 pr-3 text-sm font-medium text-blue-600 transition active:opacity-60"
      @click="goBack"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
      Back
    </button>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-3" aria-label="Loading">
      <div class="animate-pulse rounded-2xl border border-slate-200 bg-white p-5">
        <div class="mb-3 h-7 w-44 rounded bg-slate-200"></div>
        <div class="mb-4 h-3 w-28 rounded bg-slate-100"></div>
        <div class="grid grid-cols-3 gap-2">
          <div class="h-12 rounded-lg bg-slate-100"></div>
          <div class="h-12 rounded-lg bg-slate-100"></div>
          <div class="h-12 rounded-lg bg-slate-100"></div>
        </div>
      </div>
      <div class="h-32 animate-pulse rounded-2xl border border-slate-200 bg-white"></div>
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

    <div v-else-if="bin">
      <!-- Header -->
      <div class="mb-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="h-1.5" :class="accentClass(bin.status)"></div>
        <div class="p-5">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="break-all font-mono text-2xl font-bold tracking-tight">{{ bin.bin_id }}</div>
              <div class="mt-0.5 text-sm text-slate-600">{{ bin.warehouse }}</div>
            </div>
            <span
              class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
              :class="{
                'bg-green-100 text-green-800': bin.status === 'Vacant',
                'bg-blue-100 text-blue-800': bin.status === 'Occupied',
                'bg-red-100 text-red-800': bin.status === 'Blocked',
              }"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="accentClass(bin.status)"></span>
              {{ bin.status }}
            </span>
          </div>

          <div v-if="bin.bin_type" class="mt-3">
            <span class="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {{ bin.bin_type }}
            </span>
          </div>

          <!-- Location -->
          <div class="mt-4 grid grid-cols-3 gap-2 text-center">
            <div class="rounded-lg bg-slate-50 py-2.5">
              <div class="text-xs text-slate-500">Aisle</div>
              <div class="mt-0.5 font-mono text-sm font-semibold text-slate-800">{{ bin.aisle }}</div>
            </div>
            <div class="rounded-lg bg-slate-50 py-2.5">
              <div class="text-xs text-slate-500">Rack</div>
              <div class="mt-0.5 font-mono text-sm font-semibold text-slate-800">{{ bin.rack }}</div>
            </div>
            <div class="rounded-lg bg-slate-50 py-2.5">
              <div class="text-xs text-slate-500">Shelf</div>
              <div class="mt-0.5 font-mono text-sm font-semibold text-slate-800">{{ bin.shelf }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Current contents -->
      <section class="mb-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="mb-2 text-sm font-medium text-slate-500">Current contents</h2>
        <div v-if="bin.current_item" class="text-lg font-semibold leading-snug">
          {{ bin.current_item }}
        </div>
        <div v-else class="italic text-slate-400">Empty</div>

        <div class="mt-3 flex items-baseline gap-1.5">
          <span class="font-mono text-3xl font-bold">{{ bin.qty_in_bin }}</span>
          <span v-if="bin.max_capacity" class="text-slate-500">/ {{ bin.max_capacity }}</span>
          <span v-else class="text-sm text-slate-500">(no capacity set)</span>
        </div>

        <div
          v-if="bin.max_capacity"
          class="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100"
        >
          <div
            class="h-full rounded-full transition-all"
            :class="fillPct() >= 90 ? 'bg-amber-500' : 'bg-blue-500'"
            :style="{ width: fillPct() + '%' }"
          ></div>
        </div>

        <div v-if="bin.remaining !== null" class="mt-2 text-xs text-slate-500">
          {{ bin.remaining }} unit(s) of space remaining
        </div>
      </section>

      <!-- Movements -->
      <section class="mb-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="mb-3 text-sm font-medium text-slate-500">Recent movements</h2>
        <div
          v-if="bin.movements.length === 0"
          class="rounded-xl bg-slate-50 py-6 text-center text-sm italic text-slate-400"
        >
          No movements recorded yet.
        </div>
        <div
          v-for="m in bin.movements"
          :key="m.name"
          class="flex items-center gap-3 border-b border-slate-100 py-3 first:pt-0 last:border-b-0 last:pb-0"
        >
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M6 13l6 6 6-6" /></svg>
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate font-mono text-sm font-medium">{{ m.item_code }}</div>
            <div class="mt-0.5 truncate text-xs text-slate-500">
              {{ formatTime(m.completed_at) }} · {{ m.modified_by }}
            </div>
          </div>
          <span class="shrink-0 rounded-full bg-emerald-50 px-2.5 py-0.5 text-sm font-semibold text-emerald-700">+{{ m.qty }}</span>
        </div>
      </section>

      <!-- Supervisor action: unblock -->
      <div v-if="isSupervisor && bin.status === 'Blocked'" class="mt-4">
        <button
          class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
          :disabled="working"
          @click="confirmOpen = true"
        >
          <svg v-if="!working" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 017.5-2" /></svg>
          <svg v-else class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-6.2-8.6" /></svg>
          {{ working ? 'Working…' : 'Unblock bin' }}
        </button>
      </div>
    </div>

    <!-- Confirm sheet -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="confirmOpen"
        class="fixed inset-0 z-[60] flex items-end justify-center bg-slate-900/50"
        @click.self="confirmOpen = false"
      >
        <div
          class="w-full max-w-md rounded-t-2xl bg-white px-5 pb-6 pt-3 shadow-xl"
          role="dialog"
          aria-modal="true"
          aria-label="Confirm unblock"
        >
          <div class="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-300"></div>
          <div class="flex items-start gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 017.5-2" /></svg>
            </span>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold">Unblock this bin?</h2>
              <p class="mt-1 text-sm text-slate-500">
                <span class="break-all font-mono text-slate-700">{{ bin?.bin_id }}</span>
                will be available for putaway again.
              </p>
            </div>
          </div>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <button
              class="rounded-lg border border-slate-300 bg-white py-3 text-sm font-semibold text-slate-700 transition active:bg-slate-100"
              @click="confirmOpen = false"
            >
              Cancel
            </button>
            <button
              class="rounded-lg bg-blue-600 py-3 text-sm font-semibold text-white transition active:bg-blue-700"
              @click="unblock"
            >
              Unblock
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
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'

const route = useRoute()
const router = useRouter()

const bin = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const working = ref(false)
const isSupervisor = ref(false)
const confirmOpen = ref(false)

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

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    bin.value = await call('wms.api.putaway.get_bin_details', {
      bin_name: route.params.binName,
    })
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load bin'
  } finally {
    loading.value = false
  }
}

async function loadUserInfo() {
  try {
    const info = await call('wms.api.api.get_current_user_info')
    isSupervisor.value = info.is_supervisor
  } catch (e) {
    // non-fatal
  }
}

async function unblock() {
  confirmOpen.value = false
  working.value = true
  try {
    const res = await call('wms.api.putaway.unblock_bin', {
      bin_name: bin.value.name,
    })
    if (res.success) {
      showToast(res.message || 'Bin unblocked', 'success')
      await load()  // refresh
    } else {
      showToast(res.message || 'Could not unblock bin')
    }
  } catch (e) {
    showToast(e.message || 'Failed to unblock bin')
  } finally {
    working.value = false
  }
}

function formatTime(dt) {
  if (!dt) return ''
  return new Date(String(dt).replace(' ', 'T')).toLocaleString()
}

onMounted(() => {
  load()
  loadUserInfo()
})
onBeforeUnmount(() => clearTimeout(toastTimer))

function goBack() {
  if (window.history.length > 1 && window.history.state?.back) {
    router.back()
  } else {
    router.push({ name: 'BinList' })
  }
}

// Display-only helpers (styling, no business logic)
function accentClass(s) {
  if (s === 'Vacant') return 'bg-green-500'
  if (s === 'Occupied') return 'bg-blue-500'
  if (s === 'Blocked') return 'bg-red-500'
  return 'bg-slate-300'
}

function fillPct() {
  const max = Number(bin.value?.max_capacity || 0)
  if (!max) return 0
  return Math.min(100, Math.round((Number(bin.value.qty_in_bin || 0) / max) * 100))
}
</script>