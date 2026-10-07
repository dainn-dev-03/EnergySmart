/** Calendar dates (YYYY-MM-DD) in Vietnam time, for default filter ranges. */

const vietnamDate = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Ho_Chi_Minh",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})

export function todayInVietnam(): string {
  return vietnamDate.format(new Date())
}

export function shiftDays(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

export function monthStart(isoDate: string): string {
  return `${isoDate.slice(0, 7)}-01`
}
