import Cookies from "js-cookie"

/** Cookie holding the JWT. Read by proxy.ts (route guard) and by the API client. */
export const TOKEN_COOKIE = "es_token"

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_COOKIE)
}

export function setToken(token: string, expiresInSeconds: number): void {
  Cookies.set(TOKEN_COOKIE, token, {
    expires: expiresInSeconds / 86_400, // js-cookie expects days
    sameSite: "lax",
    secure: window.location.protocol === "https:",
    path: "/",
  })
}

export function clearToken(): void {
  Cookies.remove(TOKEN_COOKIE, { path: "/" })
}

/**
 * Full page navigation to /login. Used outside React (axios interceptor) and on logout: reloading
 * also discards every cached query, so no data of the previous session survives.
 */
function goToLogin(query = ""): void {
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.assign(`/login${query}`)
}

/** Send the browser to /login, remembering where to come back after signing in. */
export function redirectToLogin(): void {
  const { pathname, search } = window.location
  goToLogin(pathname.startsWith("/login") ? "" : `?next=${encodeURIComponent(pathname + search)}`)
}

export function logout(): void {
  clearToken()
  goToLogin()
}
