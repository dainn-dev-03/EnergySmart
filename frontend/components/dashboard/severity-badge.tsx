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
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap border",
      severity === "CRITICAL" && "bg-status-critical/10 text-status-critical border-status-critical/20",
      severity === "WARNING" && "bg-status-serious/10 text-status-serious border-status-serious/20",
      severity === "INFO" && "bg-status-warning/10 text-status-warning border-status-warning/20",
    )}>
      <style.icon className="size-3.5" aria-hidden />
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
