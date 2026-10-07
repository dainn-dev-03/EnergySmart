import type { Metadata } from "next"
import { Zap } from "lucide-react"

import { LoginForm } from "@/components/forms/login-form"

export const metadata: Metadata = { title: "Đăng nhập" }

export default function LoginPage() {
  return (
    <main className="bg-muted/40 flex min-h-svh flex-col items-center justify-center gap-6 p-6">
      <div className="flex items-center gap-2 text-lg font-semibold">
        <div className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-lg">
          <Zap className="size-5" />
        </div>
        EnergySmart
      </div>
      <LoginForm />
      <p className="text-muted-foreground text-center text-xs">
        Hệ thống quản lý và phân tích tiêu thụ điện năng tòa nhà
      </p>
    </main>
  )
}
