<template>
  <div v-if="visible">
    <!-- Spacer so page content is never hidden behind the bar -->
    <div class="h-24" aria-hidden="true"></div>

    <!-- More sheet -->
    <div
      v-if="moreOpen"
      class="fixed inset-0 z-40 bg-slate-900/40"
      @click="moreOpen = false"
    ></div>
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-full"
      enter-to-class="translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0"
      leave-to-class="translate-y-full"
    >
      <div
        v-if="moreOpen"
        class="fixed inset-x-0 bottom-0 z-40 mx-auto max-w-md rounded-t-3xl bg-white px-4 pb-24 pt-3 shadow-2xl"
        role="dialog"
        aria-label="More"
      >
        <div class="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-300"></div>
        <div class="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">More</div>
        <div class="space-y-1">
          <router-link
            v-for="item in moreItems"
            :key="item.label"
            :to="{ name: item.route }"
            class="flex items-center gap-3 rounded-xl px-2 py-2.5 no-underline transition hover:no-underline focus:no-underline active:bg-slate-100"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="item.color">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path v-for="p in item.paths" :key="p" :d="p" />
              </svg>
            </span>
            <span class="min-w-0 flex-1">
              <span class="block font-medium leading-tight" :class="item.text">{{ item.label }}</span>
              <span class="block text-xs text-slate-500">{{ item.hint }}</span>
            </span>
            <svg class="h-5 w-5 shrink-0 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6" /></svg>
          </router-link>
        </div>
      </div>
    </transition>

    <!-- Bar -->
    <nav
      class="fixed inset-x-0 bottom-0 z-50 border-t border-slate-200 bg-white/95 backdrop-blur"
      style="padding-bottom: env(safe-area-inset-bottom)"
      aria-label="Main navigation"
    >
      <div class="mx-auto flex max-w-md items-stretch justify-between px-2">
        <router-link
          v-for="tab in tabs"
          :key="tab.label"
          :to="{ name: tab.route }"
          class="flex flex-1 flex-col items-center gap-0.5 py-2 no-underline transition hover:no-underline focus:no-underline active:opacity-60"
          :class="activeTab === tab.label ? 'text-blue-600' : 'text-slate-500'"
          :aria-current="activeTab === tab.label ? 'page' : null"
        >
          <span
            class="flex h-8 w-14 items-center justify-center rounded-full transition"
            :class="activeTab === tab.label ? 'bg-blue-50' : ''"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path v-for="p in tab.paths" :key="p" :d="p" />
            </svg>
          </span>
          <span class="text-[11px] font-medium leading-none">{{ tab.label }}</span>
        </router-link>

        <!-- More -->
        <button
          class="flex flex-1 flex-col items-center gap-0.5 py-2 transition active:opacity-60"
          :class="moreOpen || activeTab === 'More' ? 'text-blue-600' : 'text-slate-500'"
          :aria-expanded="moreOpen"
          @click="moreOpen = !moreOpen"
        >
          <span
            class="flex h-8 w-14 items-center justify-center rounded-full transition"
            :class="moreOpen || activeTab === 'More' ? 'bg-blue-50' : ''"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="5" cy="12" r="1.8" />
              <circle cx="12" cy="12" r="1.8" />
              <circle cx="19" cy="12" r="1.8" />
            </svg>
          </span>
          <span class="text-[11px] font-medium leading-none">More</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'

const route = useRoute()

const moreOpen = ref(false)
const isSupervisor = ref(false)
const receivingMode = ref('Standard ERPNext Only')

// Focused task screens hide the bar so it never competes with scanning
// or with a screen's own primary action button.
const hiddenOn = ['ConfirmPick', 'ConfirmPutaway', 'PackingStation', 'ReceivingForm']
const visible = computed(() => !hiddenOn.includes(route.name))

const tabs = [
  {
    label: 'Home',
    route: 'Dashboard',
    routes: ['Dashboard'],
    paths: ['M3 11l9-8 9 8', 'M5 10v10h14V10', 'M10 20v-6h4v6'],
  },
  {
    label: 'Putaway',
    route: 'TaskList',
    routes: ['TaskList', 'ConfirmPutaway'],
    paths: ['M12 3l9 5-9 5-9-5 9-5z', 'M3 13l9 5 9-5'],
  },
  {
    label: 'Picks',
    route: 'PickTaskList',
    routes: ['PickTaskList', 'PendingPicks', 'ConfirmPick'],
    paths: ['M9 11l3 3 8-8', 'M20 12v6a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h9'],
  },
  {
    label: 'Packing',
    route: 'PackingList',
    routes: ['PackingList', 'PackingStation'],
    paths: ['M3 10a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2v-8z', 'M3 12h18', 'M8 8V4h8v4'],
  },
]

const moreRoutes = ['BinList', 'BinDetail', 'ReceivingList', 'ReceivingForm', 'CompletedPutaways', 'ExceptionsList']

const activeTab = computed(() => {
  // While the More sheet is open, only More is highlighted
  if (moreOpen.value) return 'More'
  const name = route.name
  const tab = tabs.find(t => t.routes.includes(name))
  if (tab) return tab.label
  if (moreRoutes.includes(name)) return 'More'
  return null
})

const moreItems = computed(() => {
  const items = []
  if (receivingMode.value !== 'Standard ERPNext Only') {
    items.push({
      label: 'Receive',
      hint: 'Receive stock',
      route: 'ReceivingList',
      color: 'bg-blue-50 text-blue-600',
      text: 'text-slate-900',
      paths: ['M12 3v12', 'M8 11l4 4 4-4', 'M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2'],
    })
  }
  items.push({
    label: 'Bins',
    hint: 'Browse bins',
    route: 'BinList',
    color: 'bg-sky-50 text-sky-600',
    text: 'text-slate-900',
    paths: ['M21 8l-9-5-9 5v8l9 5 9-5V8z', 'M3.3 7.5L12 12.5l8.7-5M12 22V12.5'],
  })
  if (isSupervisor.value) {
    items.push(
      {
        label: 'History',
        hint: 'Completed putaways',
        route: 'CompletedPutaways',
        color: 'bg-slate-100 text-slate-600',
        text: 'text-slate-900',
        paths: ['M12 7v5l3 2', 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z'],
      },
      {
        label: 'Exceptions',
        hint: 'Issues needing attention',
        route: 'ExceptionsList',
        color: 'bg-red-100 text-red-600',
        text: 'text-red-700',
        paths: ['M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z', 'M12 9v4M12 17h.01'],
      },
    )
  }
  return items
})

// Close the sheet whenever the user navigates
watch(() => route.name, () => { moreOpen.value = false })

async function loadUserInfo() {
  try {
    const info = await call('wms.api.api.get_current_user_info')
    isSupervisor.value = info.is_supervisor
  } catch (e) {
    console.error('BottomNav loadUserInfo error:', e)
  }
}

async function loadReceivingMode() {
  try {
    const cfg = await call('wms.api.receiving.get_receiving_config')
    receivingMode.value = cfg.receiving_mode || 'Standard ERPNext Only'
  } catch (e) {
    console.error('BottomNav loadReceivingMode error:', e)
  }
}

onMounted(() => {
  loadUserInfo()
  loadReceivingMode()
})
</script>