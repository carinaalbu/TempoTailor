import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { api } from "../lib/api";
import { SPOTIFY_AUTH_EXPIRED_EVENT } from "../lib/api";

const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

interface User {
  id: string
  display_name: string | null
  email: string | null
  image_url: string | null
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  authError: string | null;
  login: () => void;
  logout: () => void;
  reAuthorize: () => void;
  clearAuthError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const ERROR_MESSAGES: Record<string, string> = {
  missing_code: "Authorization was cancelled or incomplete.",
  invalid_state: "Invalid login state. Please try again.",
  auth_failed: "Spotify authentication failed. Please try again.",
  access_denied: "You denied access to your Spotify account.",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("spotify_token"),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const fetchUser = useCallback(async (accessToken: string) => {
    try {
      const { data } = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setUser(data);
      setAuthError(null);
    } catch {
      setUser(null);
      setToken(null);
      localStorage.removeItem("spotify_token");
      localStorage.removeItem("spotify_refresh_token");
    }
  }, []);

  const clearAuthError = useCallback(() => setAuthError(null), []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");
    const urlError = params.get("error");

    if (urlError) {
      setAuthError(
        ERROR_MESSAGES[urlError] || "Login failed. Please try again.",
      );
      setToken(null);
      localStorage.removeItem("spotify_token");
      window.history.replaceState({}, "", window.location.pathname);
      setIsLoading(false);
      return;
    }

    if (urlToken) {
      const urlRefresh = params.get("refresh_token");
      localStorage.setItem("spotify_token", urlToken);
      if (urlRefresh) localStorage.setItem("spotify_refresh_token", urlRefresh);
      setToken(urlToken);
      setAuthError(null);
      fetchUser(urlToken).finally(() => setIsLoading(false));
      window.history.replaceState({}, "", window.location.pathname);
    } else if (token) {
      fetchUser(token).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [token, fetchUser]);

  const login = () => {
    setAuthError(null);
    window.location.href = `${API_BASE}/auth/login`;
  };

  const logout = useCallback(() => {
    localStorage.removeItem("spotify_token");
    localStorage.removeItem("spotify_refresh_token");
    setToken(null);
    setUser(null);
    setAuthError(null);
  }, []);

  const reAuthorize = useCallback(() => {
    localStorage.removeItem("spotify_token");
    localStorage.removeItem("spotify_refresh_token");
    setToken(null);
    setUser(null);
    setAuthError(null);
    window.location.href = `${API_BASE}/auth/login`;
  }, []);

  useEffect(() => {
    const handleAuthExpired = () => {
      setToken(null);
      setUser(null);
      if (sessionStorage.getItem("spotify_403")) {
        sessionStorage.removeItem("spotify_403");
        setAuthError(
          "Spotify denied access. Please log in again to grant permissions.",
        );
      }
    };
    window.addEventListener(SPOTIFY_AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () =>
      window.removeEventListener(SPOTIFY_AUTH_EXPIRED_EVENT, handleAuthExpired);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        authError,
        login,
        logout,
        reAuthorize,
        clearAuthError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
