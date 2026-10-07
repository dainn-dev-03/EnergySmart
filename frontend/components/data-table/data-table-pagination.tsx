"use client"

import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatNumber } from "@/lib/format"
import type { Pagination } from "@/types/api"

interface DataTablePaginationProps {
  pagination: Pagination | undefined
  onPageChange: (page: number) => void
}

export function DataTablePagination({ pagination, onPageChange }: DataTablePaginationProps) {
  if (!pagination || pagination.total === 0) return null
  const { page, page_size: pageSize, total, total_pages: totalPages } = pagination
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col items-center justify-between gap-2 text-sm sm:flex-row">
      <p className="text-muted-foreground">
        Hiển thị {formatNumber(first)}–{formatNumber(last)} / {formatNumber(total)} bản ghi
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          <ChevronLeft />
          Trước
        </Button>
        <span className="tabular-nums">
          Trang {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Sau
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}
