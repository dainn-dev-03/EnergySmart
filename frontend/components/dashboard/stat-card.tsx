import type { LucideIcon } from "lucide-react"
import type { ReactNode } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface StatCardProps {
  label: string
  value: string | undefined
  icon: LucideIcon
  /** Secondary line, e.g. a delta versus the previous period. */
  footer?: ReactNode
}

/** Stat tile: sentence-case label, one prominent value (proportional figures), optional footer. */
export function StatCard({ label, value, icon: Icon, footer }: StatCardProps) {
  return (
    <Card className="gap-2 border-border/60">
      <CardHeader className="flex flex-row items-center justify-between pb-2 z-10 relative">
        <CardTitle className="text-muted-foreground text-sm font-medium">{label}</CardTitle>
        <div className="bg-primary/10 text-primary p-2 rounded-md">
          <Icon className="size-4" aria-hidden />
        </div>
      </CardHeader>
      <CardContent className="space-y-1.5 z-10 relative">
        {value === undefined ? (
          <Skeleton className="h-9 w-28" />
        ) : (
          <p className="text-3xl font-bold tracking-tight text-foreground">{value}</p>
        )}
        {footer ? <div className="text-muted-foreground text-xs pt-1 border-t border-border/40 font-medium flex items-center">{footer}</div> : null}
      </CardContent>
    </Card>
  )
}
