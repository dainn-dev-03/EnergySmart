import type { Metadata } from "next"

import { RoomsView } from "@/components/views/rooms-view"

export const metadata: Metadata = { title: "Phòng" }

export default function Page() {
  return <RoomsView />
}
