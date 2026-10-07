import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Báo cáo" }

export default function Page() {
  return <ComingSoon title="Báo cáo" description="Báo cáo tiêu thụ và xuất file CSV" />
}
