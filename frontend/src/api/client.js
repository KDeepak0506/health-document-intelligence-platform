import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const TOKEN_KEY = "ips18_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const client = axios.create({ baseURL: BASE_URL });

// Attach the bearer token to every outgoing request, per the API's
// "Bearer token (JWT) required on all endpoints except health check" convention.
client.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors into { code, message, status } regardless of where they
// came from, so components never have to inspect axios internals.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const body = error.response.data;
      const apiError = body?.error;
      if (status === 401) {
        tokenStore.clear();
      }
      return Promise.reject({
        status,
        code: apiError?.code || "UNKNOWN_ERROR",
        message: apiError?.message || "Something went wrong. Please try again.",
      });
    }
    if (error.request) {
      return Promise.reject({
        status: 0,
        code: "NETWORK_ERROR",
        message: "Can't reach the server. Check your connection and try again.",
      });
    }
    return Promise.reject({
      status: 0,
      code: "CLIENT_ERROR",
      message: error.message || "Unexpected error.",
    });
  }
);

export default client;
