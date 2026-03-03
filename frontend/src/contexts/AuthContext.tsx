import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { api } from '../lib/api'

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface User {
  id: string
  display_name: string | null
  email: string | null
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('spotify_token')
  )
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = useCallback(async (accessToken: string) => {
    try {
      const { data } = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      setUser(data)
    } catch {
      setUser(null)
      localStorage.removeItem('spotify_token')
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      localStorage.setItem('spotify_token', urlToken)
      setToken(urlToken)
      fetchUser(urlToken).finally(() => setIsLoading(false))
      window.history.replaceState({}, '', window.location.pathname)
    } else if (token) {
      fetchUser(token).finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [token, fetchUser])

  const login = () => {
    window.location.href = `${API_BASE}/auth/login`
  }

  const logout = () => {
    localStorage.removeItem('spotify_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
