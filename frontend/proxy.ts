import { NextResponse, type NextRequest } from "next/server"

import { TOKEN_COOKIE } from "@/lib/auth"

/**
 * Optimistic route guard: only checks that the token cookie exists. The backend validates the
 * JWT on every API call and the client redirects to /login on 401.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl
  const hasToken = request.cookies.has(TOKEN_COOKIE)
  const isLoginPage = pathname === "/login"

  if (!hasToken && !isLoginPage) {
    const loginUrl = new URL("/login", request.nextUrl)
    if (pathname !== "/") {
      loginUrl.searchParams.set("next", pathname + search)
    }
    return NextResponse.redirect(loginUrl)
  }
  if (hasToken && isLoginPage) {
    return NextResponse.redirect(new URL("/dashboard", request.nextUrl))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|svg|ico|webp)$).*)"],
}
