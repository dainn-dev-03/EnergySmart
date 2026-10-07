"use client"

import { ChartColumn, Table2 } from "lucide-react"
import { useState, type ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export interface TableView {
  headers: string[]
  rows: (string | number)[][]
}

interface ChartCardProps {
  title: string
  description?: string
  isLoading: boolean
  /** Same data as the chart, so no value is reachable through the tooltip only. */
  table: TableView
  children: ReactNode
  className?: string
}

/** Card holding one chart, with a toggle to an accessible table view of the same data. */
export function ChartCard({ title, description, isLoading, table, children, className }: ChartCardProps) {
  const [showTable, setShowTable] = useState(false)

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
        <CardAction>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setShowTable((value) => !value)}
            aria-label={showTable ? "Xem biểu đồ" : "Xem dạng bảng"}
            title={showTable ? "Xem biểu đồ" : "Xem dạng bảng"}
          >
            {showTable ? <ChartColumn /> : <Table2 />}
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : showTable ? (
          <div className="max-h-72 overflow-auto rounded-md border">
            <Table>
              <TableHeader className="bg-muted/50 sticky top-0">
                <TableRow>
                  {table.headers.map((header) => (
                    <TableHead key={header}>{header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody className="tabular-nums">
                {table.rows.map((row, index) => (
                  <TableRow key={index}>
                    {row.map((cell, cellIndex) => (
                      <TableCell key={cellIndex}>{cell}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}
