import axios, { AxiosInstance } from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Unknown error occurred'
    return Promise.reject(new Error(message))
  },
)

export default client
