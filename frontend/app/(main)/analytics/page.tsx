import type { Metadata } from "next"

import { AnalyticsView } from "@/components/views/analytics-view"

export const metadata: Metadata = { title: "Phân tích" }

export default function Page() {
  return <AnalyticsView />
}
