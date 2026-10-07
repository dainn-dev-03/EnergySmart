"use client"

import { Plus } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog"
import { DataTable, type Column } from "@/components/data-table/data-table"
import { DataTablePagination } from "@/components/data-table/data-table-pagination"
import { RowActions } from "@/components/data-table/row-actions"
import { SearchInput } from "@/components/data-table/search-input"
import { BuildingFormDialog } from "@/components/forms/building-form-dialog"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useResourceList, useResourceMutations } from "@/hooks/use-resource"
import { errorMessage } from "@/lib/api"
import { formatDateTime } from "@/lib/format"
import { buildingsApi } from "@/lib/resources"
import type { Building } from "@/types/models"

export function BuildingsView() {
  const canWrite = useCanWrite()
  const list = useListState({ sort_by: "code", sort_order: "asc" })
  const { data, isLoading, isFetching } = useResourceList(buildingsApi, list.params)
  const { remove } = useResourceMutations(buildingsApi)

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Building | null>(null)
  const [deleting, setDeleting] = useState<Building | null>(null)

  const openForm = (building: Building | null) => {
    setEditing(building)
    setFormOpen(true)
  }

  const confirmDelete = () => {
    if (!deleting) return
    remove.mutate(deleting.id, {
      onSuccess: () => setDeleting(null),
      onError: (error) => toast.error(errorMessage(error)),
    })
  }

  const columns: Column<Building>[] = [
    {
      key: "code",
      header: "Mã",
      sortKey: "code",
      className: "w-32",
      cell: (building) => <span className="font-medium">{building.code}</span>,
    },
    { key: "name", header: "Tên tòa nhà", sortKey: "name", cell: (building) => building.name },
    {
      key: "address",
      header: "Địa chỉ",
      cell: (building) => building.address ?? <span className="text-muted-foreground">—</span>,
    },
    {
      key: "created_at",
      header: "Ngày tạo",
      sortKey: "created_at",
      className: "w-40",
      cell: (building) => formatDateTime(building.created_at),
    },
  ]
  if (canWrite) {
    columns.push({
      key: "actions",
      header: "",
      className: "w-24 text-right",
      cell: (building) => (
        <RowActions onEdit={() => openForm(building)} onDelete={() => setDeleting(building)} />
      ),
    })
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Tòa nhà"
        description="Danh sách tòa nhà được quản lý trong hệ thống"
        actions={
          canWrite ? (
            <Button onClick={() => openForm(null)}>
              <Plus />
              Thêm tòa nhà
            </Button>
          ) : null
        }
      />
      <SearchInput placeholder="Tìm theo tên, mã, địa chỉ..." onSearch={list.setSearch} />
      <div className={isFetching && !isLoading ? "opacity-70 transition-opacity" : undefined}>
        <DataTable
          columns={columns}
          rows={data?.data}
          rowKey={(building) => building.id}
          isLoading={isLoading}
          emptyMessage="Chưa có tòa nhà nào"
          sortBy={list.params.sort_by}
          sortOrder={list.params.sort_order}
          onSort={list.setSort}
        />
      </div>
      <DataTablePagination pagination={data?.pagination} onPageChange={list.setPage} />

      <BuildingFormDialog open={formOpen} onOpenChange={setFormOpen} building={editing} />
      <ConfirmDeleteDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Xóa tòa nhà?"
        description={
          <>
            Tòa nhà <strong>{deleting?.name}</strong> sẽ bị xóa. Không thể xóa tòa nhà còn tầng.
          </>
        }
        isPending={remove.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
