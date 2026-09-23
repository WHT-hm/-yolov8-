import request from './request'

export function listDetections(params) {
  return request.get('/detections', { params })
}

export function getDetection(id) {
  return request.get(`/detections/${id}`)
}

export function createDetection(formData) {
  return request.post('/detections', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteDetection(id) {
  return request.delete(`/detections/${id}`)
}

export function getMetaOptions() {
  return request.get('/meta/pest-types')
}
