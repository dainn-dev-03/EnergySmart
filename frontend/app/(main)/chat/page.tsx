import type { Metadata } from "next"

import { ChatView } from "@/components/views/chat-view"

export const metadata: Metadata = { title: "Trợ lý AI" }

export default function Page() {
  return <ChatView />
}
