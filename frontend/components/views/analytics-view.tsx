"use client"

import { useQuery } from "@tanstack/react-query"
import { ArrowDownRight, ArrowUpRight, CalendarDays, CalendarRange, Clock } from "lucide-react"
import { useState } from "react"

import { ChartCard } from "@/components/charts/chart-card"
import { ColumnChart, ENERGY_COLOR, HorizontalBarChart, MultiLineChart } from "@/components/charts/charts"
import { StatCard } from "@/components/dashboard/stat-card"
import { DateRangeFilter } from "@/components/data-table/date-range-filter"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useFloorOptions } from "@/hooks/use-options"
import { apiGet } from "@/lib/api"
import { shiftDays, todayInVietnam } from "@/lib/dates"
import { formatDate, formatKwh, formatNumber, formatPercent, formatVnd } from "@/lib/format"
import type {
  Comparison,
  DailyPoint,
  FloorConsumption,
  HourlyPoint,
  RoomConsumption,
} from "@/types/models"

type Period = "day" | "week" | "month"

const PERIODS: { period: Period; label: string; versus: string; icon: typeof Clock }[] = [
  { period: "day", label: "Hôm nay", versus: "so với hôm qua cùng giờ", icon: Clock },
  { period: "week", label: "Tuần này", versus: "so với tuần trước cùng thời điểm", icon: CalendarRange },
  { period: "month", label: "Tháng này", versus: "so với tháng trước cùng thời điểm", icon: CalendarDays },
]

const HOURLY_SERIES = [
  { key: "weekday", label: "Ngày thường", color: "var(--chart-1)" },
  { key: "weekend", label: "Cuối tuần", color: "var(--chart-3)" },
]

function ComparisonTile({ period, label, versus, icon, floorId }: (typeof PERIODS)[number] & { floorId?: number }) {
  const { data } = useQuery({
    queryKey: ["analytics", "comparison", period, floorId],
    queryFn: () => apiGet<Comparison>("/analytics/comparison", { period, floor_id: floorId }),
  })
  const change = data?.percentage_change ?? null
  const Arrow = change !== null && change > 0 ? ArrowUpRight : ArrowDownRight
  return (
    <StatCard
      label={label}
      icon={icon}
      value={data && formatKwh(data.current_period.kwh)}
      footer={
        data ? (
          <span className="inline-flex items-center gap-1">
            {change !== null ? (
              <Arrow className={change > 0 ? "text-status-critical size-3.5" : "text-status-good size-3.5"} aria-hidden />
            ) : null}
            {formatPercent(change)} {versus} ({formatKwh(data.previous_period.kwh)})
          </span>
        ) : null
      }
    />
  )
}

export function AnalyticsView() {
  const today = todayInVietnam()
  const [range, setRange] = useState<{ from: string | undefined; to: string | undefined }>({
    from: shiftDays(today, -29),
    to: today,
  })
  const [floorId, setFloorId] = useState<number | undefined>()
  const floors = useFloorOptions()
  const params = { from_date: range.from, to_date: range.to, floor_id: floorId }

  const daily = useQuery({
    queryKey: ["analytics", "daily", params],
    queryFn: () => apiGet<DailyPoint[]>("/analytics/daily", params),
  })
  const hourly = useQuery({
    queryKey: ["analytics", "hourly", params],
    queryFn: () => apiGet<HourlyPoint[]>("/analytics/hourly", params),
  })
  const byFloor = useQuery({
    queryKey: ["analytics", "by-floor", params],
    queryFn: () => apiGet<FloorConsumption[]>("/analytics/by-floor", params),
  })
  const byRoom = useQuery({
    queryKey: ["analytics", "by-room", params],
    queryFn: () => apiGet<RoomConsumption[]>("/analytics/by-room", { ...params, limit: 10 }),
  })

  const hourlyRows = (hourly.data ?? []).map((p) => ({
    hour: `${String(p.hour).padStart(2, "0")}h`,
    weekday: p.weekday_kwh,
    weekend: p.weekend_kwh,
  }))

  return (
    <div className="space-y-6">
      <PageHeader title="Phân tích" description="Xu hướng tiêu thụ, giờ cao điểm và so sánh giữa các kỳ" />

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <DateRangeFilter from={range.from} to={range.to} onChange={setRange} />
        <FilterSelect label="Tầng" value={floorId} options={floors} onChange={(v) => setFloorId(toNumber(v))} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {PERIODS.map((item) => (
          <ComparisonTile key={item.period} {...item} floorId={floorId} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard
          title="Tiêu thụ theo ngày"
          description="Trong khoảng thời gian đã chọn (kWh)"
          isLoading={daily.isLoading}
          table={{
            headers: ["Ngày", "Điện năng", "Chi phí"],
            rows: (daily.data ?? []).map((p) => [formatDate(p.date), formatKwh(p.kwh), formatVnd(p.cost)]),
          }}
        >
          <ColumnChart
            data={(daily.data ?? []).map((p) => ({ label: formatDate(p.date).slice(0, 5), value: p.kwh }))}
            seriesLabel="Điện năng"
            color={ENERGY_COLOR}
            format={formatKwh}
          />
        </ChartCard>

        <ChartCard
          title="Biểu đồ tải theo giờ"
          description="kWh trung bình mỗi ngày tại từng giờ — thấy rõ giờ cao điểm"
          isLoading={hourly.isLoading}
          table={{
            headers: ["Giờ", "Ngày thường", "Cuối tuần"],
            rows: hourlyRows.map((r) => [r.hour, formatKwh(r.weekday), formatKwh(r.weekend)]),
          }}
        >
          <MultiLineChart data={hourlyRows} xKey="hour" series={HOURLY_SERIES} format={formatKwh} />
        </ChartCard>

        <ChartCard
          title="Tiêu thụ theo tầng"
          description="Tổng kWh trong khoảng thời gian đã chọn"
          isLoading={byFloor.isLoading}
          table={{
            headers: ["Tầng", "Điện năng", "Chi phí", "Tỷ trọng"],
            rows: (byFloor.data ?? []).map((f) => [
              f.floor_name,
              formatKwh(f.kwh),
              formatVnd(f.cost),
              `${formatNumber(f.share_percent, 1)}%`,
            ]),
          }}
        >
          <HorizontalBarChart
            data={(byFloor.data ?? []).map((f) => ({ label: `Tầng ${f.floor_number}`, value: f.kwh }))}
            seriesLabel="Điện năng"
            color={ENERGY_COLOR}
            format={formatKwh}
          />
        </ChartCard>

        <Card>
          <CardHeader>
            <CardTitle>Phòng tiêu thụ nhiều nhất</CardTitle>
            <CardDescription>Top 10 phòng và tỷ trọng trên tổng tiêu thụ</CardDescription>
          </CardHeader>
          <CardContent>
            {byRoom.isLoading ? (
              <Skeleton className="h-64" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Phòng</TableHead>
                    <TableHead className="text-right">Điện năng</TableHead>
                    <TableHead className="text-right">Tỷ trọng</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="tabular-nums">
                  {(byRoom.data ?? []).map((room) => (
                    <TableRow key={room.room_id}>
                      <TableCell>
                        <p className="font-medium">{room.room_name}</p>
                        <p className="text-muted-foreground text-xs">
                          {room.room_code} · {room.floor_name}
                        </p>
                      </TableCell>
                      <TableCell className="text-right">{formatKwh(room.kwh)}</TableCell>
                      <TableCell className="text-right">{formatNumber(room.share_percent, 1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
