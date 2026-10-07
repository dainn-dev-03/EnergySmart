import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Dashboard" }

export default function Page() {
  return <ComingSoon title="Dashboard" description="Tình hình tiêu thụ điện của tòa nhà" />
}
