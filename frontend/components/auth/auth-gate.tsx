"use client"

import { useEffect, useSyncExternalStore, type ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useCurrentUser } from "@/hooks/use-current-user"
import { errorMessage } from "@/lib/api"
import { getToken, redirectToLogin } from "@/lib/auth"

const noopSubscribe = () => () => {}

/** false while prerendering on the server and during hydration, true afterwards. */
function useIsClient(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  )
}

/**
 * Renders the signed-in area only in the browser once `/auth/me` succeeds.
 * Keeping data hooks out of the server prerender is what lets every page below fetch with
 * TanStack Query under `cacheComponents` without Suspense/time-related prerender errors.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  const isClient = useIsClient()
  if (!isClient) return <AppSkeleton />
  return <Session>{children}</Session>
}

function Session({ children }: { children: ReactNode }) {
  const hasToken = getToken() !== undefined
  const { data: user, error, refetch, isFetching } = useCurrentUser()

  useEffect(() => {
    if (!hasToken) redirectToLogin()
  }, [hasToken])

  if (!hasToken) return <AppSkeleton />
  if (error) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-muted-foreground max-w-md">{errorMessage(error)}</p>
        <Button onClick={() => refetch()} disabled={isFetching}>
          Thử lại
        </Button>
      </div>
    )
  }
  if (!user) return <AppSkeleton />
  return children
}

function AppSkeleton() {
  return (
    <div className="flex min-h-svh w-full" aria-busy="true" aria-label="Đang tải">
      <div className="bg-sidebar hidden w-64 shrink-0 border-r p-4 md:block">
        <Skeleton className="mb-6 h-8 w-40" />
        {Array.from({ length: 8 }, (_, index) => (
          <Skeleton key={index} className="mb-3 h-6 w-full" />
        ))}
      </div>
      <div className="flex-1 space-y-4 p-6">
        <Skeleton className="h-8 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-80" />
      </div>
    </div>
  )
}
