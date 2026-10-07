"use client"

import { useQuery } from "@tanstack/react-query"
import { ArrowDownRight, ArrowUpRight, BellRing, CalendarDays, Gauge, Wallet, Zap } from "lucide-react"
import Link from "next/link"

import { ChartCard } from "@/components/charts/chart-card"
import {
  COST_COLOR,
  ColumnChart,
  ENERGY_COLOR,
  HorizontalBarChart,
  millionsAxis,
} from "@/components/charts/charts"
import { SeverityBadge, TrendStatusIcon } from "@/components/dashboard/severity-badge"
import { StatCard } from "@/components/dashboard/stat-card"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { apiGet, apiList } from "@/lib/api"
import {
  formatDate,
  formatKwh,
  formatNumber,
  formatPercent,
  formatVnd,
  formatVndCompact,
} from "@/lib/format"
import type {
  Alert,
  Comparison,
  DailyPoint,
  DashboardSummary,
  FloorTrend,
  MonthlyPoint,
} from "@/types/models"

const kwhAxis = (value: number) => formatKwh(value)

function shortDate(isoDate: string): string {
  return formatDate(isoDate).slice(0, 5) // dd/MM
}

function monthLabel(month: string): string {
  const [year, monthNumber] = month.split("-")
  return `T${Number(monthNumber)}/${year.slice(2)}`
}

function DeltaLine({ comparison, suffix }: { comparison: Comparison | undefined; suffix: string }) {
  if (!comparison || comparison.percentage_change === null) return null
  const up = comparison.percentage_change > 0
  const Icon = up ? ArrowUpRight : ArrowDownRight
  return (
    <span className="inline-flex items-center gap-1">
      {/* For consumption, up is bad: the arrow carries direction, the text stays in ink. */}
      <Icon className={up ? "text-status-critical size-3.5" : "text-status-good size-3.5"} aria-hidden />
      {formatPercent(comparison.percentage_change)} {suffix}
    </span>
  )
}

export function DashboardView() {
  const summary = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => apiGet<DashboardSummary>("/dashboard/summary"),
  })
  const dayComparison = useQuery({
    queryKey: ["analytics", "comparison", "day"],
    queryFn: () => apiGet<Comparison>("/analytics/comparison", { period: "day" }),
  })
  const monthComparison = useQuery({
    queryKey: ["analytics", "comparison", "month"],
    queryFn: () => apiGet<Comparison>("/analytics/comparison", { period: "month" }),
  })
  const daily = useQuery({
    queryKey: ["dashboard", "daily"],
    queryFn: () => apiGet<DailyPoint[]>("/dashboard/daily", { days: 30 }),
  })
  const monthly = useQuery({
    queryKey: ["dashboard", "monthly"],
    queryFn: () => apiGet<MonthlyPoint[]>("/dashboard/monthly", { months: 6 }),
  })
  const floors = useQuery({
    queryKey: ["dashboard", "by-floor"],
    queryFn: () => apiGet<FloorTrend[]>("/dashboard/by-floor"),
  })
  const openAlerts = useQuery({
    queryKey: ["/alerts", "list", { is_resolved: false, page_size: 5 }],
    queryFn: () => apiList<Alert>("/alerts", { is_resolved: false, page_size: 5 }),
  })

  const data = summary.data
  const dailyPoints = (daily.data ?? []).map((p) => ({ label: shortDate(p.date), value: p.kwh }))
  const monthlyPoints = monthly.data ?? []
  const floorTrends = floors.data ?? []
  const warningFloors = floorTrends.filter((floor) => floor.status === "WARNING")

  return (
    <div className="space-y-6">
      <PageHeader title="Tổng quan" description="Tình hình tiêu thụ điện của tòa nhà, cập nhật theo giờ" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label="Tiêu thụ hôm nay"
          icon={Zap}
          value={data && formatKwh(data.today_kwh)}
          footer={<DeltaLine comparison={dayComparison.data} suffix="so với hôm qua cùng giờ" />}
        />
        <StatCard
          label="Tiêu thụ tháng này"
          icon={CalendarDays}
          value={data && formatKwh(data.month_kwh)}
          footer={<DeltaLine comparison={monthComparison.data} suffix="so với cùng kỳ tháng trước" />}
        />
        <StatCard
          label="Chi phí tháng này"
          icon={Wallet}
          value={data && formatVndCompact(data.month_cost)}
          footer={data && formatVnd(data.month_cost)}
        />
        <StatCard
          label="Công tơ hoạt động"
          icon={Gauge}
          value={data && formatNumber(data.active_meters)}
          footer="Trạng thái ACTIVE"
        />
        <StatCard
          label="Cảnh báo chưa xử lý"
          icon={BellRing}
          value={data && formatNumber(data.alert_count)}
          footer={
            <Link href="/alerts" className="hover:text-foreground underline-offset-4 hover:underline">
              Xem danh sách cảnh báo
            </Link>
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard
          title="Tiêu thụ theo ngày"
          description="30 ngày gần nhất (kWh)"
          isLoading={daily.isLoading}
          table={{
            headers: ["Ngày", "Điện năng", "Chi phí"],
            rows: (daily.data ?? []).map((p) => [formatDate(p.date), formatKwh(p.kwh), formatVnd(p.cost)]),
          }}
        >
          <ColumnChart data={dailyPoints} seriesLabel="Điện năng" color={ENERGY_COLOR} format={kwhAxis} />
        </ChartCard>

        <ChartCard
          title="Tiêu thụ theo tầng"
          description="7 ngày gần nhất (kWh)"
          isLoading={floors.isLoading}
          table={{
            headers: ["Tầng", "7 ngày gần nhất", "7 ngày trước", "Thay đổi"],
            rows: floorTrends.map((f) => [
              f.floor_name,
              formatKwh(f.kwh),
              formatKwh(f.previous_kwh),
              formatPercent(f.percentage_change),
            ]),
          }}
        >
          <HorizontalBarChart
            data={floorTrends.map((f) => ({ label: `Tầng ${f.floor_number}`, value: f.kwh }))}
            seriesLabel="Điện năng"
            color={ENERGY_COLOR}
            format={kwhAxis}
          />
        </ChartCard>

        <ChartCard
          title="Tiêu thụ theo tháng"
          description="6 tháng gần nhất (kWh)"
          isLoading={monthly.isLoading}
          table={{
            headers: ["Tháng", "Điện năng"],
            rows: monthlyPoints.map((p) => [p.month, formatKwh(p.kwh)]),
          }}
        >
          <ColumnChart
            data={monthlyPoints.map((p) => ({ label: monthLabel(p.month), value: p.kwh }))}
            seriesLabel="Điện năng"
            color={ENERGY_COLOR}
            format={kwhAxis}
          />
        </ChartCard>

        <ChartCard
          title="Chi phí theo tháng"
          description="6 tháng gần nhất (VND)"
          isLoading={monthly.isLoading}
          table={{
            headers: ["Tháng", "Chi phí"],
            rows: monthlyPoints.map((p) => [p.month, formatVnd(p.cost)]),
          }}
        >
          <ColumnChart
            data={monthlyPoints.map((p) => ({ label: monthLabel(p.month), value: p.cost }))}
            seriesLabel="Chi phí"
            color={COST_COLOR}
            format={formatVnd}
            axisFormat={millionsAxis}
          />
        </ChartCard>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cảnh báo</CardTitle>
          <CardDescription>
            {warningFloors.length > 0
              ? `${warningFloors.length} tầng tăng tiêu thụ từ 20% trở lên so với 7 ngày trước`
              : "Không có tầng nào tăng tiêu thụ bất thường"}
          </CardDescription>
          <CardAction>
            <Button variant="outline" size="sm" asChild>
              <Link href="/alerts">Xem tất cả</Link>
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <ul className="space-y-2" aria-label="Tình trạng theo tầng">
            {floors.isLoading
              ? Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-6" />)
              : [...floorTrends]
                  .sort((a, b) => (b.percentage_change ?? 0) - (a.percentage_change ?? 0))
                  .slice(0, 5)
                  .map((floor) => (
                    <li key={floor.floor_id} className="flex items-center gap-2 text-sm">
                      <TrendStatusIcon warning={floor.status === "WARNING"} />
                      <span>
                        {floor.status === "WARNING"
                          ? `Tầng ${floor.floor_number} tăng ${formatPercent(floor.percentage_change)} tiêu thụ so với 7 ngày trước`
                          : `Tầng ${floor.floor_number} bình thường (${formatPercent(floor.percentage_change)})`}
                      </span>
                    </li>
                  ))}
          </ul>
          <ul className="space-y-3" aria-label="Cảnh báo mới nhất">
            {openAlerts.isLoading ? (
              Array.from({ length: 3 }, (_, index) => <Skeleton key={index} className="h-10" />)
            ) : (openAlerts.data?.data.length ?? 0) === 0 ? (
              <li className="text-muted-foreground text-sm">Không có cảnh báo chưa xử lý</li>
            ) : (
              openAlerts.data?.data.map((alert) => (
                <li key={alert.id} className="space-y-1 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <SeverityBadge severity={alert.severity} />
                    <span className="text-muted-foreground text-xs">{formatDate(alert.usage_date)}</span>
                  </div>
                  <p className="text-muted-foreground">{alert.message}</p>
                </li>
              ))
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
