import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)

    // Get user info
    await getUserInfo()
  }

  async function register(userData: any) {
    await authApi.register(userData)
  }

  async function getUserInfo() {
    try {
      const data = await authApi.getCurrentUser()
      user.value = data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  async function checkAuth() {
    if (token.value) {
      await getUserInfo()
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    getUserInfo,
    checkAuth,
  }
})
