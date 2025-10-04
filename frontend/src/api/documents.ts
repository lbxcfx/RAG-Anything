import request from './request'

export const documentsApi = {
  list(params?: any) {
    return request.get('/documents/', { params })
  },

  upload(kbId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/documents/upload?knowledge_base_id=${kbId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  get(id: number) {
    return request.get(`/documents/${id}`)
  },

  delete(id: number) {
    return request.delete(`/documents/${id}`)
  },
}
