"use client"

import { useQuery } from "@tanstack/react-query"

import { CrudList, Muted } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { PageHeader } from "@/components/layout/page-header"
import { useIsAdmin } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { apiList } from "@/lib/api"
import { formatDateTime } from "@/lib/format"
import type { AuditLog } from "@/types/models"

const columns: Column<AuditLog>[] = [
  { key: "created_at", header: "Thời điểm", sortKey: "created_at", cell: (row) => formatDateTime(row.created_at) },
  { key: "user", header: "Người thao tác", cell: (row) => row.user?.full_name ?? row.user?.username ?? <Muted>Hệ thống</Muted> },
  { key: "action", header: "Thao tác", cell: (row) => row.action },
  { key: "entity", header: "Dữ liệu", cell: (row) => <span>{row.entity_label} <Muted>({row.entity_type}{row.entity_id ? ` #${row.entity_id}` : ""})</Muted></span> },
  { key: "changes", header: "Thay đổi", cell: (row) => row.changes ? <span className="line-clamp-2 max-w-md text-xs">{Object.keys(row.changes).join(", ")}</span> : <Muted /> },
]

export function AuditLogsView() {
  const isAdmin = useIsAdmin()
  const list = useListState({ sort_by: "created_at", sort_order: "desc" })
  const query = useQuery({ queryKey: ["audit-logs", list.params], queryFn: () => apiList<AuditLog>("/audit-logs", list.params), enabled: isAdmin })
  if (!isAdmin) return null
  return <div className="space-y-4">
    <PageHeader title="Nhật ký hoạt động" description="Lịch sử tạo, sửa, xóa và xử lý cảnh báo." />
    <CrudList query={query} list={list} columns={columns} emptyMessage="Chưa có hoạt động nào" />
  </div>
}
