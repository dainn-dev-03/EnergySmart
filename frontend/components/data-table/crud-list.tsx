"use client"

import type { UseQueryResult } from "@tanstack/react-query"

import { DataTable, type Column } from "@/components/data-table/data-table"
import { DataTablePagination } from "@/components/data-table/data-table-pagination"
import { RowActions } from "@/components/data-table/row-actions"
import type { ListState } from "@/hooks/use-list-state"
import { cn } from "@/lib/utils"
import type { PaginatedResponse } from "@/types/api"

interface CrudListProps<T extends { id: number }> {
  query: UseQueryResult<PaginatedResponse<T>>
  list: ListState
  columns: Column<T>[]
  emptyMessage: string
  onRowClick?: (row: T) => void
  fillHeight?: boolean
}

/** Table + pagination of a list page. While a new page loads, the old one stays dimmed. */
export function CrudList<T extends { id: number }>({
  query,
  list,
  columns,
  emptyMessage,
  onRowClick,
  fillHeight = false,
}: CrudListProps<T>) {
  const { data, isLoading, isFetching } = query
  return (
    <div className={cn("space-y-4", fillHeight && "flex min-h-0 flex-1 flex-col")}>
      <div className={cn("transition-opacity", fillHeight && "min-h-0 flex-1", isFetching && !isLoading && "opacity-60")}>
        <DataTable
          columns={columns}
          rows={data?.data}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          emptyMessage={emptyMessage}
          sortBy={list.params.sort_by}
          sortOrder={list.params.sort_order}
          onSort={list.setSort}
          onRowClick={onRowClick}
          fillHeight={fillHeight}
        />
      </div>
      <div className={fillHeight ? "shrink-0" : undefined}>
        <DataTablePagination pagination={data?.pagination} onPageChange={list.setPage} />
      </div>
    </div>
  )
}

/** Edit/delete column, appended only for users allowed to write. */
export function withRowActions<T>(
  columns: Column<T>[],
  canWrite: boolean,
  onEdit: (row: T) => void,
  onDelete: (row: T) => void,
): Column<T>[] {
  if (!canWrite) return columns
  return [
    ...columns,
    {
      key: "actions",
      header: "",
      className: "w-24 text-right",
      cell: (row) => <RowActions onEdit={() => onEdit(row)} onDelete={() => onDelete(row)} />,
    },
  ]
}

export function Muted({ children }: { children?: React.ReactNode }) {
  return <span className="text-muted-foreground">{children ?? "—"}</span>
}
