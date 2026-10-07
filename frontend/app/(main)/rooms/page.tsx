import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Phòng" }

export default function Page() {
  return <ComingSoon title="Phòng" description="Quản lý phòng trong từng tầng" />
}
