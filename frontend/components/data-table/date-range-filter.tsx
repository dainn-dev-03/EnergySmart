"use client"

import { DatePicker } from "@/components/forms/date-picker"

interface DateRangeFilterProps {
  from: string | undefined
  to: string | undefined
  onChange: (range: { from: string | undefined; to: string | undefined }) => void
}

/** From/to calendar dates (Vietnam days). An empty bound means "no limit". */
export function DateRangeFilter({ from, to, onChange }: DateRangeFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <DatePicker
        value={from}
        max={to}
        onChange={(value) => onChange({ from: value, to })}
        placeholder="Từ ngày"
        aria-label="Từ ngày"
        clearable
        className="w-full sm:w-40"
      />
      <span className="text-muted-foreground text-sm">→</span>
      <DatePicker
        value={to}
        min={from}
        onChange={(value) => onChange({ from, to: value })}
        placeholder="Đến ngày"
        aria-label="Đến ngày"
        clearable
        className="w-full sm:w-40"
      />
    </div>
  )
}
