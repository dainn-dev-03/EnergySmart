"use client"

import { ArrowRight, MessageCircle, Zap } from "lucide-react"
import Image from "next/image"
import Link from "next/link"

import { NAVIGATION } from "@/components/layout/navigation"
import { Button } from "@/components/ui/button"
import { useIsAdmin } from "@/hooks/use-current-user"

export function DashboardView() {
  const isAdmin = useIsAdmin()
  const sections = NAVIGATION.filter(
    (group) => group.label !== "Tổng quan" && (group.label !== "Quản trị" || isAdmin),
  )

  return (
    <div className="space-y-8 pb-6">
      <section className="relative isolate flex min-h-72 items-center overflow-hidden rounded-lg bg-[#143b32] px-6 py-8 text-white sm:px-10 lg:min-h-80 lg:px-14">
        <Image
          src="/bg-login.png"
          alt="Tuabin gió giữa khung cảnh đồi núi lúc hoàng hôn"
          fill
          priority
          sizes="(max-width: 768px) 100vw, 1200px"
          className="-z-20 object-cover object-center"
        />
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(90deg,rgba(13,43,36,0.96)_0%,rgba(18,58,48,0.88)_48%,rgba(17,54,45,0.25)_100%)]" />
        <div className="max-w-2xl space-y-5">
          <div className="inline-flex items-center gap-2 border-l-2 border-emerald-300 pl-3 text-xs font-semibold uppercase text-emerald-100">
            <Zap className="size-4" aria-hidden />
            Nền tảng quản lý năng lượng
          </div>
          <div className="space-y-2">
            <h1 className="font-heading text-4xl font-semibold sm:text-5xl">EnergySmart</h1>
            <p className="max-w-xl text-sm leading-6 text-white/85 sm:text-base">
              Quản lý tòa nhà, theo dõi dữ liệu điện và khám phá xu hướng tiêu thụ trong cùng một không gian làm việc.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild className="bg-white text-[#174b3b] hover:bg-emerald-50">
              <Link href="/analytics">
                Khám phá phân tích
                <ArrowRight />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-white/70 bg-white/10 text-white hover:bg-white/20 hover:text-white"
            >
              <Link href="/chat">
                <MessageCircle />
                Trợ lý AI
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <section aria-labelledby="workspace-links-heading" className="space-y-5">
        <div className="flex flex-col gap-1 border-b pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-primary">Không gian làm việc</p>
            <h2 id="workspace-links-heading" className="mt-1 text-xl font-semibold">
              Bắt đầu từ một khu vực
            </h2>
          </div>
          <p className="text-muted-foreground text-sm">Chọn chức năng để tiếp tục</p>
        </div>

        <div className="space-y-8">
          {sections.map((group) => (
            <section key={group.label} aria-label={group.label} className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">{group.label}</h3>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {group.items.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="group flex min-h-28 items-start gap-4 rounded-md border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-primary/2.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <item.icon className="size-5" aria-hidden />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-medium">{item.title}</span>
                        <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" aria-hidden />
                      </span>
                      <span className="mt-1 block text-sm leading-5 text-muted-foreground">{item.description}</span>
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>
    </div>
  )
}
