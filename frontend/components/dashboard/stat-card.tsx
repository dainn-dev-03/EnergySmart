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
    <Card className="gap-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-muted-foreground text-sm font-medium">{label}</CardTitle>
        <Icon className="text-muted-foreground size-4" aria-hidden />
      </CardHeader>
      <CardContent className="space-y-1">
        {value === undefined ? (
          <Skeleton className="h-8 w-28" />
        ) : (
          <p className="text-2xl font-semibold tracking-tight">{value}</p>
        )}
        {footer ? <div className="text-muted-foreground text-xs">{footer}</div> : null}
      </CardContent>
    </Card>
  )
}
