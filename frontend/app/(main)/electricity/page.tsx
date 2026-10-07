import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Dữ liệu điện" }

export default function Page() {
  return <ComingSoon title="Dữ liệu điện" description="Điện năng tiêu thụ theo giờ của các công tơ" />
}
