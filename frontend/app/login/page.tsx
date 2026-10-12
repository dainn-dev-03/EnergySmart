import type { Metadata } from "next"
import Image from "next/image"
import { ArrowUpRight, Building2, Zap } from "lucide-react"

import { LoginForm } from "@/components/forms/login-form"

export const metadata: Metadata = { title: "Đăng nhập" }

export default function LoginPage() {
  return (
    <main className="min-h-svh bg-[#f5f7f4] lg:grid lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative isolate flex min-h-76 flex-col justify-between overflow-hidden bg-[#173d32] px-6 py-7 text-white sm:min-h-88 sm:px-10 sm:py-9 lg:min-h-svh lg:px-14 lg:py-12">
        <Image
          src="/bg-login.png"
          alt="Tuabin gió trên những ngọn đồi lúc hoàng hôn"
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 55vw"
          className="-z-20 object-cover object-center"
        />
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(12,43,35,0.78)_0%,rgba(15,48,39,0.28)_42%,rgba(12,43,35,0.94)_100%)]" />

        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-md bg-emerald-300 text-[#123a30]">
            <Zap className="size-5" aria-hidden />
          </div>
          <div>
            <p className="font-semibold leading-tight">EnergySmart</p>
            <p className="text-xs text-white/70">Quản lý năng lượng</p>
          </div>
        </div>

        <div className="max-w-xl space-y-5 pb-1">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase text-emerald-200">
            <span className="h-px w-7 bg-emerald-300" />
            Nền tảng vận hành tòa nhà
          </p>
          <div className="space-y-3">
            <h1 className="font-heading text-4xl font-semibold leading-tight sm:text-5xl">
              Hiểu rõ năng lượng. Chủ động vận hành.
            </h1>
            <p className="max-w-lg text-sm leading-6 text-white/80 sm:text-base">
              Kết nối dữ liệu từ tòa nhà, tầng, phòng và công tơ trong một góc nhìn thống nhất.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-white/85">
            <Building2 className="size-4 text-emerald-300" aria-hidden />
            Dữ liệu rõ ràng cho quyết định tốt hơn
            <ArrowUpRight className="size-4 text-emerald-300" aria-hidden />
          </div>
        </div>

        <p className="text-xs text-white/60">EnergySmart · Quản lý tiêu thụ điện năng</p>
      </section>

      <section className="flex min-h-136 items-center justify-center px-5 py-10 sm:px-8 lg:min-h-svh lg:px-12">
        <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-2 duration-500">
          <LoginForm />
          <p className="mt-6 text-center text-xs text-muted-foreground">
            Truy cập được bảo vệ bằng xác thực tài khoản EnergySmart.
          </p>
        </div>
      </section>
    </main>
  )
}
