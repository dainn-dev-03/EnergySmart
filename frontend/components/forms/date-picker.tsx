"use client"

import { CalendarIcon } from "lucide-react"
import { useState } from "react"
import { vi } from "react-day-picker/locale"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { formatDate } from "@/lib/format"
import { cn } from "@/lib/utils"

/** "2026-10-07" <-> Date at local midnight (calendar dates carry no time zone). */
function toDate(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number)
  return new Date(year, month - 1, day)
}

function toIsoDate(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

interface DatePickerProps {
  value: string | undefined
  onChange: (value: string | undefined) => void
  placeholder?: string
  min?: string
  max?: string
  id?: string
  "aria-label"?: string
  "aria-invalid"?: boolean
  clearable?: boolean
  className?: string
}

/**
 * Date input that always shows dd/MM/yyyy with a Vietnamese calendar
 * (a native <input type="date"> follows the OS locale, e.g. MM/DD/YYYY).
 */
export function DatePicker({
  value,
  onChange,
  placeholder = "Chọn ngày",
  min,
  max,
  id,
  clearable = false,
  className,
  ...aria
}: DatePickerProps) {
  const [open, setOpen] = useState(false)
  const selected = value ? toDate(value) : undefined
  const disabled = [
    ...(min ? [{ before: toDate(min) }] : []),
    ...(max ? [{ after: toDate(max) }] : []),
  ]

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          className={cn("justify-start font-normal tabular-nums", !value && "text-muted-foreground", className)}
          {...aria}
        >
          <CalendarIcon className="text-muted-foreground" />
          {value ? formatDate(value) : placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          locale={vi}
          selected={selected}
          defaultMonth={selected}
          disabled={disabled}
          onSelect={(date) => {
            onChange(date ? toIsoDate(date) : undefined)
            setOpen(false)
          }}
        />
        {clearable && value ? (
          <div className="border-t p-2">
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={() => {
                onChange(undefined)
                setOpen(false)
              }}
            >
              Xóa ngày
            </Button>
          </div>
        ) : null}
      </PopoverContent>
    </Popover>
  )
}
