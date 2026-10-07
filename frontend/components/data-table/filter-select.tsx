"use client"

import type { Option } from "@/components/forms/form-fields"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const ALL = "__all__"

interface FilterSelectProps {
  label: string
  value: string | number | undefined
  options: Option[]
  onChange: (value: string | undefined) => void
  allLabel?: string
  className?: string
}

/** Filter dropdown with an "all" entry (Radix Select cannot use an empty value). */
export function FilterSelect({
  label,
  value,
  options,
  onChange,
  allLabel = "Tất cả",
  className = "w-full sm:w-48",
}: FilterSelectProps) {
  return (
    <Select
      value={value === undefined ? ALL : String(value)}
      onValueChange={(next) => onChange(next === ALL ? undefined : next)}
    >
      <SelectTrigger className={className} aria-label={label}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>
          {label}: {allLabel.toLowerCase()}
        </SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function toNumber(value: string | undefined): number | undefined {
  return value === undefined ? undefined : Number(value)
}
