import type { ReactNode } from "react"

export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border/70 bg-card/80 p-3 shadow-sm sm:flex-row sm:flex-wrap sm:items-center">
      {children}
    </div>
  )
}