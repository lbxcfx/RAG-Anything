import request from './request'

export const queryApi = {
  query(kbId: number | null, data: any) {
    const url = kbId ? `/query/${kbId}/` : '/query/'
    return request.post(url, data)
  },

  createSession(kbId?: number) {
    const url = kbId ? `/query/${kbId}/sessions/` : '/query/sessions/'
    return request.post(url)
  },

  getSessions(params?: any) {
    return request.get('/query/sessions/', { params })
  },

  getSession(sessionId: number) {
    return request.get(`/query/sessions/${sessionId}`)
  },
}
