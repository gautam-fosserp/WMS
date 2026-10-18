<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-4">
      <h1 class="text-2xl font-bold tracking-tight">Pending Picks</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        Draft Delivery Notes ready to release for picking
      </p>
    </header>

    <!-- Navigation pill -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <router-link
        :to="{ name: 'PickTaskList' }"
        class="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3.5 py-1.5 text-sm font-medium text-blue-700 transition active:scale-95 active:bg-blue-100"
      >
        Active Picks
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </router-link>
    </div>

    <!-- Search -->
    <div class="relative mb-5">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
      <input
        v-model="search"
        type="text"
        aria-label="Search delivery notes"
        class="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-3 text-sm shadow-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        placeholder="Search DN or customer"
        @keyup.enter="loadDNs"
      />
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
        <div class="mb-3 flex items-center justify-between">
          <div class="h-4 w-40 rounded bg-slate-200"></div>
          <div class="h-5 w-12 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-2 h-3 w-28 rounded bg-slate-100"></div>
        <div class="mb-4 h-3 w-36 rounded bg-slate-100"></div>
        <div class="h-10 rounded-lg bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="dns.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-slate-500">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No draft Delivery Notes pending.</p>
      <p class="mt-1 text-sm text-slate-500">Try a different DN number or customer name.</p>
    </div>

    <!-- Delivery note list -->
    <div
      v-for="dn in dns"
      :key="dn.name"
      class="mb-3 flex overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <!-- Accent: amber = needs release, green = already released -->
      <div class="w-1.5 shrink-0" :class="dn.pick_tasks === 0 ? 'bg-amber-400' : 'bg-emerald-500'"></div>

      <div class="min-w-0 flex-1 p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="truncate font-mono text-[15px] font-semibold">{{ dn.name }}</div>
            <div class="mt-0.5 truncate text-sm text-slate-700">{{ dn.customer_name || dn.customer }}</div>
          </div>
          <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
            {{ dn.status }}
          </span>
        </div>

        <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
          <span class="inline-flex items-center gap-1">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
            {{ formatDate(dn.posting_date) }}
          </span>
          <span class="inline-flex items-center gap-1">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /></svg>
            {{ dn.line_count }} item(s)
          </span>
        </div>

        <button
          v-if="dn.pick_tasks === 0"
          class="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
          :disabled="releasingDN === dn.name"
          @click="askRelease(dn)"
        >
          <svg v-if="releasingDN !== dn.name" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /><path d="M3.3 7.5L12 12.5l8.7-5M12 22V12.5" /></svg>
          <svg v-else class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-6.2-8.6" /></svg>
          {{ releasingDN === dn.name ? 'Releasing…' : 'Release to Warehouse' }}
        </button>
        <div
          v-else
          class="mt-4 flex items-center justify-center gap-1.5 rounded-lg bg-emerald-50 py-2.5 text-xs font-medium text-emerald-700"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
          Already released ({{ dn.pick_tasks }} task(s))
        </div>
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
        v-if="confirmDN"
        class="fixed inset-0 z-[60] flex items-end justify-center bg-slate-900/50"
        @click.self="confirmDN = null"
      >
        <div
          class="w-full max-w-md rounded-t-2xl bg-white px-5 pb-6 pt-3 shadow-xl"
          role="dialog"
          aria-modal="true"
          aria-label="Confirm release"
        >
          <div class="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-300"></div>
          <div class="flex items-start gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /><path d="M3.3 7.5L12 12.5l8.7-5M12 22V12.5" /></svg>
            </span>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold">Release to warehouse?</h2>
              <p class="mt-1 text-sm text-slate-500">
                <span class="break-all font-mono text-slate-700">{{ confirmDN.name }}</span>
                will be released for picking. This reserves bin stock.
              </p>
            </div>
          </div>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <button
              class="rounded-lg border border-slate-300 bg-white py-3 text-sm font-semibold text-slate-700 transition active:bg-slate-100"
              @click="confirmDN = null"
            >
              Cancel
            </button>
            <button
              class="rounded-lg bg-blue-600 py-3 text-sm font-semibold text-white transition active:bg-blue-700"
              @click="releaseDN"
            >
              Release
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
import { call } from 'frappe-ui'

const dns = ref([])
const loading = ref(true)
const errorMsg = ref('')
const search = ref('')
const releasingDN = ref('')
const confirmDN = ref(null)

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

async function loadDNs() {
  loading.value = true
  errorMsg.value = ''
  try {
    dns.value = await call('wms.api.picking.get_draft_delivery_notes', {
      search: search.value || null,
    })
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load Delivery Notes'
  } finally {
    loading.value = false
  }
}

function askRelease(dn) {
  confirmDN.value = dn
}

async function releaseDN() {
  const dn = confirmDN.value
  if (!dn) return
  confirmDN.value = null
  releasingDN.value = dn.name
  try {
    const res = await call('wms.api.picking.generate_pick_tasks', {
      dn_name: dn.name,
    })
    showToast(res?.message || 'Released to warehouse', 'success')
    await loadDNs()
  } catch (e) {
    showToast(e.message || 'Failed to release')
  } finally {
    releasingDN.value = ''
  }
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString()
}

onMounted(loadDNs)
onBeforeUnmount(() => clearTimeout(toastTimer))
</script>