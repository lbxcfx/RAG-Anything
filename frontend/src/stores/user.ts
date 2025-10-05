import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    console.log('🔐 Starting login process for user:', username)
    try {
      const data = await authApi.login(username, password)
      console.log('✅ Login successful, token received')
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      console.log('💾 Token stored in localStorage')

      // Get user info
      await getUserInfo()
    } catch (error) {
      console.log('❌ Login failed:', error)
      throw error
    }
  }

  async function register(userData: any) {
    await authApi.register(userData)
  }

  async function getUserInfo() {
    console.log('👤 Getting user info...')
    try {
      const data = await authApi.getCurrentUser()
      console.log('✅ User info retrieved:', data.username)
      user.value = data
    } catch (error) {
      console.error('❌ Failed to get user info:', error)
      // 只有在明确是401错误时才登出
      if (error?.response?.status === 401) {
        console.log('🚪 401 error - logging out')
        logout()
      }
    }
  }

  function logout() {
    console.log('🚪 Logging out user')
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  async function checkAuth() {
    console.log('🔍 Checking authentication...')
    if (token.value) {
      console.log('🔑 Token found, checking user info')
      try {
        await getUserInfo()
      } catch (error) {
        console.error('❌ Auth check failed:', error)
        // 不自动登出，让用户手动重新登录
      }
    } else {
      console.log('⚠️ No token found')
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
