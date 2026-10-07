"use client"

import { useQuery } from "@tanstack/react-query"

import { apiGet } from "@/lib/api"
import type { User, UserRole } from "@/types/models"

export const CURRENT_USER_KEY = ["auth", "me"] as const

export function useCurrentUser() {
  return useQuery({
    queryKey: CURRENT_USER_KEY,
    queryFn: () => apiGet<User>("/auth/me"),
    staleTime: Number.POSITIVE_INFINITY,
  })
}

const WRITE_ROLES: readonly UserRole[] = ["ADMIN", "MANAGER"]

/** Mirrors the backend rule: ADMIN and MANAGER may create/update/delete. */
export function useCanWrite(): boolean {
  const { data: user } = useCurrentUser()
  return user !== undefined && WRITE_ROLES.includes(user.role)
}

export function useIsAdmin(): boolean {
  const { data: user } = useCurrentUser()
  return user?.role === "ADMIN"
}

export const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: "Quản trị viên",
  MANAGER: "Quản lý",
  VIEWER: "Người xem",
}
