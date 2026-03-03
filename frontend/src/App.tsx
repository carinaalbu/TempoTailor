import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { LandingPage } from '@/pages/LandingPage'
import { CreatePage } from '@/pages/CreatePage'
import { ResultPage } from '@/pages/ResultPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { DraftDetailPage } from '@/pages/DraftDetailPage'
import { PublishPage } from '@/pages/PublishPage'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, login, logout } = useAuth()
  const location = useLocation()
  const isLanding = location.pathname === '/'

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold tracking-tight">
          TempoTailor
        </Link>
        <nav className="flex items-center gap-6">
          {user ? (
            <>
              <Link
                to="/create"
                className="text-gray-400 hover:text-white text-sm transition-colors"
              >
                Create
              </Link>
              <Link
                to="/history"
                className="text-gray-400 hover:text-white text-sm transition-colors"
              >
                My runs
              </Link>
              <span className="text-gray-400 text-sm">
                {user.display_name || user.email || user.id}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              {!isLanding && (
                <Link
                  to="/"
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Home
                </Link>
              )}
              <Button onClick={login}>Log in with Spotify</Button>
            </>
          )}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/create"
            element={
              <ProtectedRoute>
                <CreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/result"
            element={
              <ProtectedRoute>
                <ResultPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/draft/:id"
            element={
              <ProtectedRoute>
                <DraftDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/publish/:id"
            element={
              <ProtectedRoute>
                <PublishPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App
