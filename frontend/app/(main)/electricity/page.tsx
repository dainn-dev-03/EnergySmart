import type { Metadata } from "next"

import { ElectricityView } from "@/components/views/electricity-view"

export const metadata: Metadata = { title: "Dữ liệu điện" }

export default function Page() {
  return <ElectricityView />
}
