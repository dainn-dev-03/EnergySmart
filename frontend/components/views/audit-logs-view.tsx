"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { CrudList, Muted } from "@/components/data-table/crud-list"
import { DateRangeFilter } from "@/components/data-table/date-range-filter"
import { FilterSelect } from "@/components/data-table/filter-select"
import type { Column } from "@/components/data-table/data-table"
import type { Option } from "@/components/forms/form-fields"
import { PageHeader } from "@/components/layout/page-header"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useIsAdmin } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { apiList } from "@/lib/api"
import { formatDateTime } from "@/lib/format"
import type { AuditLog } from "@/types/models"

const ACTION_OPTIONS: Option[] = [
  { value: "CREATE", label: "Tạo dữ liệu" },
  { value: "UPDATE", label: "Cập nhật dữ liệu" },
  { value: "DELETE", label: "Xóa dữ liệu" },
  { value: "LOGIN", label: "Đăng nhập" },
  { value: "LOGOUT", label: "Đăng xuất" },
  { value: "CHANGE_PASSWORD", label: "Đổi mật khẩu" },
  { value: "CREATE_USER", label: "Tạo người dùng" },
  { value: "UPDATE_USER", label: "Cập nhật người dùng" },
  { value: "DEACTIVATE_USER", label: "Khóa người dùng" },
  { value: "ACTIVATE_USER", label: "Mở khóa người dùng" },
  { value: "RESET_PASSWORD", label: "Đặt lại mật khẩu" },
  { value: "RESOLVE", label: "Xử lý cảnh báo" },
  { value: "DETECT_ALERTS", label: "Phát hiện cảnh báo" },
]

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—"
  if (typeof value === "string") return value
  if (typeof value === "number" || typeof value === "boolean") return String(value)
  return JSON.stringify(value, null, 2) ?? String(value)
}

const columns: Column<AuditLog>[] = [
  { key: "created_at", header: "Thời điểm", sortKey: "created_at", cell: (row) => formatDateTime(row.created_at) },
  { key: "action", header: "Thao tác", cell: (row) => row.action },
  { key: "ip_address", header: "Địa chỉ IP", cell: (row) => row.ip_address ?? <Muted /> },
  { key: "changes", header: "Thay đổi", cell: (row) => row.changes ? <span className="line-clamp-2 max-w-md text-xs">{Object.keys(row.changes).join(", ")}</span> : <Muted /> },
]

export function AuditLogsView() {
  const isAdmin = useIsAdmin()
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)
  const list = useListState({ sort_by: "created_at", sort_order: "desc" })
  const queryParams = {
    ...list.params,
    from_date: list.params.from_date
      ? `${String(list.params.from_date).slice(0, 10)}T00:00:00+07:00`
      : undefined,
    to_date: list.params.to_date
      ? `${String(list.params.to_date).slice(0, 10)}T23:59:59.999999+07:00`
      : undefined,
  }
  const query = useQuery({ queryKey: ["audit-logs", queryParams], queryFn: () => apiList<AuditLog>("/audit-logs", queryParams), enabled: isAdmin })
  if (!isAdmin) return null
  return <div className="flex min-h-0 flex-1 flex-col gap-4">
    <PageHeader title="Nhật ký hoạt động" description="Lịch sử đăng nhập, thay đổi dữ liệu và thao tác quan trọng. Chọn một dòng để xem chi tiết." />
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
      <FilterSelect
        label="Thao tác"
        value={list.params.action as string | undefined}
        options={ACTION_OPTIONS}
        onChange={(value) => list.setFilter("action", value)}
      />
      <DateRangeFilter
        from={list.params.from_date as string | undefined}
        to={list.params.to_date as string | undefined}
        onChange={({ from, to }) => {
          list.setFilter("from_date", from)
          list.setFilter("to_date", to)
        }}
      />
    </div>
    <CrudList query={query} list={list} columns={columns} emptyMessage="Chưa có hoạt động nào" onRowClick={setSelectedLog} fillHeight />
    <Dialog open={selectedLog !== null} onOpenChange={(open) => !open && setSelectedLog(null)}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Chi tiết thao tác</DialogTitle>
        </DialogHeader>
        {selectedLog && (
          <div className="space-y-5">
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm text-muted-foreground">Thời điểm</dt>
                <dd className="mt-1">{formatDateTime(selectedLog.created_at)}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Người thao tác</dt>
                <dd className="mt-1">{selectedLog.user?.full_name ?? selectedLog.user?.username ?? "Hệ thống"}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Thao tác</dt>
                <dd className="mt-1">{selectedLog.action}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Dữ liệu</dt>
                <dd className="mt-1 break-words">{selectedLog.entity_label} ({selectedLog.entity_type}{selectedLog.entity_id ? ` #${selectedLog.entity_id}` : ""})</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Địa chỉ IP</dt>
                <dd className="mt-1">{selectedLog.ip_address ?? "—"}</dd>
              </div>
            </dl>
            <section className="space-y-2">
              <h3 className="text-sm font-medium">Chi tiết thay đổi</h3>
              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 ? (
                <div className="divide-y rounded-md border">
                  {Object.entries(selectedLog.changes).map(([field, change]) => {
                    const values = Array.isArray(change) ? change : [undefined, change]
                    return (
                      <div className="grid gap-3 p-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)]" key={field}>
                        <div className="font-medium break-words">{field}</div>
                        <div className="min-w-0">
                          <div className="mb-1 text-xs text-muted-foreground">Trước</div>
                          <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs">{formatValue(values[0])}</pre>
                        </div>
                        <div className="min-w-0">
                          <div className="mb-1 text-xs text-muted-foreground">Sau</div>
                          <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs">{formatValue(values[1])}</pre>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Thao tác này không lưu giá trị thay đổi chi tiết.</p>
              )}
            </section>
          </div>
        )}
      </DialogContent>
    </Dialog>
  </div>
}
