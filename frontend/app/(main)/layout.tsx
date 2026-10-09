import { AuthGate } from "@/components/auth/auth-gate"
import { AppHeader } from "@/components/layout/app-header"
import { AppSidebar } from "@/components/layout/app-sidebar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export default function MainLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthGate>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <AppHeader />
          <main className="flex min-h-0 flex-1 flex-col p-4 md:p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </AuthGate>
  )
}
