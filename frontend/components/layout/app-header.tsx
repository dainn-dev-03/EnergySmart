"use client"

import { usePathname } from "next/navigation"

import { findNavGroup } from "@/components/layout/navigation"
import { UserMenu } from "@/components/layout/user-menu"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

export function AppHeader() {
  const currentGroup = findNavGroup(usePathname())

  return (
    <header className="glass sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b border-primary/15 px-4 shadow-sm transition-all">
      <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
      <Separator orientation="vertical" className="mr-2 data-vertical:h-5 data-vertical:self-center opacity-50" />
      
      <div className="flex items-center gap-1.5 text-sm">
        <span className="text-muted-foreground font-medium">{currentGroup?.label}</span>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <UserMenu />
      </div>
    </header>
  )
}
