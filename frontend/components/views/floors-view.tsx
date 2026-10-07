"use client"

import { CrudList, Muted, withRowActions } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { SearchInput } from "@/components/data-table/search-input"
import { FloorFormDialog } from "@/components/forms/entity-forms"
import { CrudPage } from "@/components/views/crud-page"
import { useCrudDialogs } from "@/hooks/use-crud-dialogs"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useBuildingOptions } from "@/hooks/use-options"
import { useResourceList } from "@/hooks/use-resource"
import { floorsApi } from "@/lib/resources"
import type { Floor } from "@/types/models"

const COLUMNS: Column<Floor>[] = [
  {
    key: "floor_number",
    header: "Số tầng",
    sortKey: "floor_number",
    className: "w-28",
    cell: (f) => <span className="font-medium tabular-nums">{f.floor_number}</span>,
  },
  { key: "name", header: "Tên tầng", sortKey: "name", cell: (f) => f.name },
  { key: "building", header: "Tòa nhà", cell: (f) => `${f.building.code} · ${f.building.name}` },
  { key: "description", header: "Mô tả", cell: (f) => <Muted>{f.description}</Muted> },
]

export function FloorsView() {
  const canWrite = useCanWrite()
  const buildings = useBuildingOptions()
  const list = useListState({ sort_by: "floor_number", sort_order: "asc" })
  const query = useResourceList(floorsApi, list.params)
  const dialogs = useCrudDialogs(floorsApi)

  return (
    <CrudPage
      title="Tầng"
      description="Các tầng của từng tòa nhà"
      createLabel="Thêm tầng"
      canWrite={canWrite}
      onCreate={dialogs.openCreate}
      toolbar={
        <>
          <SearchInput placeholder="Tìm theo tên tầng..." onSearch={list.setSearch} />
          <FilterSelect
            label="Tòa nhà"
            value={list.params.building_id as number | undefined}
            options={buildings}
            onChange={(value) => list.setFilter("building_id", toNumber(value))}
          />
        </>
      }
      dialogs={
        <FloorFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      }
      deleteDialog={{
        open: dialogs.deleting !== null,
        title: "Xóa tầng?",
        description: (
          <>
            <strong>{dialogs.deleting?.name}</strong> sẽ bị xóa. Không thể xóa tầng còn phòng.
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
        emptyMessage="Không có tầng nào"
      />
    </CrudPage>
  )
}
