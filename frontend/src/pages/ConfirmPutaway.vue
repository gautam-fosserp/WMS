<template>
  <div class="p-4 max-w-md mx-auto">
    <button class="text-blue-600 mb-4" @click="$router.back()">← Back</button>

    <div v-if="task" class="mb-6">
      <div class="text-lg font-semibold">{{ task.item_code }}</div>
      <div class="text-gray-600">Qty: {{ task.qty }}</div>
      <div class="mt-4 text-center">
        <div class="text-sm text-gray-500">Go to bin</div>
        <div class="text-3xl font-mono font-bold">{{ task.target_bin || 'Not assigned' }}</div>

        <div v-if="binInfo" class="mt-2">
          <span class="text-sm text-gray-500">
            Bin capacity:
            <span :class="willExceedCapacity ? 'text-red-500 font-semibold' : 'text-gray-700'">
              {{ binInfo.qty_in_bin }} / {{ binInfo.max_capacity || '∞' }}
            </span>
          </span>
          <div v-if="willExceedCapacity" class="text-red-500 text-sm mt-1">
            ⚠ Adding {{ task.qty }} will exceed capacity (room for {{ binInfo.remaining }} only)
          </div>
        </div>
      </div>
    </div>

    <div v-if="!task?.target_bin" class="text-red-500 text-center mb-4">
      This task has no bin assigned yet.
    </div>

    <div v-else>
      <!-- Camera scanner -->
      <div v-if="cameraActive" class="mb-4">
        <div id="scanner-region" class="rounded-lg overflow-hidden"></div>
        <button class="text-sm text-blue-600 mt-2" @click="stopCamera">
          Stop camera / enter manually
        </button>
      </div>

      <button v-else class="w-full bg-gray-100 text-gray-800 py-3 rounded-lg font-semibold mb-4" @click="startCamera">
        📷 Scan Bin Barcode
      </button>

      <!-- Manual entry fallback -->
      <div class="mb-4">
        <label class="block text-sm text-gray-500 mb-1">Enter/scan bin ID</label>
        <input v-model="scanResult" type="text" class="w-full border rounded-lg p-3 font-mono text-lg"
          placeholder="e.g. A1-R1-S1-B01" @keyup.enter="confirm" />
      </div>

      <div v-if="scanResult && scanResult !== task.target_bin" class="text-red-500 text-sm mb-4">
        ⚠ Wrong bin! Expected {{ task.target_bin }}
      </div>

      <button class="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold disabled:bg-gray-300"
        :disabled="scanResult !== task.target_bin || confirming || willExceedCapacity" @click="confirm">
        {{ confirming ? 'Confirming...' : 'Confirm Putaway' }}
      </button>
    </div>

    <div v-if="successMsg" class="mt-4 text-center text-green-600 font-semibold">
      {{ successMsg }}
    </div>

    <div class="mt-6 text-center">
      <button class="text-sm text-red-500 underline" @click="showExceptionForm = true">
        ⚠ Can't complete this task? Report an issue
      </button>
    </div>

    <div v-if="showExceptionForm" class="mt-4 border rounded-lg p-4 bg-gray-50">
      <label class="block text-sm text-gray-600 mb-1">What's wrong?</label>
      <select v-model="exceptionReason" class="w-full border rounded-lg p-2 mb-3">
        <option disabled value="">Select a reason</option>
        <option>Bin Full</option>
        <option>Bin Damaged or Missing</option>
        <option>Wrong Item on Task</option>
        <option>Item Damaged</option>
        <option>Other</option>
      </select>

      <textarea v-model="exceptionNotes" class="w-full border rounded-lg p-2 mb-3" rows="2"
        placeholder="Optional notes"></textarea>

      <div class="flex gap-2">
        <button class="flex-1 bg-gray-200 py-2 rounded-lg" @click="showExceptionForm = false">
          Cancel
        </button>
        <button class="flex-1 bg-red-500 text-white py-2 rounded-lg disabled:bg-gray-300"
          :disabled="!exceptionReason || reportingException" @click="submitException">
          {{ reportingException ? 'Submitting...' : 'Submit' }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { Html5Qrcode } from 'html5-qrcode'

const route = useRoute()
const router = useRouter()

const task = ref(null)
const binInfo = ref(null)
const scanResult = ref('')
const confirming = ref(false)
const successMsg = ref('')
const cameraActive = ref(false)
const showExceptionForm = ref(false)
const exceptionReason = ref('')
const exceptionNotes = ref('')
const reportingException = ref(false)

let scanner = null

const willExceedCapacity = computed(() => {
  if (!binInfo.value || binInfo.value.remaining === null || binInfo.value.remaining === undefined) return false
  return task.value.qty > binInfo.value.remaining
})

async function loadTask() {
  const tasks = await call('wms.api.api.get_pending_tasks')
  task.value = tasks.find(t => t.name === route.params.taskName)

  if (task.value?.target_bin) {
    binInfo.value = await call('wms.api.putaway.get_bin_capacity_info', {
      bin_name: task.value.target_bin,
    })
  }
}

async function startCamera() {
  cameraActive.value = true
  // Wait for the DOM element to render before initializing
  await new Promise(resolve => setTimeout(resolve, 50))

  scanner = new Html5Qrcode('scanner-region')
  try {
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      (decodedText) => {
        scanResult.value = decodedText
        stopCamera() // auto-stop once a code is read
      },
      () => { } // ignore per-frame scan misses, not real errors
    )
  } catch (err) {
    console.error('Camera start failed:', err)
    alert('Could not access camera. You can enter the bin ID manually instead.')
    cameraActive.value = false
  }
}

async function stopCamera() {
  if (scanner) {
    try {
      await scanner.stop()
      await scanner.clear()
    } catch (e) {
      // scanner may already be stopped, safe to ignore
    }
  }
  cameraActive.value = false
}

async function confirm() {
  if (scanResult.value !== task.value.target_bin) return
  if (willExceedCapacity.value) return
  confirming.value = true
  try {
    const res = await call('wms.api.putaway.confirm_putaway', {
      task_name: task.value.name,
      scanned_bin_id: scanResult.value,
    })
    successMsg.value = res.message
    setTimeout(() => router.push({ name: 'TaskList' }), 1200)
  } catch (e) {
    alert(e.message || 'Failed to confirm putaway')
  } finally {
    confirming.value = false
  }
}

onMounted(loadTask)

onBeforeUnmount(() => {
  if (cameraActive.value) stopCamera()
})

async function submitException() {
  reportingException.value = true
  try {
    const res = await call('wms.api.putaway.report_exception', {
      task_name: task.value.name,
      exception_reason: exceptionReason.value,
      exception_notes: exceptionNotes.value,
    })
    successMsg.value = res.message
    setTimeout(() => router.push({ name: 'TaskList' }), 1500)
  } catch (e) {
    alert(e.message || 'Failed to report issue')
  } finally {
    reportingException.value = false
  }
}
</script>