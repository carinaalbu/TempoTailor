import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Link,
  useLocation,
} from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { LandingPage } from "@/pages/LandingPage";
import { CreatePage } from "@/pages/CreatePage";
import { ResultPage } from "@/pages/ResultPage";
import { HistoryPage } from "@/pages/HistoryPage";
import { DraftDetailPage } from "@/pages/DraftDetailPage";
import { PublishPage } from "@/pages/PublishPage";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, login, logout } = useAuth();
  const location = useLocation();
  const isLanding = location.pathname === "/";

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className={`min-h-screen text-white ${isLanding ? "bg-gray-950" : "mesh-gradient"}`}>
      {!isLanding && (
        <nav className="relative z-10 flex items-center justify-between px-6 py-5 md:px-10 lg:px-16">
          <Link
            to="/"
            className="text-xl md:text-2xl font-bold text-white tracking-tight"
          >
            TempoTailor
          </Link>
          <div className="flex items-center gap-4 md:gap-6">
            {user ? (
              <>
                <Link
                  to="/create"
                  className="text-white text-sm font-medium hover:text-green-400 transition-colors"
                >
                  Create
                </Link>
                <Link
                  to="/history"
                  className="text-white text-sm font-medium hover:text-green-400 transition-colors"
                >
                  My runs
                </Link>
                <div className="flex items-center gap-2">
                  <div
                    className="h-9 w-9 rounded-full overflow-hidden border border-white/20 flex-shrink-0 bg-violet-900/60"
                    aria-hidden
                  >
                    {user.image_url ? (
                      <img
                        src={user.image_url}
                        alt=""
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="h-full w-full flex items-center justify-center">
                        <svg
                          className="w-5 h-5 text-violet-300"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <span className="text-sm text-gray-300 max-w-[120px] truncate hidden sm:inline">
                    {user.display_name || user.email || "Profile"}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium rounded-full border border-white/20 hover:bg-white/5 transition-colors text-white"
                >
                  Log out
                </button>
              </>
            ) : (
              <button
                onClick={login}
                className="px-4 py-2 text-sm font-medium rounded-full border border-white/20 hover:bg-white/5 transition-colors text-white"
              >
                Log in with Spotify
              </button>
            )}
          </div>
        </nav>
      )}
      <main>{children}</main>
    </div>
  );
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
  );
}

export default App;
