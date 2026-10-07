import type { Metadata } from "next"

import { MetersView } from "@/components/views/meters-view"

export const metadata: Metadata = { title: "Công tơ" }

export default function Page() {
  return <MetersView />
}
