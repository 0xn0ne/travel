import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<{ id: string; email: string } | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const response = await client.post('/auth/login', { email, password })
    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem('auth_token', response.data.access_token)
    return response.data
  }

  async function register(email: string, password: string) {
    const response = await client.post('/auth/register', { email, password })
    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem('auth_token', response.data.access_token)
    return response.data
  }

  async function fetchUser() {
    if (!token.value) return null
    try {
      const response = await client.get('/auth/me')
      user.value = response.data
      return response.data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  // Initialize: fetch user if token exists
  if (token.value) {
    fetchUser()
  }

  return { token, user, isAuthenticated, login, register, logout, fetchUser }
})
