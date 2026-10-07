"use client"

import { CrudList, Muted, withRowActions } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { SearchInput } from "@/components/data-table/search-input"
import { BuildingFormDialog } from "@/components/forms/entity-forms"
import { CrudPage } from "@/components/views/crud-page"
import { useCrudDialogs } from "@/hooks/use-crud-dialogs"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useResourceList } from "@/hooks/use-resource"
import { formatDateTime } from "@/lib/format"
import { buildingsApi } from "@/lib/resources"
import type { Building } from "@/types/models"

const COLUMNS: Column<Building>[] = [
  {
    key: "code",
    header: "Mã",
    sortKey: "code",
    className: "w-32",
    cell: (b) => <span className="font-medium">{b.code}</span>,
  },
  { key: "name", header: "Tên tòa nhà", sortKey: "name", cell: (b) => b.name },
  { key: "address", header: "Địa chỉ", cell: (b) => <Muted>{b.address}</Muted> },
  {
    key: "created_at",
    header: "Ngày tạo",
    sortKey: "created_at",
    className: "w-40",
    cell: (b) => formatDateTime(b.created_at),
  },
]

export function BuildingsView() {
  const canWrite = useCanWrite()
  const list = useListState({ sort_by: "code", sort_order: "asc" })
  const query = useResourceList(buildingsApi, list.params)
  const dialogs = useCrudDialogs(buildingsApi)

  return (
    <CrudPage
      title="Tòa nhà"
      description="Danh sách tòa nhà được quản lý trong hệ thống"
      createLabel="Thêm tòa nhà"
      canWrite={canWrite}
      onCreate={dialogs.openCreate}
      toolbar={<SearchInput placeholder="Tìm theo tên, mã, địa chỉ..." onSearch={list.setSearch} />}
      dialogs={
        <BuildingFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      }
      deleteDialog={{
        open: dialogs.deleting !== null,
        title: "Xóa tòa nhà?",
        description: (
          <>
            Tòa nhà <strong>{dialogs.deleting?.name}</strong> sẽ bị xóa. Không thể xóa tòa nhà còn tầng.
          </>
        ),
        isPending: dialogs.isDeleting,
        onCancel: dialogs.cancelDelete,
        onConfirm: dialogs.confirmDelete,
      }}
    >
      <CrudList
        query={query}
        list={list}
        columns={withRowActions(COLUMNS, canWrite, dialogs.openEdit, dialogs.askDelete)}
        emptyMessage="Chưa có tòa nhà nào"
      />
    </CrudPage>
  )
}
