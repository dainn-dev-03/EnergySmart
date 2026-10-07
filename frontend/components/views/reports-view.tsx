"use client"

import { useMutation, useQuery } from "@tanstack/react-query"
import { CalendarRange, Download, Loader2, Wallet, Zap } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { DateRangeFilter } from "@/components/data-table/date-range-filter"
import { FilterSelect } from "@/components/data-table/filter-select"
import { StatCard } from "@/components/dashboard/stat-card"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { apiDownload, apiGet, errorMessage } from "@/lib/api"
import { monthStart, todayInVietnam } from "@/lib/dates"
import { formatDate, formatKwh, formatNumber, formatVnd, formatVndCompact } from "@/lib/format"
import type { ConsumptionReport, ReportGroup } from "@/types/models"

const GROUPS: { value: ReportGroup; label: string; codeHeader: string }[] = [
  { value: "floor", label: "Theo tầng", codeHeader: "Số tầng" },
  { value: "room", label: "Theo phòng", codeHeader: "Mã phòng" },
  { value: "meter", label: "Theo công tơ", codeHeader: "Mã công tơ" },
]

export function ReportsView() {
  const today = todayInVietnam()
  const [range, setRange] = useState<{ from: string | undefined; to: string | undefined }>({
    from: monthStart(today),
    to: today,
  })
  const [groupBy, setGroupBy] = useState<ReportGroup>("floor")
  const params = { from_date: range.from, to_date: range.to, group_by: groupBy }
  const group = GROUPS.find((item) => item.value === groupBy) ?? GROUPS[0]

  const report = useQuery({
    queryKey: ["reports", "consumption", params],
    queryFn: () => apiGet<ConsumptionReport>("/reports/consumption", params),
  })
  const exportCsv = useMutation({
    mutationFn: () => apiDownload("/reports/consumption/export", params),
    onError: (error) => toast.error(errorMessage(error)),
  })

  const data = report.data
  return (
    <div className="space-y-6">
      <PageHeader
        title="Báo cáo"
        description="Báo cáo tiêu thụ điện và chi phí, xuất file CSV mở được bằng Excel"
        actions={
          <Button onClick={() => exportCsv.mutate()} disabled={exportCsv.isPending || !data}>
            {exportCsv.isPending ? <Loader2 className="animate-spin" /> : <Download />}
            Xuất CSV
          </Button>
        }
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <DateRangeFilter from={range.from} to={range.to} onChange={setRange} />
        <FilterSelect
          label="Gom nhóm"
          value={groupBy}
          options={GROUPS.map(({ value, label }) => ({ value, label }))}
          onChange={(value) => setGroupBy((value as ReportGroup | undefined) ?? "floor")}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Kỳ báo cáo"
          icon={CalendarRange}
          value={data && `${formatDate(data.from_date)} – ${formatDate(data.to_date)}`}
        />
        <StatCard label="Tổng điện năng" icon={Zap} value={data && formatKwh(data.total_kwh)} />
        <StatCard
          label="Tổng chi phí"
          icon={Wallet}
          value={data && formatVndCompact(data.total_cost)}
          footer={data && formatVnd(data.total_cost)}
        />
      </div>

      <Card>
        <CardContent>
          {report.isLoading ? (
            <Skeleton className="h-72" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-28">{group.codeHeader}</TableHead>
                  <TableHead>Tên</TableHead>
                  {groupBy !== "floor" ? <TableHead>Tầng</TableHead> : null}
                  <TableHead className="text-right">Điện năng</TableHead>
                  <TableHead className="text-right">Chi phí</TableHead>
                  <TableHead className="w-28 text-right">Tỷ trọng</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="tabular-nums">
                {(data?.rows ?? []).map((row) => (
                  <TableRow key={row.code}>
                    <TableCell className="font-medium">{row.code}</TableCell>
                    <TableCell>{row.name}</TableCell>
                    {groupBy !== "floor" ? <TableCell className="text-muted-foreground">{row.parent}</TableCell> : null}
                    <TableCell className="text-right">{formatKwh(row.kwh)}</TableCell>
                    <TableCell className="text-right">{formatVnd(row.cost)}</TableCell>
                    <TableCell className="text-right">{formatNumber(row.share_percent, 1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              {data && data.rows.length > 0 ? (
                <TableFooter className="tabular-nums">
                  <TableRow>
                    <TableCell colSpan={groupBy !== "floor" ? 3 : 2}>Tổng cộng</TableCell>
                    <TableCell className="text-right">{formatKwh(data.total_kwh)}</TableCell>
                    <TableCell className="text-right">{formatVnd(data.total_cost)}</TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableFooter>
              ) : null}
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
