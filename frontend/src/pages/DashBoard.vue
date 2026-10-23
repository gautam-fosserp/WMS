<template>
  <div class="mx-auto max-w-md pb-10 text-slate-900">
    <!-- Sticky header -->
    <header class="sticky top-0 z-30 bg-slate-50/95 backdrop-blur-sm">
      <div class="relative flex items-center justify-between gap-3 px-4 pb-3 pt-6">
        <div class="min-w-0">
          <h1 class="truncate text-2xl font-bold tracking-tight">Warehouse</h1>
          <p class="mt-0.5 truncate text-sm text-slate-500">What would you like to do?</p>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <!-- Notifications -->
          <button
            class="relative flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition active:scale-95 active:bg-slate-50"
            aria-label="Notifications" @click="togglePanel('notif')">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9" />
              <path d="M10.3 21a1.9 1.9 0 003.4 0" />
            </svg>
            <span v-if="notifCount > 0"
              class="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-bold leading-none text-white ring-2 ring-slate-50">{{
                notifCount > 9 ? '9+' : notifCount }}</span>
          </button>

          <!-- Profile -->
          <button
            class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-blue-600 text-sm font-semibold text-white shadow-sm transition active:scale-95"
            aria-label="Profile" @click="togglePanel('profile')">
            <img v-if="user.image" :src="user.image" alt="" class="h-full w-full object-cover" />
            <span v-else>{{ initials }}</span>
          </button>
        </div>

        <!-- Click-away layer -->
        <div v-if="openPanel" class="fixed inset-0 z-10" @click="openPanel = null"></div>

        <!-- Notifications panel -->
        <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="-translate-y-1 opacity-0"
          enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-100 ease-in"
          leave-from-class="translate-y-0 opacity-100" leave-to-class="-translate-y-1 opacity-0">
          <div v-if="openPanel === 'notif'"
            class="absolute right-4 top-[calc(100%-8px)] z-20 w-72 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
            <div class="border-b border-slate-100 px-4 py-3 text-sm font-semibold">Notifications</div>

            <div v-if="notifItems.length === 0" class="flex flex-col items-center px-4 py-8 text-center">
              <span
                class="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 13l4 4L19 7" />
                </svg>
              </span>
              <p class="text-sm font-medium text-slate-700">You're all caught up</p>
            </div>

            <router-link v-for="n in notifItems" :key="n.label" :to="{ name: n.route }"
              class="flex items-center gap-3 border-b border-slate-100 px-4 py-3 transition last:border-b-0 active:bg-slate-50"
              @click="openPanel = null">
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" :class="n.color">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path v-for="p in n.paths" :key="p" :d="p" />
                </svg>
              </span>
              <span class="min-w-0 flex-1 text-sm text-slate-800">{{ n.label }}</span>
              <svg class="h-4 w-4 shrink-0 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </router-link>
          </div>
        </Transition>

        <!-- Profile panel -->
        <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="-translate-y-1 opacity-0"
          enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-100 ease-in"
          leave-from-class="translate-y-0 opacity-100" leave-to-class="-translate-y-1 opacity-0">
          <div v-if="openPanel === 'profile'"
            class="absolute right-4 top-[calc(100%-8px)] z-20 w-64 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
            <div class="flex items-center gap-3 border-b border-slate-100 px-4 py-4">
              <span
                class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-blue-600 text-sm font-semibold text-white">
                <img v-if="user.image" :src="user.image" alt="" class="h-full w-full object-cover" />
                <span v-else>{{ initials }}</span>
              </span>
              <div class="min-w-0">
                <div class="truncate text-sm font-semibold">{{ user.name || 'User' }}</div>
                <div class="mt-0.5 text-xs text-slate-500">{{ isSupervisor ? 'Supervisor' : 'Operator' }}</div>
              </div>
            </div>
            <button
              class="flex w-full items-center gap-3 px-4 py-3 text-sm font-medium text-red-600 transition active:bg-red-50 disabled:text-slate-400"
              :disabled="loggingOut" @click="logout">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <path d="M16 17l5-5-5-5M21 12H9" />
              </svg>
              {{ loggingOut ? 'Logging out…' : 'Log out' }}
            </button>
          </div>
        </Transition>
      </div>
    </header>

    <!-- Scrollable content -->
    <div class="px-4">
      <!-- Load error with retry -->
      <div v-if="loadError" class="mb-4 flex items-center gap-3 rounded-2xl border border-red-100 bg-red-50 px-4 py-3"
        role="alert">
        <span class="min-w-0 flex-1 text-sm text-red-700">{{ loadError }}</span>
        <button class="shrink-0 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white active:bg-red-700"
          @click="loadAll()">Retry</button>
      </div>

      <!-- Putaway hero -->
      <router-link :to="{ name: 'TaskList' }"
        class="mb-6 flex items-center gap-4 rounded-2xl bg-slate-900 p-5 text-white shadow-md transition active:scale-[0.99]">
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/10">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l9 5-9 5-9-5 9-5z" />
            <path d="M3 13l9 5 9-5" />
          </svg>
        </span>
        <div class="min-w-0 flex-1">
          <div class="text-lg font-semibold leading-tight">Putaway</div>
          <div class="mt-0.5 text-sm text-slate-300">
            <template v-if="pendingCount === null">Open putaway tasks</template>
            <template v-else-if="pendingCount === 0">All caught up</template>
            <template v-else>{{ pendingCount }} {{ pendingCount === 1 ? 'task' : 'tasks' }} waiting</template>
          </div>
        </div>
        <span v-if="pendingCount" class="shrink-0 rounded-full bg-blue-500 px-3 py-1 text-sm font-bold">{{ pendingCount
          }}</span>
        <svg class="h-5 w-5 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 6l6 6-6 6" />
        </svg>
      </router-link>

      <!-- Operations — 2-column tile grid, gated to avoid flash -->
      <template v-if="receivingModeLoaded">
        <h2 class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Operations</h2>
        <nav class="mb-6 grid grid-cols-2 gap-3">
          <router-link v-for="tile in operations" :key="tile.label" :to="{ name: tile.route }"
            class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition active:scale-[0.98] active:bg-slate-50">
            <span class="flex h-11 w-11 items-center justify-center rounded-xl" :class="tile.color">
              <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path v-for="p in tile.paths" :key="p" :d="p" />
              </svg>
            </span>
            <div>
              <div class="font-semibold leading-tight">{{ tile.label }}</div>
              <div class="mt-0.5 text-xs text-slate-500">{{ tile.hint }}</div>
            </div>
          </router-link>
        </nav>
      </template>

      <!-- Supervisor — also gated so both sections appear together, no positional shift -->
      <template v-if="receivingModeLoaded && isSupervisor">
        <h2 class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Supervisor</h2>
        <nav class="grid grid-cols-2 gap-3">
          <router-link v-for="tile in supervisorTiles" :key="tile.label" :to="{ name: tile.route }"
            class="flex items-center gap-3 rounded-2xl border px-3 py-3 shadow-sm transition active:scale-[0.98]"
            :class="tile.card">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="tile.color">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path v-for="p in tile.paths" :key="p" :d="p" />
              </svg>
            </span>
            <span class="min-w-0 truncate text-sm font-semibold" :class="tile.text">{{ tile.label }}</span>
          </router-link>
        </nav>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { call } from 'frappe-ui'

const isSupervisor = ref(false)
const receivingMode = ref('Standard ERPNext Only')
const receivingModeLoaded = ref(false)
const pendingCount = ref(null)
const exceptionCount = ref(0)
const openPanel = ref(null)
const loggingOut = ref(false)
const user = ref({ name: '', image: '' })
const loadError = ref('')

function togglePanel(name) {
  openPanel.value = openPanel.value === name ? null : name
}

const initials = computed(() => {
  const parts = (user.value.name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  const first = parts[0].charAt(0)
  const last = parts.length > 1 ? parts[parts.length - 1].charAt(0) : ''
  return (first + last).toUpperCase()
})

const notifItems = computed(() => {
  const items = []
  if (pendingCount.value) {
    items.push({
      label: `${pendingCount.value} putaway ${pendingCount.value === 1 ? 'task' : 'tasks'} waiting`,
      route: 'TaskList',
      color: 'bg-blue-50 text-blue-600',
      paths: ['M12 3l9 5-9 5-9-5 9-5z', 'M3 13l9 5 9-5'],
    })
  }
  if (isSupervisor.value && exceptionCount.value) {
    items.push({
      label: `${exceptionCount.value} ${exceptionCount.value === 1 ? 'exception needs' : 'exceptions need'} attention`,
      route: 'ExceptionsList',
      color: 'bg-red-50 text-red-600',
      paths: ['M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z', 'M12 9v4M12 17h.01'],
    })
  }
  return items
})

const notifCount = computed(
  () => (pendingCount.value || 0) + (isSupervisor.value ? exceptionCount.value : 0)
)

const operations = computed(() => {
  const tiles = []
  if (receivingMode.value !== 'Standard ERPNext Only') {
    tiles.push({
      label: 'Receive',
      hint: 'Receive stock',
      route: 'ReceivingList',
      color: 'bg-blue-50 text-blue-600',
      paths: ['M12 3v12', 'M8 11l4 4 4-4', 'M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2'],
    })
  }
  tiles.push(
    {
      label: 'Bins',
      hint: 'Browse bins',
      route: 'BinList',
      color: 'bg-sky-50 text-sky-600',
      paths: ['M21 8l-9-5-9 5v8l9 5 9-5V8z', 'M3.3 7.5L12 12.5l8.7-5M12 22V12.5'],
    },
    {
      label: 'Picks',
      hint: 'Outbound picks',
      route: 'PickTaskList',
      color: 'bg-emerald-50 text-emerald-600',
      paths: ['M9 11l3 3 8-8', 'M20 12v6a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h9'],
    },
    {
      label: 'Packing',
      hint: 'Pack deliveries',
      route: 'PackingList',
      color: 'bg-violet-50 text-violet-600',
      paths: ['M3 10a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2v-8z', 'M3 12h18', 'M8 8V4h8v4'],
    },
  )
  return tiles
})

const supervisorTiles = [
  {
    label: 'History',
    hint: 'Completed putaways',
    route: 'CompletedPutaways',
    card: 'border-slate-200 bg-white active:bg-slate-50',
    color: 'bg-slate-100 text-slate-600',
    text: '',
    paths: ['M12 7v5l3 2', 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z'],
  },
  {
    label: 'Exceptions',
    hint: 'Issues needing attention',
    route: 'ExceptionsList',
    card: 'border-red-100 bg-red-50/60 active:bg-red-50',
    color: 'bg-red-100 text-red-600',
    text: 'text-red-700',
    paths: ['M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z', 'M12 9v4M12 17h.01'],
  },
]

async function loadAll(silent = false) {
  if (!silent) loadError.value = ''
  try {
    const s = await call('wms.api.home.get_home_summary')
    const info = s.user || {}
    isSupervisor.value = !!info.is_supervisor
    user.value = {
      name: info.full_name || info.user_name || info.user || info.name || '',
      image: info.user_image || info.image || '',
    }
    receivingMode.value = s.receiving_mode || 'Standard ERPNext Only'
    pendingCount.value = s.pending_count
    exceptionCount.value = s.exception_count || 0
    loadError.value = ''
  } catch (e) {
    // Check if the error is due to the user not being logged in or session expired.
    const isAuthError =
      e.httpStatus === 403 ||
      e.httpStatus === 401 ||
      (e.message && (
        e.message.includes('PermissionError') ||
        e.message.includes('403') ||
        e.message.includes('Forbidden') ||
        e.message.includes('Unauthorized') ||
        e.message.includes('Login to access')
      )) ||
      (e.message && (e.message.includes('JSON') || e.message.includes('Unexpected token')));

    if (isAuthError) {
      // Silently redirect to the custom Vue Login page without logging an error
      window.location.href = '/wms-mobile/login';
      return;
    }

    // Only log to console if it's a real network/server error, not an auth redirect
    console.error('loadAll error:', e)
    if (!silent) loadError.value = 'Could not load the dashboard.'
  } finally {
    receivingModeLoaded.value = true
  }
}

async function logout() {
  loggingOut.value = true
  try {
    await call('logout')
  } catch (e) {
    console.error('logout error:', e)
  } finally {
    // replace() keeps the protected page out of the back-button history
    window.location.replace('/wms-mobile/login')
  }
}

let timer = null

function refreshIfVisible() {
  if (document.visibilityState === 'visible') loadAll(true)
}

onMounted(() => {
  loadAll()
  timer = setInterval(refreshIfVisible, 60000)
  document.addEventListener('visibilitychange', refreshIfVisible)
})

onUnmounted(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', refreshIfVisible)
})
</script>