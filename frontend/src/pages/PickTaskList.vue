<template>
  <div class="mx-auto max-w-md px-4 pb-10 pt-5 text-slate-900">
    <!-- Header -->
    <header class="mb-4">
      <h1 class="text-2xl font-bold tracking-tight">Pick Tasks</h1>
      <p class="mt-0.5 text-sm text-slate-500">
        Outbound picking for Draft Delivery Notes
      </p>
    </header>

    <!-- Navigation pill -->
    <div class="mb-5 flex flex-wrap items-center gap-2">
      <router-link
        :to="{ name: 'PendingPicks' }"
        class="inline-flex items-center gap-1.5 rounded-full border border-blue-100 bg-blue-50 px-3.5 py-1.5 text-sm font-medium text-blue-700 transition active:scale-95 active:bg-blue-100"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>
        Release New Orders
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </router-link>
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
          <div class="h-4 w-36 rounded bg-slate-200"></div>
          <div class="h-5 w-14 rounded-full bg-slate-100"></div>
        </div>
        <div class="mb-2 h-3 w-28 rounded bg-slate-100"></div>
        <div class="h-3 w-44 rounded bg-slate-100"></div>
      </div>
      <span class="sr-only">Loading…</span>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="tasks.length === 0"
      class="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center"
    >
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
      </span>
      <p class="font-semibold text-slate-800">No open pick tasks</p>
      <p class="mt-1 text-sm text-slate-500">New pick tasks will show up here.</p>
    </div>

    <!-- Task list -->
    <p v-if="!loading && !errorMsg && tasks.length" class="mb-3 text-sm text-slate-500">
      {{ tasks.length }} {{ tasks.length === 1 ? 'task' : 'tasks' }} to pick
    </p>

    <div
      v-for="task in tasks"
      :key="task.name"
      class="mb-3 cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition active:scale-[0.99] active:bg-slate-50"
      role="button"
      tabindex="0"
      @click="goToTask(task)"
      @keydown.enter="goToTask(task)"
    >
      <div class="flex items-stretch">
        <!-- Accent -->
        <div class="w-1.5 shrink-0 bg-emerald-500"></div>

        <div class="min-w-0 flex-1 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 break-words text-base font-semibold leading-snug">{{ task.item_code }}</div>
            <span class="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              Qty: {{ task.qty }}
            </span>
          </div>

          <div class="mt-3 flex items-center gap-2 text-sm text-slate-500">
            <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
            <span>From bin:</span>
            <span class="rounded-md bg-emerald-50 px-2 py-0.5 font-mono text-sm font-medium text-emerald-700">{{ task.source_bin || '—' }}</span>
          </div>
        </div>

        <div class="flex items-center pr-3 text-slate-300">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6" /></svg>
        </div>
      </div>

      <!-- Footer -->
      <div
        v-if="task.customer || task.delivery_note"
        class="space-y-1 border-t border-slate-100 bg-slate-50/60 px-4 py-2.5 pl-5 text-xs text-slate-500"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'

const router = useRouter()
const tasks = ref([])
const loading = ref(true)
const errorMsg = ref('')

async function loadTasks() {
  loading.value = true
  errorMsg.value = ''
  try {
    tasks.value = await call('wms.api.picking.get_pick_tasks')
  } catch (e) {
    errorMsg.value = e.message || 'Failed to load pick tasks'
  } finally {
    loading.value = false
  }
}

function goToTask(task) {
  router.push({ name: 'ConfirmPick', params: { taskName: task.name } })
}

onMounted(loadTasks)
</script>