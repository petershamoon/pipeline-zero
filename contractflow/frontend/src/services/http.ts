import axios from "axios";
import { isEntraEnabled, msalInstance, loginRequest } from "@/config/msal";
import { useSessionStore } from "@/store/session";

export class HttpError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "HttpError";
  }
}

function readCookie(name: string): string | null {
  const prefixed = `${name}=`;
  const parts = document.cookie.split(";").map((part) => part.trim());
  const found = parts.find((part) => part.startsWith(prefixed));
  return found ? decodeURIComponent(found.slice(prefixed.length)) : null;
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api/v1",
  withCredentials: true,
});

http.interceptors.request.use(async (config) => {
  if (isEntraEnabled) {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      try {
        const response = await msalInstance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0],
        });
        config.headers.set("Authorization", `Bearer ${response.accessToken}`);
        return config;
      } catch {
        // Silent acquisition failed; fall through to CSRF
      }
    }
  }

  const method = (config.method ?? "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const csrf = readCookie("cf_csrf");
    if (csrf) {
      config.headers.set("X-CSRF-Token", csrf);
    }
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        useSessionStore.getState().setUser(null);
        window.location.href = "/login";
      }
      const message = typeof data?.detail === "string" ? data.detail : "Request failed";
      return Promise.reject(new HttpError(status, message));
    }
    return Promise.reject(error);
  }
);
