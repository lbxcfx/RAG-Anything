import request from './request'

export const modelsApi = {
  list(params?: any) {
    return request.get('/models/', { params })
  },

  create(data: any) {
    return request.post('/models/', data)
  },

  get(id: number) {
    return request.get(`/models/${id}`)
  },

  update(id: number, data: any) {
    return request.put(`/models/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/models/${id}`)
  },

  setDefault(id: number) {
    return request.post(`/models/${id}/default/`)
  },
}
