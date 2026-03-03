import axios, { type InternalAxiosRequestConfig } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'
const BACKEND_BASE = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('spotify_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

async function doRefresh(): Promise<string | null> {
  const refreshToken = localStorage.getItem('spotify_refresh_token')
  if (!refreshToken) return null
  try {
    const { data } = await axios.post(`${BACKEND_BASE}/auth/refresh`, {
      refresh_token: refreshToken,
    })
    const newToken = data.access_token
    const newRefresh = data.refresh_token ?? refreshToken
    localStorage.setItem('spotify_token', newToken)
    if (newRefresh) localStorage.setItem('spotify_refresh_token', newRefresh)
    return newToken
  } catch {
    localStorage.removeItem('spotify_token')
    localStorage.removeItem('spotify_refresh_token')
    return null
  }
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (err.response?.status === 401 && !originalRequest._retry) {
      if (!refreshPromise) {
        refreshPromise = doRefresh().finally(() => {
          refreshPromise = null
        })
      }
      const newToken = await refreshPromise
      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      }
    }

    return Promise.reject(err)
  }
)
