import type { Option } from "@/components/forms/form-fields"
import type { MeterStatus, MeterType } from "@/types/models"

export const METER_STATUS_LABELS: Record<MeterStatus, string> = {
  ACTIVE: "Hoạt động",
  MAINTENANCE: "Bảo trì",
  INACTIVE: "Ngưng hoạt động",
}

export const METER_TYPE_LABELS: Record<MeterType, string> = {
  SINGLE_PHASE: "1 pha",
  THREE_PHASE: "3 pha",
}

function toOptions<T extends string>(labels: Record<T, string>): Option[] {
  return (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
}

export const METER_STATUS_OPTIONS = toOptions(METER_STATUS_LABELS)
export const METER_TYPE_OPTIONS = toOptions(METER_TYPE_LABELS)

export const HOUR_OPTIONS: Option[] = Array.from({ length: 24 }, (_, hour) => ({
  value: String(hour),
  label: `${String(hour).padStart(2, "0")}:00`,
}))
