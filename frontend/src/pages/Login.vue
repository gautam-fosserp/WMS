<template>
  <div class="mx-auto max-w-md px-6 pt-20 text-slate-900">
    <div class="mb-10 flex flex-col items-center">
      <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-lg">
        <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5" /></svg>
      </div>
      <h1 class="text-2xl font-bold tracking-tight">
        {{ mode === 'login' ? 'WMS Login' : 'Reset password' }}
      </h1>
      <p class="mt-1 text-center text-sm text-slate-500">
        {{ mode === 'login'
          ? 'Sign in to access your warehouse'
          : 'Enter your email and we will send you a reset link' }}
      </p>
    </div>

    <!-- Login -->
    <form v-if="mode === 'login'" @submit.prevent="submit" class="space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Email</label>
        <input
          v-model="email"
          type="text"
          autocomplete="username"
          class="w-full rounded-xl border border-slate-300 bg-white p-3 text-base focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          placeholder="jane@example.com"
          required
        />
      </div>

      <div>
        <div class="mb-1 flex items-center justify-between">
          <label class="block text-sm font-medium text-slate-700">Password</label>
          <button
            type="button"
            class="text-sm font-medium text-blue-600 active:text-blue-700"
            @click="switchMode('forgot')"
          >
            Forgot password?
          </button>
        </div>
        <div class="relative">
        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          class="w-full rounded-xl border border-slate-300 bg-white p-3 pr-12 text-base focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          placeholder="••••••••"
          required
        />
          <button
            type="button"
            class="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-500 active:text-slate-700"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            :aria-pressed="showPassword"
            @click="showPassword = !showPassword"
          >
            <svg v-if="!showPassword" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg v-else class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.94 10.94 0 0112 19c-7 0-11-7-11-7a19.8 19.8 0 015.06-5.94M9.9 4.24A10.9 10.9 0 0112 4c7 0 11 7 11 7a19.7 19.7 0 01-3.17 4.19M14.12 14.12a3 3 0 11-4.24-4.24M1 1l22 22" />
            </svg>
          </button>
        </div>
      </div>

      <div v-if="errorMsg" class="rounded-lg bg-red-50 p-3 text-sm text-red-600" role="alert">
        {{ errorMsg }}
      </div>

      <button
        type="submit"
        class="w-full rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300"
        :disabled="loading"
      >
        {{ loading ? 'Logging in…' : 'Log In' }}
      </button>

      <!-- Social login (Google etc.), shown only if enabled in Social Login Key -->
      <template v-if="socialLogins.length">
        <div class="flex items-center gap-3 text-sm text-slate-400">
          <span class="h-px flex-1 bg-slate-200"></span>
          or
          <span class="h-px flex-1 bg-slate-200"></span>
        </div>
        <button
          v-for="p in socialLogins"
          :key="p.name"
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white py-3.5 text-base font-semibold text-slate-700 transition active:bg-slate-50"
          @click="socialLogin(p)"
        >
          <svg v-if="p.provider_name === 'Google'" class="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5a5.6 5.6 0 01-2.4 3.7v3h3.9c2.3-2.1 3.5-5.2 3.5-8.9z" />
            <path fill="#34A853" d="M12 24c3.2 0 6-1.1 7.9-2.9l-3.9-3c-1.1.7-2.5 1.2-4 1.2-3.1 0-5.7-2.1-6.6-4.9H1.4v3.1A12 12 0 0012 24z" />
            <path fill="#FBBC05" d="M5.4 14.4a7.2 7.2 0 010-4.8V6.5H1.4a12 12 0 000 11l4-3.1z" />
            <path fill="#EA4335" d="M12 4.8c1.8 0 3.3.6 4.6 1.8l3.4-3.4A12 12 0 001.4 6.5l4 3.1C6.3 6.9 8.9 4.8 12 4.8z" />
          </svg>
          Login with {{ p.provider_name }}
        </button>
      </template>
    </form>

    <!-- Forgot password -->
    <form v-else @submit.prevent="submitReset" class="space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Email</label>
        <input
          v-model="email"
          type="text"
          autocomplete="username"
          class="w-full rounded-xl border border-slate-300 bg-white p-3 text-base focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          placeholder="jane@example.com"
          required
          :disabled="resetSent"
        />
      </div>

      <div v-if="errorMsg" class="rounded-lg bg-red-50 p-3 text-sm text-red-600" role="alert">
        {{ errorMsg }}
      </div>

      <div v-if="resetSent" class="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700" role="status">
        Reset instructions have been sent to your email. Open the link in the email to set a new password.
      </div>

      <button
        v-if="!resetSent"
        type="submit"
        class="w-full rounded-xl bg-blue-600 py-3.5 text-base font-semibold text-white shadow-sm transition active:scale-[0.99] active:bg-blue-700 disabled:bg-slate-300"
        :disabled="loading"
      >
        {{ loading ? 'Sending…' : 'Send reset link' }}
      </button>

      <button
        type="button"
        class="w-full rounded-xl border border-slate-300 bg-white py-3.5 text-base font-semibold text-slate-700 transition active:bg-slate-50"
        @click="switchMode('login')"
      >
        Back to login
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const socialLogins = ref([])

onMounted(async () => {
  try {
    const res = await fetch('/api/method/wms.api.auth.get_social_logins')
    if (res.ok) socialLogins.value = (await res.json()).message || []
  } catch (e) {
    // No social login buttons if this fails; email/password still works
  }
})

function socialLogin(provider) {
  window.location.href = provider.auth_url
}

const mode = ref('login') // 'login' | 'forgot'
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const resetSent = ref(false)
const showPassword = ref(false)

function switchMode(next) {
  mode.value = next
  errorMsg.value = ''
  resetSent.value = false
  password.value = ''
  showPassword.value = false
}

async function submit() {
  loading.value = true
  errorMsg.value = ''

  try {
    const response = await fetch('/api/method/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token,
      },
      body: JSON.stringify({
        usr: email.value,
        pwd: password.value,
      }),
    })

    const data = await response.json()

    if (response.ok) {
      // Success! Reload the page to load the Dashboard
      window.location.href = '/wms-mobile/'
    } else {
      errorMsg.value = data.message || 'Invalid login credentials'
    }
  } catch (e) {
    errorMsg.value = 'Network error. Please try again.'
  } finally {
    loading.value = false
  }
}

async function submitReset() {
  loading.value = true
  errorMsg.value = ''

  try {
    const response = await fetch('/api/method/frappe.core.doctype.user.user.reset_password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token,
      },
      body: JSON.stringify({ user: email.value.trim() }),
    })

    const data = await response.json().catch(() => ({}))

    if (response.ok && data.message !== 'not found') {
      resetSent.value = true
    } else if (data.message === 'not found') {
      errorMsg.value = 'No account found with this email.'
    } else {
      errorMsg.value = 'Could not send the reset link. Please try again.'
    }
  } catch (e) {
    errorMsg.value = 'Network error. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>