/** Vietnamese number, currency and date formatting. */

const LOCALE = "vi-VN"
const TIME_ZONE = "Asia/Ho_Chi_Minh"

const integer = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 })
const oneDecimal = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 1 })
const threeDecimals = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 3 })

export function formatNumber(value: number, fractionDigits: 0 | 1 | 3 = 0): string {
  const formatter = fractionDigits === 0 ? integer : fractionDigits === 1 ? oneDecimal : threeDecimals
  return formatter.format(value)
}

/** 1245.5 -> "1.246 kWh" (or with decimals for small values). */
export function formatKwh(value: number): string {
  return `${formatNumber(value, Math.abs(value) < 100 ? 1 : 0)} kWh`
}

/** 72500000 -> "72.500.000 ₫" */
export function formatVnd(value: number): string {
  return `${integer.format(value)} ₫`
}

/** 72500000 -> "72,5 tr ₫"; 1250000000 -> "1,3 tỷ ₫" (for cards and chart axes). */
export function formatVndCompact(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1e9) return `${oneDecimal.format(value / 1e9)} tỷ ₫`
  if (abs >= 1e6) return `${oneDecimal.format(value / 1e6)} tr ₫`
  if (abs >= 1e3) return `${oneDecimal.format(value / 1e3)} nghìn ₫`
  return formatVnd(value)
}

export function formatPercent(value: number | null): string {
  if (value === null) return "—"
  const sign = value > 0 ? "+" : ""
  return `${sign}${oneDecimal.format(value)}%`
}

/** "2026-10-07" -> "07/10/2026" (date-only strings are not shifted by time zones). */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.slice(0, 10).split("-")
  return `${day}/${month}/${year}`
}

const dateTimeParts = new Intl.DateTimeFormat(LOCALE, {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
})

/** UTC timestamp -> "07/10/2026 14:00" in Vietnam time (vi-VN would put the time first). */
export function formatDateTime(isoDateTime: string): string {
  const parts = Object.fromEntries(
    dateTimeParts.formatToParts(new Date(isoDateTime)).map((part) => [part.type, part.value]),
  )
  return `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`
}
