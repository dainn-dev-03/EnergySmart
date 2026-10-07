"use client"

import { CrudList, Muted, withRowActions } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { SearchInput } from "@/components/data-table/search-input"
import { RoomFormDialog } from "@/components/forms/entity-forms"
import { CrudPage } from "@/components/views/crud-page"
import { useCrudDialogs } from "@/hooks/use-crud-dialogs"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useFloorOptions } from "@/hooks/use-options"
import { useResourceList } from "@/hooks/use-resource"
import { formatNumber } from "@/lib/format"
import { roomsApi } from "@/lib/resources"
import type { Room } from "@/types/models"

const COLUMNS: Column<Room>[] = [
  {
    key: "code",
    header: "Mã",
    sortKey: "code",
    className: "w-28",
    cell: (r) => <span className="font-medium">{r.code}</span>,
  },
  { key: "name", header: "Tên phòng", sortKey: "name", cell: (r) => r.name },
  { key: "floor", header: "Tầng", cell: (r) => r.floor.name },
  {
    key: "area",
    header: "Diện tích",
    sortKey: "area",
    className: "w-32 text-right",
    cell: (r) =>
      r.area === null ? <Muted /> : <span className="tabular-nums">{formatNumber(r.area, 1)} m²</span>,
  },
]

export function RoomsView() {
  const canWrite = useCanWrite()
  const floors = useFloorOptions()
  const list = useListState({ sort_by: "code", sort_order: "asc" })
  const query = useResourceList(roomsApi, list.params)
  const dialogs = useCrudDialogs(roomsApi)

  return (
    <CrudPage
      title="Phòng"
      description="Phòng trong từng tầng của tòa nhà"
      createLabel="Thêm phòng"
      canWrite={canWrite}
      onCreate={dialogs.openCreate}
      toolbar={
        <>
          <SearchInput placeholder="Tìm theo tên, mã phòng..." onSearch={list.setSearch} />
          <FilterSelect
            label="Tầng"
            value={list.params.floor_id as number | undefined}
            options={floors}
            onChange={(value) => list.setFilter("floor_id", toNumber(value))}
          />
        </>
      }
      dialogs={
        <RoomFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      }
      deleteDialog={{
        open: dialogs.deleting !== null,
        title: "Xóa phòng?",
        description: (
          <>
            Phòng <strong>{dialogs.deleting?.name}</strong> sẽ bị xóa. Không thể xóa phòng còn công tơ.
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
        emptyMessage="Không có phòng nào"
      />
    </CrudPage>
  )
}
