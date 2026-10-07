import type { Metadata } from "next"

import { FloorsView } from "@/components/views/floors-view"

export const metadata: Metadata = { title: "Tầng" }

export default function Page() {
  return <FloorsView />
}
