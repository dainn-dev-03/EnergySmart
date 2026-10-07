import type { Metadata } from "next"

import { ComingSoon } from "@/components/layout/coming-soon"

export const metadata: Metadata = { title: "Phân tích" }

export default function Page() {
  return <ComingSoon title="Phân tích" description="Xu hướng tiêu thụ, giờ cao điểm và so sánh các kỳ" />
}
