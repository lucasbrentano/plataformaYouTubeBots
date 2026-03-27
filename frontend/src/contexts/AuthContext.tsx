import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";

interface JWTPayload {
  sub: string;
  role: string;
  exp: number;
}

interface AuthUser {
  username: string;
  role: string;
}

interface AuthContextType {
  token: string | null;
  user: AuthUser | null;
  isAdmin: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function decodeJWT(token: string): JWTPayload | null {
  try {
    return JSON.parse(atob(token.split(".")[1])) as JWTPayload;
  } catch {
    return null;
  }
}

function readStoredUser(): AuthUser | null {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  const payload = decodeJWT(token);
  if (!payload || payload.exp * 1000 < Date.now()) {
    localStorage.removeItem("access_token");
    return null;
  }
  return { username: payload.sub, role: payload.role };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("access_token"),
  );
  const [user, setUser] = useState<AuthUser | null>(readStoredUser);

  const login = useCallback((newToken: string) => {
    localStorage.setItem("access_token", newToken);
    setToken(newToken);
    const payload = decodeJWT(newToken);
    if (payload) {
      setUser({ username: payload.sub, role: payload.role });
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
  }, []);

  const isAdmin = user?.role === "admin";

  return (
    <AuthContext.Provider value={{ token, user, isAdmin, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext deve ser usado dentro de AuthProvider");
  return ctx;
}
