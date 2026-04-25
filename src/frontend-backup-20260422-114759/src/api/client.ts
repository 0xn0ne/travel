import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 120000, // SSE needs long timeout
})

// Request interceptor: attach JWT if available
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor: handle 401 by clearing auth
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
    }
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  },
)

export default client
