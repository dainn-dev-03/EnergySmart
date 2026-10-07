"use client"

import { usePathname } from "next/navigation"

import { findNavItem } from "@/components/layout/navigation"
import { UserMenu } from "@/components/layout/user-menu"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

export function AppHeader() {
  const current = findNavItem(usePathname())

  return (
    <header className="bg-background/95 sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-4 backdrop-blur">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 data-vertical:h-4 data-vertical:self-center" />
      <h1 className="truncate text-base font-semibold">{current?.title ?? "EnergySmart"}</h1>
      <div className="ml-auto">
        <UserMenu />
      </div>
    </header>
  )
}
