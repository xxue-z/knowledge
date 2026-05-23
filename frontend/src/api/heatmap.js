import request from './request'

export const heatmapApi = {
  getHotQueries(timeRange = '24h', limit = 10) {
    return request.get('/api/heatmap/queries', { params: { time_range: timeRange, limit } })
  },

  getHotDocuments(timeRange = '24h', limit = 10) {
    return request.get('/api/heatmap/documents', { params: { time_range: timeRange, limit } })
  },

  getTimeline(date, granularity = 'hour') {
    return request.get('/api/heatmap/timeline', { params: { date, granularity } })
  },

  getNavigationHeat() {
    return request.get('/api/heatmap/navigation')
  }
}
