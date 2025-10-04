import request from './request'

export const knowledgeBaseApi = {
  list() {
    return request.get('/knowledge-bases/')
  },

  create(data: any) {
    return request.post('/knowledge-bases/', data)
  },

  get(id: number) {
    return request.get(`/knowledge-bases/${id}`)
  },

  update(id: number, data: any) {
    return request.put(`/knowledge-bases/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/knowledge-bases/${id}`)
  },
}
