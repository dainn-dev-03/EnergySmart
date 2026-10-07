import type { Metadata } from "next"

import { BuildingsView } from "@/components/views/buildings-view"

export const metadata: Metadata = { title: "Tòa nhà" }

export default function BuildingsPage() {
  return <BuildingsView />
}
