import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Tầng" }

export default function Page() {
  return <ComingSoon title="Tầng" description="Quản lý các tầng của tòa nhà" />
}
