import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Cảnh báo" }

export default function Page() {
  return <ComingSoon title="Cảnh báo" description="Các trường hợp tiêu thụ bất thường" />
}
