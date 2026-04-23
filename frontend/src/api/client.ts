import axios, { AxiosInstance } from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'
const API_KEY = import.meta.env.VITE_API_KEY || ''

const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

if (API_KEY) {
  client.defaults.headers.common['X-API-Key'] = API_KEY
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Unknown error occurred'
    return Promise.reject(new Error(message))
  },
)

export default client
export { API_KEY }
