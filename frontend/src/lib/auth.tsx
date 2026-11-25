import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler, type Role, type User } from './api'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; first_name: string; last_name: string; role: Role }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => getToken() !== null)

  const clear = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(clear)
    if (!getToken()) return
    api
      .me()
      .then(setUser)
      .catch(clear)
      .finally(() => setLoading(false))
  }, [clear])

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      async login(email, password) {
        const { token, user } = await api.login(email, password)
        setToken(token)
        setUser(user)
      },
      async register(data) {
        const { token, user } = await api.register(data)
        setToken(token)
        setUser(user)
      },
      async logout() {
        await api.logout().catch(() => undefined)
        clear()
      },
    }),
    [user, loading, clear],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
