"use client"

import { Zap } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import { NAVIGATION } from "@/components/layout/navigation"
import { useIsAdmin } from "@/hooks/use-current-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

export function AppSidebar() {
  const pathname = usePathname()
  const isAdmin = useIsAdmin()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link
                href="/dashboard"
                className="group-data-[collapsible=icon]:justify-center"
              >
                <div className="bg-primary text-primary-foreground flex size-8 shrink-0 items-center justify-center rounded-lg">
                  <Zap className="size-4 shrink-0" />
                </div>
                <div className="grid min-w-0 flex-1 text-left leading-tight group-data-[collapsible=icon]:hidden">
                  <span className="font-semibold">EnergySmart</span>
                  <span className="text-muted-foreground text-xs">Quản lý điện năng</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {NAVIGATION.filter((group) => group.label !== "Quản trị" || isAdmin).map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  const isActive =
                    pathname === item.href || pathname.startsWith(`${item.href}/`)
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton 
                        asChild 
                        isActive={isActive} 
                        tooltip={item.title}
                        className="transition-colors data-[active=true]:bg-primary/10 data-[active=true]:text-primary data-[active=true]:font-medium hover:bg-muted"
                      >
                        <Link href={item.href} className="flex items-center gap-3">
                          <item.icon className={isActive ? "text-primary" : "text-muted-foreground"} />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <p className="text-muted-foreground px-2 text-xs group-data-[collapsible=icon]:hidden">
          EnergySmart Tower · v0.1
        </p>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
