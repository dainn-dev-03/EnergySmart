import type { Metadata } from "next"
import { Zap } from "lucide-react"

import { LoginForm } from "@/components/forms/login-form"

export const metadata: Metadata = { title: "Đăng nhập" }

export default function LoginPage() {
  return (
    <main className="relative flex min-h-svh flex-col items-center justify-center p-6 sm:p-12 overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 -z-20 bg-[url('/bg-login.png')] bg-cover bg-center bg-no-repeat" />
      <div className="absolute inset-0 -z-10 bg-background/40 backdrop-blur-[2px] dark:bg-background/60" />

      <div className="z-10 flex w-full max-w-[400px] flex-col items-center gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="bg-gradient-to-br from-primary to-primary/70 text-primary-foreground flex size-14 items-center justify-center rounded-2xl shadow-lg shadow-primary/30 ring-1 ring-white/20">
            <Zap className="size-7" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">EnergySmart</h1>
          <p className="text-muted-foreground text-sm font-medium">
            Hệ thống quản lý tiêu thụ điện năng thông minh
          </p>
        </div>
        
        <LoginForm />
        
        <p className="text-muted-foreground/60 text-center text-xs">
          &copy; {new Date().getFullYear()} EnergySmart Tower. All rights reserved.
        </p>
      </div>
    </main>
  )
}
