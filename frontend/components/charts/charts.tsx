"use client"

import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { formatNumber } from "@/lib/format"

/**
 * Chart specs (shared): bars <= 24px with a 4px rounded data end, 2px lines, hairline
 * horizontal grid only, axis text in muted ink, values formatted vi-VN.
 * Colours come from tokens: --chart-1 = kWh, --chart-2 = cost.
 */
export const ENERGY_COLOR = "var(--chart-1)"
export const COST_COLOR = "var(--chart-2)"

export interface Point {
  label: string
  value: number
}

type Formatter = (value: number) => string

/** Axis ticks: full numbers with thousands separators (1.600), never cryptic compact suffixes. */
const defaultAxis: Formatter = (value) => formatNumber(value)

/** VND axis in millions: 25.000.000 -> "25 tr". */
export const millionsAxis: Formatter = (value) => `${formatNumber(value / 1e6, 1)} tr`

function TooltipRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex w-full items-center justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  )
}

interface ColumnChartProps {
  data: Point[]
  seriesLabel: string
  color: string
  format: Formatter
  axisFormat?: Formatter
  className?: string
}

/** Single-series column chart (title names the series, so no legend box). */
export function ColumnChart({
  data,
  seriesLabel,
  color,
  format,
  axisFormat = defaultAxis,
  className = "h-64",
}: ColumnChartProps) {
  const config = { value: { label: seriesLabel, color } } satisfies ChartConfig
  return (
    <ChartContainer config={config} className={`aspect-auto w-full ${className}`}>
      <BarChart data={data} margin={{ top: 8, right: 4, left: 4, bottom: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={16} />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={56}
          tickFormatter={(value: number) => axisFormat(value)}
        />
        <ChartTooltip
          cursor={{ fill: "var(--muted)" }}
          content={
            <ChartTooltipContent
              formatter={(value) => <TooltipRow label={seriesLabel} value={format(Number(value))} />}
            />
          }
        />
        <Bar
          dataKey="value"
          fill="var(--color-value)"
          radius={[4, 4, 0, 0]}
          maxBarSize={24}
          isAnimationActive={false}
        />
      </BarChart>
    </ChartContainer>
  )
}

/** Horizontal bars for ranking categories (floors, rooms). */
export function HorizontalBarChart({
  data,
  seriesLabel,
  color,
  format,
  axisFormat = defaultAxis,
}: Omit<ColumnChartProps, "className">) {
  const config = { value: { label: seriesLabel, color } } satisfies ChartConfig
  const height = Math.max(160, data.length * 32 + 24)
  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height }}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid horizontal={false} />
        <XAxis
          type="number"
          tickLine={false}
          axisLine={false}
          tickFormatter={(value: number) => axisFormat(value)}
        />
        <YAxis type="category" dataKey="label" tickLine={false} axisLine={false} width={88} />
        <ChartTooltip
          cursor={{ fill: "var(--muted)" }}
          content={
            <ChartTooltipContent
              formatter={(value) => <TooltipRow label={seriesLabel} value={format(Number(value))} />}
            />
          }
        />
        <Bar
          dataKey="value"
          fill="var(--color-value)"
          radius={[0, 4, 4, 0]}
          maxBarSize={18}
          isAnimationActive={false}
        />
      </BarChart>
    </ChartContainer>
  )
}

export interface Series {
  key: string
  label: string
  color: string
}

interface MultiLineChartProps {
  data: Record<string, string | number>[]
  xKey: string
  series: Series[]
  format: Formatter
}

/** Line chart for 2+ series on one axis; legend always shown. */
export function MultiLineChart({ data, xKey, series, format }: MultiLineChartProps) {
  const config = Object.fromEntries(
    series.map((item) => [item.key, { label: item.label, color: item.color }]),
  ) satisfies ChartConfig
  return (
    <ChartContainer config={config} className="aspect-auto h-72 w-full">
      <LineChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey={xKey} tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={48}
          tickFormatter={(value: number) => formatNumber(value)}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              formatter={(value, name) => {
                const label = series.find((item) => item.key === name)?.label ?? String(name)
                return <TooltipRow label={label} value={format(Number(value))} />
              }}
            />
          }
        />
        <ChartLegend content={<ChartLegendContent />} />
        {series.map((item) => (
          <Line
            key={item.key}
            dataKey={item.key}
            type="monotone"
            stroke={`var(--color-${item.key})`}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--card)" }}
          />
        ))}
      </LineChart>
    </ChartContainer>
  )
}
