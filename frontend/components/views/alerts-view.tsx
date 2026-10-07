"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CheckCheck, Loader2, ScanSearch } from "lucide-react"
import { toast } from "sonner"

import { CrudList, Muted } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { DateRangeFilter } from "@/components/data-table/date-range-filter"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { SeverityBadge, SEVERITY } from "@/components/dashboard/severity-badge"
import type { Option } from "@/components/forms/form-fields"
import { PageHeader } from "@/components/layout/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useFloorOptions } from "@/hooks/use-options"
import { useResourceList } from "@/hooks/use-resource"
import { apiPost, errorMessage } from "@/lib/api"
import { formatDate, formatDateTime, formatKwh } from "@/lib/format"
import { createResource } from "@/lib/resources"
import type { Alert, AlertSeverity } from "@/types/models"

const alertsApi = createResource<Alert, never>("/alerts")

const STATUS_OPTIONS: Option[] = [
  { value: "false", label: "Chưa xử lý" },
  { value: "true", label: "Đã xử lý" },
]
const SEVERITY_OPTIONS: Option[] = (Object.keys(SEVERITY) as AlertSeverity[]).map((severity) => ({
  value: severity,
  label: SEVERITY[severity].label,
}))

export function AlertsView() {
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const floors = useFloorOptions()
  const list = useListState({ sort_by: "created_at", sort_order: "desc", is_resolved: false })
  const query = useResourceList(alertsApi, list.params)

  const refreshAlerts = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ["/alerts"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    ])
  const onError = (error: unknown) => toast.error(errorMessage(error))
  const resolve = useMutation({
    mutationFn: (id: number) => apiPost<Alert>(`/alerts/${id}/resolve`),
    onSuccess: ({ message }) => {
      toast.success(message)
      return refreshAlerts()
    },
    onError,
  })
  const detect = useMutation({
    mutationFn: () => apiPost<{ created_alerts: number }>("/alerts/detect"),
    onSuccess: ({ message }) => {
      toast.success(`Đã kiểm tra dữ liệu hôm qua. ${message}`)
      return refreshAlerts()
    },
    onError,
  })

  const columns: Column<Alert>[] = [
    {
      key: "severity",
      header: "Mức độ",
      className: "w-36",
      cell: (a) => <SeverityBadge severity={a.severity} />,
    },
    {
      key: "usage_date",
      header: "Ngày",
      sortKey: "usage_date",
      className: "w-28",
      cell: (a) => formatDate(a.usage_date),
    },
    {
      key: "meter",
      header: "Công tơ",
      className: "w-48",
      cell: (a) => (
        <div className="leading-tight">
          <p className="font-medium">{a.meter.meter_code}</p>
          <p className="text-muted-foreground text-xs">{a.meter.room.floor.name}</p>
        </div>
      ),
    },
    { key: "message", header: "Nội dung", cell: (a) => <p className="max-w-md text-sm whitespace-normal">{a.message}</p> },
    {
      key: "actual_value",
      header: "Thực tế / ngưỡng",
      sortKey: "actual_value",
      className: "w-40 text-right",
      cell: (a) =>
        a.actual_value === null ? (
          <Muted />
        ) : (
          <span className="tabular-nums">
            {formatKwh(a.actual_value)}
            <span className="text-muted-foreground block text-xs">
              ngưỡng {a.threshold_value === null ? "—" : formatKwh(a.threshold_value)}
            </span>
          </span>
        ),
    },
    {
      key: "status",
      header: "Trạng thái",
      className: "w-44",
      cell: (a) =>
        a.is_resolved ? (
          <span className="text-muted-foreground text-xs">
            Đã xử lý
            <br />
            {a.resolved_at ? formatDateTime(a.resolved_at) : null}
          </span>
        ) : canWrite ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => resolve.mutate(a.id)}
            disabled={resolve.isPending && resolve.variables === a.id}
          >
            <CheckCheck />
            Đã xử lý
          </Button>
        ) : (
          <Badge variant="secondary">Chưa xử lý</Badge>
        ),
    },
  ]

  return (
    <div className="space-y-4">
      <PageHeader
        title="Cảnh báo"
        description="Ngày có tiêu thụ cao bất thường so với trung bình 14 ngày cùng loại (ngưỡng 1,2 / 1,5 / 2 lần)"
        actions={
          canWrite ? (
            <Button variant="outline" onClick={() => detect.mutate()} disabled={detect.isPending}>
              {detect.isPending ? <Loader2 className="animate-spin" /> : <ScanSearch />}
              Kiểm tra dữ liệu hôm qua
            </Button>
          ) : null
        }
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <FilterSelect
          label="Trạng thái"
          value={list.params.is_resolved === undefined ? undefined : String(list.params.is_resolved)}
          options={STATUS_OPTIONS}
          onChange={(value) => list.setFilter("is_resolved", value)}
        />
        <FilterSelect
          label="Mức độ"
          value={list.params.severity as string | undefined}
          options={SEVERITY_OPTIONS}
          onChange={(value) => list.setFilter("severity", value)}
        />
        <FilterSelect
          label="Tầng"
          value={list.params.floor_id as number | undefined}
          options={floors}
          onChange={(value) => list.setFilter("floor_id", toNumber(value))}
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
      <CrudList query={query} list={list} columns={columns} emptyMessage="Không có cảnh báo phù hợp" />
    </div>
  )
}
