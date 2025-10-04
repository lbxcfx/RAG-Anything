import request from './request'

export const graphApi = {
  getGraph(kbId: number, params?: any) {
    return request.get(`/graph/${kbId}`, { params })
  },

  getStats(kbId: number) {
    return request.get(`/graph/${kbId}/stats/`)
  },
}
