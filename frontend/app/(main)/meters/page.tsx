import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Công tơ" }

export default function Page() {
  return <ComingSoon title="Công tơ" description="Quản lý công tơ điện" />
}
