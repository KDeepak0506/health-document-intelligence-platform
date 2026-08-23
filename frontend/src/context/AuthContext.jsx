import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { login as apiLogin } from "../api/auth";
import { tokenStore } from "../api/client";

const AuthContext = createContext(null);

// Decode the JWT payload just enough to show "who's logged in" without
// a round trip. Not used for anything security-sensitive on the client.
function decodeEmail(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || payload.email || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => tokenStore.get());
  const [email, setEmail] = useState(() => {
    const t = tokenStore.get();
    return t ? decodeEmail(t) : null;
  });

  useEffect(() => {
    if (token) {
      setEmail(decodeEmail(token));
    }
  }, [token]);

  const login = useCallback(async (credentials) => {
    const { access_token } = await apiLogin(credentials);
    tokenStore.set(access_token);
    setToken(access_token);
    return access_token;
  }, []);

  const logout = useCallback(() => {
    tokenStore.clear();
    setToken(null);
    setEmail(null);
  }, []);

  const value = {
    isAuthenticated: !!token,
    email,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
