import { CircleCheck, Info, OctagonAlert, TriangleAlert, type LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import type { AlertSeverity } from "@/types/models"

interface SeverityStyle {
  label: string
  icon: LucideIcon
  /** Status colour token; the icon and label always accompany it. */
  colorClass: string
}

export const SEVERITY: Record<AlertSeverity, SeverityStyle> = {
  CRITICAL: { label: "Nghiêm trọng", icon: OctagonAlert, colorClass: "text-status-critical" },
  WARNING: { label: "Cảnh báo", icon: TriangleAlert, colorClass: "text-status-serious" },
  INFO: { label: "Lưu ý", icon: Info, colorClass: "text-status-warning" },
}

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  const style = SEVERITY[severity]
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium whitespace-nowrap">
      <style.icon className={cn("size-4", style.colorClass)} aria-hidden />
      {style.label}
    </span>
  )
}

/** Status line for a floor trend (WARNING when consumption grew >= 20%). */
export function TrendStatusIcon({ warning }: { warning: boolean }) {
  return warning ? (
    <TriangleAlert className="text-status-serious size-4 shrink-0" aria-label="Cảnh báo" />
  ) : (
    <CircleCheck className="text-status-good size-4 shrink-0" aria-label="Bình thường" />
  )
}
