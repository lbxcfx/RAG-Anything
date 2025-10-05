import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
      console.log(`🔑 Token attached: ${userStore.token.substring(0, 20)}...`)
    } else {
      console.log('⚠️ No token available')
    }
    return config
  },
  (error) => {
    console.log('❌ Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`✅ API Success: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
    return response.data
  },
  (error) => {
    console.log(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response?.status}`)
    console.log('Error details:', error.response?.data)
    console.log('Error config:', error.config)
    
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 只有在登录相关的API调用失败时才自动登出
          const url = error.config?.url || ''
          console.log(`🔐 401 Error on URL: ${url}`)
          if (url.includes('/auth/login') || url.includes('/users/me')) {
            console.log('🚪 Auto logout triggered - login related API failed')
            ElMessage.error('未授权,请重新登录')
            const userStore = useUserStore()
            userStore.logout()
            router.push('/login')
          } else {
            console.log('⚠️ 401 Error on non-login API - not auto logging out')
            ElMessage.error('认证失败，请检查登录状态')
          }
          break
        case 403:
          console.log('🚫 403 Forbidden')
          ElMessage.error('权限不足')
          break
        case 404:
          console.log('🔍 404 Not Found')
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          console.log('💥 500 Server Error')
          ElMessage.error(data.detail || '服务器错误')
          break
        default:
          console.log(`⚠️ ${status} Error`)
          ElMessage.error(data.detail || data.message || '请求失败')
      }
    } else {
      console.log('🌐 Network Error')
      ElMessage.error('网络错误,请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default request
