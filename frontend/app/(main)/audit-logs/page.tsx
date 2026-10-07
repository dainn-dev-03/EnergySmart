import type { Metadata } from "next"

import { AuditLogsView } from "@/components/views/audit-logs-view"

export const metadata: Metadata = { title: "Nhật ký hoạt động" }

export default function AuditLogsPage() {
  return <AuditLogsView />
}
