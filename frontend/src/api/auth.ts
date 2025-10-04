import request from './request'

export const authApi = {
  login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return request.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  register(data: any) {
    return request.post('/auth/register', data)
  },

  getCurrentUser() {
    return request.get('/users/me')
  },

  updateCurrentUser(data: any) {
    return request.put('/users/me', data)
  },
}
