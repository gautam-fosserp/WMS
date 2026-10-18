<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-4">
      <h1 class="text-2xl font-bold tracking-tight">Packing</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        Draft Delivery Notes ready to pack
      </p>
    </header>

    <!-- Search -->
    <div class="relative mb-5">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
      <input
        v-model="search"
        type="text"
        aria-label="Search delivery notes"
        class="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-3 text-sm shadow-sm placeholder:text-slate-400 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200"
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
          <div class="h-5 w-16 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-3 h-3 w-28 rounded bg-slate-100"></div>
        <div class="h-2 w-full rounded-full bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="dns.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-violet-100 text-violet-600">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2" /><path d="M3 12h18M8 8V4h8v4" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No Draft Delivery Notes.</p>
      <p class="mt-1 text-sm text-slate-500">Try a different DN number or customer name.</p>
    </div>

    <!-- Delivery note list -->
    <div
      v-for="dn in dns"
      :key="dn.name"
      class="mb-3 cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition active:scale-[0.99] active:bg-slate-50"
      role="button"
      tabindex="0"
      @click="openPacking(dn)"
      @keydown.enter="openPacking(dn)"
    >
      <div class="flex items-stretch">
        <!-- Accent: green = packed, amber = partial, grey = not started -->
        <div
          class="w-1.5 shrink-0"
          :class="dn.fully_packed ? 'bg-emerald-500' : dn.total_packed > 0 ? 'bg-amber-400' : 'bg-slate-300'"
        ></div>

        <div class="min-w-0 flex-1 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="truncate font-mono text-[15px] font-semibold">{{ dn.name }}</div>
              <div class="mt-0.5 truncate text-sm text-slate-700">{{ dn.customer_name || dn.customer }}</div>
            </div>
            <span
              class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="{
                'bg-green-100 text-green-800': dn.fully_packed,
                'bg-amber-100 text-amber-800': !dn.fully_packed && dn.total_packed > 0,
                'bg-slate-100 text-slate-600': dn.total_packed === 0,
              }"
            >
              {{ dn.fully_packed ? 'Packed' : (dn.total_packed > 0 ? 'Partial' : 'Not Packed') }}
            </span>
          </div>

          <!-- Pack progress -->
          <div class="mt-3">
            <div class="mb-1.5 flex items-center justify-between text-xs">
              <span class="font-medium text-slate-600">Packed {{ dn.total_packed }} / {{ dn.total_expected }}</span>
              <span class="text-slate-400">{{ packPct(dn) }}%</span>
            </div>
            <div class="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                class="h-full rounded-full transition-all"
                :class="dn.fully_packed ? 'bg-emerald-500' : 'bg-violet-500'"
                :style="{ width: packPct(dn) + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <div class="flex items-center pr-3 text-slate-300">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6" /></svg>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-100 bg-slate-50/60 px-4 py-2.5 pl-5 text-xs text-slate-500">
        <span class="inline-flex items-center gap-1.5">
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h9" /></svg>
          Picked: {{ dn.pick_status }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2" /><path d="M3 12h18M8 8V4h8v4" /></svg>
          {{ dn.package_count }} package(s)
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'

const router = useRouter()
const dns = ref([])
const loading = ref(true)
const errorMsg = ref('')
const search = ref('')

async function loadDNs() {
  loading.value = true
  errorMsg.value = ''
  try {
    dns.value = await call('wms.api.packing.get_packable_delivery_notes', {
      search: search.value || null,
    })
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load Delivery Notes'
  } finally {
    loading.value = false
  }
}

function openPacking(dn) {
  router.push({ name: 'PackingStation', params: { dnName: dn.name } })
}

// Display-only helper (styling, no business logic)
function packPct(dn) {
  const total = Number(dn.total_expected || 0)
  if (!total) return 0
  return Math.min(100, Math.round((Number(dn.total_packed || 0) / total) * 100))
}

onMounted(loadDNs)
</script>