import {
  BrowserCacheLocation,
  PublicClientApplication,
} from '@azure/msal-browser'

import type { Configuration } from '@azure/msal-browser'

const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID
const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: `${window.location.origin}/`,
    postLogoutRedirectUri: `${window.location.origin}/`,
  },
  cache: {
    cacheLocation: BrowserCacheLocation.SessionStorage,
  },
}

export const msalInstance =
  new PublicClientApplication(msalConfig)

export const loginRequest = {
  scopes: ['openid', 'profile'],
}
