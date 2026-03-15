import { PublicClientApplication, type Configuration } from "@azure/msal-browser";

const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID ?? "";

const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: import.meta.env.VITE_ENTRA_AUTHORITY ?? "",
    redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI ?? window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage",
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: [`api://${clientId}/.default`],
};

export const isEntraEnabled = !!clientId;
